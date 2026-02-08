from apps.chores.utils import get_due_date_from_time_due, chore_runs_today_q
from apps.chores.utils import get_age_from_birth_date
from django.db.models import QuerySet, Count, Q
import os
from config.celery import app
from datetime import datetime, timezone, timedelta
from apps.chores.models import Assignment, Chore
from apps.users.models import User
import logging
import random

logger = logging.getLogger(__name__)


@app.task
def close_days_chores() -> None:
    """Close all open, incomplete assignments.

    Marks assignments with closed=False and closed_at=None as closed and sets
    closed_at to the current UTC time.
    """
    logger.info('Closing incomplete chores (excluding assignments with future due_date)...')
    now = datetime.now(timezone.utc)
    # Only close assignments that are open and either have no due_date or whose
    # due_date is in the past or now. This prevents closing chores scheduled
    # for future dates accidentally.
    open_chores = (
        Assignment.objects.filter(closed=False, closed_at=None)
        .filter(Q(due_date__lte=now) | Q(due_date__isnull=True))
        .update(closed=True, closed_at=now)
    )
    # TODO: We probably want to create a report of which chores were closed each time this runs, and log it somewhere.
    logger.info(f'Closed {open_chores} chores.')


@app.task
def assign_chores() -> None:
    """Assign chores to child users.

    - Assign chores with `assign_to_all=True` to every user in the 'child' group.
    - For other chores, pick a single assignee weighted toward children with
        fewer active (open) assignments.
    - Respect `age_restricted` and `minimum_age` when selecting eligible
        children.
    """
    logger.info('Starting chore assignment...')
    # Fetch all users in the 'child' group. We will only assign chores to these users.
    # Avoid N+1 by selecting only required fields and evaluating once.
    children_qs = User.objects.filter(groups__name='child').only('id', 'username', 'birth_date')
    children = list(children_qs)
    child_count = len(children)
    logger.info(f'Found {child_count} children to assign chores to.')

    # If there are no children to assign chores to, nothing to do.
    if child_count == 0:
        logger.info('No children found; skipping chore assignment.')
        return
    # First we want to assign any chores with the assign_to_all flag set
    logger.info('Assigning chores with assign_to_all flag set...')
    # Only include chores that should be assigned today:
    # - non-recurring chores
    # - daily recurring chores
    # - weekly recurring chores where the stored weekday matches today (e.g., "Monday")
    # - monthly recurring chores where the stored day-of-month matches today (e.g., "15")
    today = datetime.now(timezone.utc).date()
    today_weekday = today.strftime('%A')
    today_day_of_month = str(today.day)

    # Optional deterministic seed for debugging/tests (set via env var)
    seed = os.environ.get('ASSIGN_CHORES_SEED')
    if seed is not None:
        try:
            random.seed(int(seed))
            logger.info('Random seed set from ASSIGN_CHORES_SEED')
        except Exception:
            logger.exception('Invalid ASSIGN_CHORES_SEED value; ignoring.')
    # Pre-compute current active (open) assignment counts for each child so we
    # can weight random selection toward children with fewer open assignments.
    # This is the primary fairness mechanism for this task.
    child_ids = [c.id for c in children]
    counts_qs = (
        Assignment.objects.filter(closed=False, assigned_to_id__in=child_ids)
        .values('assigned_to_id')
        .annotate(cnt=Count('id'))
    )
    counts_map = {item['assigned_to_id']: item['cnt'] for item in counts_qs}

    # Prepopulate counts with completed chores from the previous 7 days so the
    # weighted distribution accounts for recent completions (fairness over time).
    # Note: `completed_at__date` may behave differently with timezones and some
    # DB backends; this is best-effort and wrapped in a try/except so failures
    # won't stop the task.
    try:
        # Compute a timezone-robust UTC range covering the previous 7 days
        # (excluding today) and query using an explicit range instead of the
        # DB-specific `__date` lookup. This avoids backend differences and
        # timezone ambiguity.
        prev_start_day = today - timedelta(days=7)
        prev_start = datetime(prev_start_day.year, prev_start_day.month, prev_start_day.day, tzinfo=timezone.utc)
        # prev_end is the start of today (exclusive), so we count completed_at
        # values in [prev_start, prev_end).
        prev_end = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
        prev_counts_qs = (
            Assignment.objects.filter(
                is_completed=True,
                completed_at__gte=prev_start,
                completed_at__lt=prev_end,
                assigned_to_id__in=child_ids,
            )
            .values('assigned_to_id')
            .annotate(cnt=Count('id'))
        )
        for item in prev_counts_qs:
            counts_map[item['assigned_to_id']] = counts_map.get(item['assigned_to_id'], 0) + item['cnt']
    except Exception:
        # If anything goes wrong, log and continue without previous-week counts.
        logger.exception('Failed to include previous 7 days completed counts; continuing without them.')

    # Use centralized recurrence filter helper
    assign_to_all_chores: QuerySet[Chore, Chore] = (
        Chore.objects.filter(disabled=False, assign_to_all=True).filter(chore_runs_today_q(today=today))
    )
    # Assign chores flagged `assign_to_all` to every child. We create the
    # assignments and, on success, increment our in-memory counts so later
    # weighting takes these into account immediately.
    assignments_created = 0
    assignments_skipped_duplicate = 0
    assignment_failures = 0
    for chore in assign_to_all_chores:
        logger.info(f"Assigning chore '{chore.name}' to all children...")
        for child in children:
            logger.info(f"Assigning chore '{chore.name}' to child '{child.username}'...")
            due_date = get_due_date_from_time_due(chore.time_due)
            # Prevent duplicate assignments for same chore/assignee/same-day using
            # an explicit UTC day range rather than `__date` lookups.
            day_start = datetime(due_date.year, due_date.month, due_date.day, tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)
            exists = Assignment.objects.filter(
                chore=chore,
                assigned_to=child,
                due_date__gte=day_start,
                due_date__lt=day_end,
                closed=False,
            ).exists()
            if exists:
                assignments_skipped_duplicate += 1
                logger.debug(
                    "Skipping duplicate assign-to-all for chore %s -> %s on %s",
                    chore.id,
                    child.id,
                    due_date.date(),
                )
                continue
            try:
                Assignment.objects.create(chore=chore, assigned_to=child, due_date=due_date)
                assignments_created += 1
            except Exception:
                assignment_failures += 1
                logger.exception(
                    "Failed to create assign-to-all assignment for chore '%s' and child '%s'.",
                    chore.name,
                    child.username,
                )
                continue
            # Update in-memory counts so weighting reflects these new assignments
            counts_map[child.id] = counts_map.get(child.id, 0) + 1
    # # Now we want to assign chores randomly to children. For chores that have a minimum age requirement, we should only assign to children who meet that requirement.
    remaining_chores = (
        Chore.objects.filter(disabled=False, assign_to_all=False).filter(chore_runs_today_q(today=today))
    )
    
    

    def choose_weighted(candidates: list[User]) -> User | None:
        """Return a single candidate chosen with weights favoring fewer assignments.

        We compute integer weights as `max_count - count + 1` so that children with
        the fewest assignments receive the largest weight. If `candidates` is empty
        return None.
        """
        if not candidates:
            return None
        # Snapshot the current counts for the provided candidates.
        counts = [counts_map.get(c.id, 0) for c in candidates]
        # Use inverse float weights so children with fewer assignments are favored.
        # Adding 1 prevents division by zero for children with zero assignments.
        weights = [1.0 / (cnt + 1) for cnt in counts]
        chosen = random.choices(candidates, weights=weights, k=1)[0]
        # Log debug info showing candidate counts and the chosen candidate to
        # aid in troubleshooting and understanding assignment decisions.
        logger.debug(
            "choose_weighted: candidates=%s counts=%s weights=%s chosen=%s",
            [c.id for c in candidates],
            counts,
            [round(w, 3) for w in weights],
            chosen.id,
        )
        # Do NOT increment counts_map here. The caller must increment after a
        # successful Assignment creation so weights reflect confirmed assignments
        # only.
        return chosen

    for chore in remaining_chores:
        logger.info(f"Assigning chore '{chore.name}' to a child...")
        if chore.age_restricted:
            # The database requires that a minimum_age be set when a chore is age_restricted.
            # Guard against chores that are marked age_restricted but missing a minimum_age to
            # avoid TypeError when comparing ages (int >= None) and to make the issue visible
            # in logs rather than crashing the task.
            if chore.minimum_age is None:
                logger.warning(
                    "Chore '%s' is age-restricted but has no minimum_age set; skipping assignment.",
                    chore.name,
                )
                continue

            eligible_children = [
                child
                for child in children
                if child.birth_date and get_age_from_birth_date(child.birth_date) >= chore.minimum_age
            ]
            logger.info(
                "Chore '%s' is age-restricted. Found %d eligible children.",
                chore.name,
                len(eligible_children),
            )
            # Pick a weighted random eligible child to assign the chore to
            if eligible_children:
                assignee = choose_weighted(list(eligible_children))
                if assignee is None:
                    logger.error(f"No eligible children found for chore '{chore.name}'; skipping assignment.")
                    continue
                logger.info(f"Assigning chore '{chore.name}' to child '{assignee.username}'...")
                due_date = get_due_date_from_time_due(chore.time_due)
                day_start = datetime(due_date.year, due_date.month, due_date.day, tzinfo=timezone.utc)
                day_end = day_start + timedelta(days=1)
                exists = Assignment.objects.filter(
                    chore=chore,
                    assigned_to=assignee,
                    due_date__gte=day_start,
                    due_date__lt=day_end,
                    closed=False,
                ).exists()
                if exists:
                    assignments_skipped_duplicate += 1
                    logger.debug(
                        "Skipping duplicate assignment for chore %s -> %s on %s",
                        chore.id,
                        assignee.id,
                        due_date.date(),
                    )
                    continue
                try:
                    Assignment.objects.create(chore=chore, assigned_to=assignee, due_date=due_date)
                    assignments_created += 1
                except Exception:
                    assignment_failures += 1
                    logger.exception(
                        "Failed to create assignment for chore '%s' and child '%s'.",
                        chore.name,
                        assignee.username,
                    )
                    continue
                # Update counts_map now that assignment was created
                counts_map[assignee.id] = counts_map.get(assignee.id, 0) + 1

                # Summary logging for observability
                logger.info(
                    "Assignment summary: created=%d skipped_duplicates=%d failures=%d",
                    assignments_created,
                    assignments_skipped_duplicate,
                    assignment_failures,
                )
            else:
                logger.error(f"No eligible children found for chore '{chore.name}'; skipping assignment.")
        else:
            # Chore is not age-restricted, so assign to any child
            assignee = choose_weighted(list(children))
            if assignee is None:
                logger.error(f"No children available to assign chore '{chore.name}'; skipping assignment.")
                continue
            logger.info(f"Assigning chore '{chore.name}' to child '{assignee.username}'...")
            due_date = get_due_date_from_time_due(chore.time_due)
            day_start = datetime(due_date.year, due_date.month, due_date.day, tzinfo=timezone.utc)
            day_end = day_start + timedelta(days=1)
            exists = Assignment.objects.filter(
                chore=chore,
                assigned_to=assignee,
                due_date__gte=day_start,
                due_date__lt=day_end,
                closed=False,
            ).exists()
            if exists:
                assignments_skipped_duplicate += 1
                logger.debug(
                    "Skipping duplicate assignment for chore %s -> %s on %s",
                    chore.id,
                    assignee.id,
                    due_date.date(),
                )
                continue
            try:
                Assignment.objects.create(chore=chore, assigned_to=assignee, due_date=due_date)
                assignments_created += 1
            except Exception:
                assignment_failures += 1
                logger.exception(
                    "Failed to create assignment for chore '%s' and child '%s'.",
                    chore.name,
                    assignee.username,
                )
                continue
            # Update counts_map now that assignment was created
            counts_map[assignee.id] = counts_map.get(assignee.id, 0) + 1
