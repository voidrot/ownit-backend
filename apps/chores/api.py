from datetime import datetime
from typing import Optional

from django.http import HttpRequest
from django.utils import timezone
from ninja import File, Router, UploadedFile

from apps.chores.api_schema import (
    AssignmentDetailSchema,
    AssignmentSummarySchema,
    ChoreDetailSchema,
    EvidenceSchema,
    EquipmentSchema,
    ErrorSchema,
    LocationSchema,
    TaskSchema,
)
from apps.chores.models import Assignment, AssignmentEvidence, Chore, Equipment, Location, Task
from apps.core.api_schema import AuthErrorSchema, NotFoundSchema
from apps.core.utils import is_child, is_parent
from apps.users.models import User

router = Router(tags=["Chores"])


def _get_request_user(request: HttpRequest) -> Optional[User]:
    """Return the authenticated user if present."""
    return getattr(request, "auth", None)


def _get_child_or_404(child_id: int) -> Optional[User]:
    """Return the active child user or None if not found."""
    return User.objects.filter(id=child_id, groups__name="child", is_active=True).first()


def _file_url(request: HttpRequest, field) -> Optional[str]:
    """Build an absolute URL for a FileField or ImageField if present."""
    if not field:
        return None
    try:
        return request.build_absolute_uri(field.url)
    except ValueError:
        return None


def _build_evidence_schema(request: HttpRequest, evidence: AssignmentEvidence) -> EvidenceSchema:
    """Serialize evidence into a response schema."""
    return EvidenceSchema(
        id=evidence.id,
        photo_url=_file_url(request, evidence.photo),
        video_url=_file_url(request, evidence.video),
        created_at=evidence.created_at,
    )


def _build_assignment_summary(assignment: Assignment) -> AssignmentSummarySchema:
    """Serialize an assignment summary payload."""
    chore = assignment.chore
    return AssignmentSummarySchema(
        assignment_id=assignment.id,
        due_date=assignment.due_date,
        is_completed=assignment.is_completed,
        pending_approval=assignment.pending_approval,
        approved=assignment.approved,
        closed=assignment.closed,
        chore={
            "id": chore.id,
            "name": chore.name,
            "description": chore.description,
            "points": chore.points,
        },
    )


def _build_location_schema(location: Optional[Location]) -> Optional[LocationSchema]:
    """Serialize a location payload."""
    if not location:
        return None
    return LocationSchema(
        id=location.id,
        name=location.name,
        description=location.description,
        notes=location.notes,
    )


def _build_equipment_schema(request: HttpRequest, equipment: Equipment) -> EquipmentSchema:
    """Serialize an equipment payload."""
    return EquipmentSchema(
        id=equipment.id,
        name=equipment.name,
        description=equipment.description,
        location=_build_location_schema(equipment.location),
        notes=equipment.notes,
        image_url=_file_url(request, equipment.image),
    )


def _build_task_schema(request: HttpRequest, task: Task) -> TaskSchema:
    """Serialize a task payload."""
    equipment = [_build_equipment_schema(request, item) for item in task.equipment.all()]
    return TaskSchema(
        id=task.id,
        name=task.name,
        description=task.description,
        notes=task.notes,
        steps=task.steps,
        equipment=equipment,
    )


def _build_chore_detail(request: HttpRequest, chore: Chore) -> ChoreDetailSchema:
    """Serialize a chore detail payload."""
    equipment = [_build_equipment_schema(request, item) for item in chore.equipment.all()]
    tasks = [_build_task_schema(request, task) for task in chore.tasks.all()]
    return ChoreDetailSchema(
        id=chore.id,
        name=chore.name,
        description=chore.description,
        points=chore.points,
        penalize_incomplete=chore.penalize_incomplete,
        penalty_amount=chore.penalty_amount,
        is_recurring=chore.is_recurring,
        recurrence=chore.recurrence,
        recurrence_day_of_week=chore.recurrence_day_of_week,
        recurrence_day_of_month=chore.recurrence_day_of_month,
        instructions_video_url=_file_url(request, chore.instructions_video),
        instructions_video_name=chore.instructions_video_name,
        instructions_video_source=chore.instructions_video_source,
        location=_build_location_schema(chore.location),
        equipment=equipment,
        tasks=tasks,
        notes=chore.notes,
        time_due=chore.time_due,
        age_restricted=chore.age_restricted,
        minimum_age=chore.minimum_age,
        assign_to_all=chore.assign_to_all,
        disabled=chore.disabled,
    )


@router.get(
    "/children/{child_id}/assignments",
    response={200: list[AssignmentSummarySchema], 403: AuthErrorSchema, 404: NotFoundSchema},
)
def list_child_assignments(request: HttpRequest, child_id: int):
    """Get all active assignments for a child."""
    user = _get_request_user(request)
    if not user:
        return 403, {"message": "Unauthorized"}
    if is_child(user) and user.id != child_id:
        return 403, {"message": "Unauthorized"}
    if not (is_child(user) or is_parent(user)):
        return 403, {"message": "Unauthorized"}

    child = _get_child_or_404(child_id)
    if not child:
        return 404, {"message": "Child not found"}

    assignments = (
        Assignment.objects.filter(assigned_to=child, closed=False)
        .select_related("chore")
        .order_by("due_date")
    )
    return [_build_assignment_summary(assignment) for assignment in assignments]


@router.get("/locations", response={200: list[LocationSchema], 403: AuthErrorSchema})
def list_locations(request: HttpRequest):
    """Get all available locations."""
    user = _get_request_user(request)
    if not user or not (is_child(user) or is_parent(user)):
        return 403, {"message": "Unauthorized"}

    locations = Location.objects.order_by("name")
    return [_build_location_schema(location) for location in locations if location]


@router.get("/equipment", response={200: list[EquipmentSchema], 403: AuthErrorSchema})
def list_equipment(request: HttpRequest):
    """Get all available equipment."""
    user = _get_request_user(request)
    if not user or not (is_child(user) or is_parent(user)):
        return 403, {"message": "Unauthorized"}

    equipment = Equipment.objects.select_related("location").order_by("name")
    return [_build_equipment_schema(request, item) for item in equipment]


@router.get(
    "/chores/{id}",
    response={200: ChoreDetailSchema, 403: AuthErrorSchema, 404: NotFoundSchema},
)
def get_chore_detail(request: HttpRequest, id: int):
    """Get full chore data including equipment, tasks, and location."""
    user = _get_request_user(request)
    if not user or not (is_child(user) or is_parent(user)):
        return 403, {"message": "Unauthorized"}

    chore = (
        Chore.objects.filter(id=id)
        .select_related("location")
        .prefetch_related("equipment", "tasks", "tasks__equipment")
        .first()
    )
    if not chore:
        return 404, {"message": "Chore not found"}

    return _build_chore_detail(request, chore)


@router.get(
    "/assignments/{assignment_id}",
    response={200: AssignmentDetailSchema, 403: AuthErrorSchema, 404: NotFoundSchema},
)
def get_assignment_detail(request: HttpRequest, assignment_id: int):
    """Get the status and details for a specific assignment."""
    user = _get_request_user(request)
    if not user:
        return 403, {"message": "Unauthorized"}

    assignment = (
        Assignment.objects.filter(id=assignment_id)
        .select_related("chore", "assigned_to")
        .prefetch_related("evidence")
        .first()
    )
    if not assignment:
        return 404, {"message": "Assignment not found"}
    if is_child(user) and assignment.assigned_to_id != user.id:
        return 403, {"message": "Unauthorized"}
    if not (is_child(user) or is_parent(user)):
        return 403, {"message": "Unauthorized"}

    summary = _build_assignment_summary(assignment)
    return AssignmentDetailSchema(
        **summary.dict(),
        approved_at=assignment.approved_at,
        completed_at=assignment.completed_at,
        closed_at=assignment.closed_at,
        evidence=[_build_evidence_schema(request, item) for item in assignment.evidence.all()],
    )


@router.patch(
    "/assignments/{assignment_id}/ready-for-approval",
    response={200: AssignmentDetailSchema, 403: AuthErrorSchema, 404: NotFoundSchema, 409: ErrorSchema},
)
def mark_assignment_ready_for_approval(request: HttpRequest, assignment_id: int):
    """Allow a child to mark an assignment as ready for approval."""
    user = _get_request_user(request)
    if not user or not is_child(user):
        return 403, {"message": "Unauthorized"}

    assignment = Assignment.objects.filter(id=assignment_id).select_related("assigned_to").first()
    if not assignment:
        return 404, {"message": "Assignment not found"}
    if assignment.assigned_to_id != user.id:
        return 403, {"message": "Unauthorized"}
    if assignment.closed or assignment.approved:
        return 409, {"message": "Assignment is closed or already approved"}

    now = timezone.now()
    assignment.pending_approval = True
    assignment.is_completed = True
    assignment.completed_at = assignment.completed_at or now
    assignment.save(update_fields=["pending_approval", "is_completed", "completed_at", "updated_at"])

    return get_assignment_detail(request, assignment_id)


@router.patch(
    "/assignments/{assignment_id}/mark-incomplete",
    response={200: AssignmentDetailSchema, 403: AuthErrorSchema, 404: NotFoundSchema, 409: ErrorSchema},
)
def mark_assignment_incomplete(request: HttpRequest, assignment_id: int):
    """Allow a parent to mark an assignment back to incomplete."""
    user = _get_request_user(request)
    if not user or not is_parent(user):
        return 403, {"message": "Unauthorized"}

    assignment = Assignment.objects.filter(id=assignment_id).first()
    if not assignment:
        return 404, {"message": "Assignment not found"}
    if assignment.closed:
        return 409, {"message": "Assignment is closed"}

    assignment.pending_approval = False
    assignment.approved = False
    assignment.is_completed = False
    assignment.completed_at = None
    assignment.approved_at = None
    assignment.closed = False
    assignment.closed_at = None
    assignment.save(
        update_fields=[
            "pending_approval",
            "approved",
            "is_completed",
            "completed_at",
            "approved_at",
            "closed",
            "closed_at",
            "updated_at",
        ]
    )

    return get_assignment_detail(request, assignment_id)


@router.patch(
    "/assignments/{assignment_id}/approve",
    response={200: AssignmentDetailSchema, 403: AuthErrorSchema, 404: NotFoundSchema, 409: ErrorSchema},
)
def approve_assignment(request: HttpRequest, assignment_id: int):
    """Allow a parent to approve and complete an assignment."""
    user = _get_request_user(request)
    if not user or not is_parent(user):
        return 403, {"message": "Unauthorized"}

    assignment = Assignment.objects.filter(id=assignment_id).first()
    if not assignment:
        return 404, {"message": "Assignment not found"}
    if assignment.closed:
        return 409, {"message": "Assignment is closed"}

    now = timezone.now()
    assignment.approved = True
    assignment.pending_approval = False
    assignment.is_completed = True
    assignment.completed_at = assignment.completed_at or now
    assignment.approved_at = now
    assignment.closed = True
    assignment.closed_at = now
    assignment.save(
        update_fields=[
            "approved",
            "pending_approval",
            "is_completed",
            "completed_at",
            "approved_at",
            "closed",
            "closed_at",
            "updated_at",
        ]
    )

    return get_assignment_detail(request, assignment_id)


@router.post(
    "/assignments/{assignment_id}/evidence",
    response={201: EvidenceSchema, 400: ErrorSchema, 403: AuthErrorSchema, 404: NotFoundSchema, 409: ErrorSchema},
)
def upload_assignment_evidence(
    request: HttpRequest,
    assignment_id: int,
    photo: Optional[UploadedFile] = File(None),
    video: Optional[UploadedFile] = File(None),
):
    """Attach photo or video evidence to an assignment."""
    user = _get_request_user(request)
    if not user:
        return 403, {"message": "Unauthorized"}

    assignment = Assignment.objects.filter(id=assignment_id).select_related("assigned_to").first()
    if not assignment:
        return 404, {"message": "Assignment not found"}
    if is_child(user) and assignment.assigned_to_id != user.id:
        return 403, {"message": "Unauthorized"}
    if not (is_child(user) or is_parent(user)):
        return 403, {"message": "Unauthorized"}
    if assignment.closed or assignment.approved:
        return 409, {"message": "Assignment is closed or approved"}
    if not photo and not video:
        return 400, {"message": "Photo or video evidence is required"}
    if photo and video:
        return 400, {"message": "Provide either a photo or a video, not both"}

    evidence = AssignmentEvidence.objects.create(assignment=assignment, photo=photo, video=video)
    return 201, _build_evidence_schema(request, evidence)


@router.post(
    "/assignments/{assignment_id}/evidence/batch",
    response={201: list[EvidenceSchema], 400: ErrorSchema, 403: AuthErrorSchema, 404: NotFoundSchema, 409: ErrorSchema},
)
def upload_assignment_evidence_batch(
    request: HttpRequest,
    assignment_id: int,
    photos: Optional[list[UploadedFile]] = File(None),
    videos: Optional[list[UploadedFile]] = File(None),
):
    """Attach multiple photo or video evidence files to an assignment."""
    user = _get_request_user(request)
    if not user:
        return 403, {"message": "Unauthorized"}

    assignment = Assignment.objects.filter(id=assignment_id).select_related("assigned_to").first()
    if not assignment:
        return 404, {"message": "Assignment not found"}
    if is_child(user) and assignment.assigned_to_id != user.id:
        return 403, {"message": "Unauthorized"}
    if not (is_child(user) or is_parent(user)):
        return 403, {"message": "Unauthorized"}
    if assignment.closed or assignment.approved:
        return 409, {"message": "Assignment is closed or approved"}

    if photos is None or photos.__class__.__name__ == "File":
        photos = []
    if videos is None or videos.__class__.__name__ == "File":
        videos = []
    if isinstance(photos, UploadedFile):
        photos = [photos]
    if isinstance(videos, UploadedFile):
        videos = [videos]
    if not photos and not videos:
        return 400, {"message": "At least one photo or video is required"}

    created = []
    for photo in photos:
        created.append(AssignmentEvidence.objects.create(assignment=assignment, photo=photo))
    for video in videos:
        created.append(AssignmentEvidence.objects.create(assignment=assignment, video=video))

    return 201, [_build_evidence_schema(request, item) for item in created]


@router.get(
    "/assignments/{assignment_id}/evidence/{evidence_id}",
    response={200: EvidenceSchema, 403: AuthErrorSchema, 404: NotFoundSchema},
)
def get_assignment_evidence(request: HttpRequest, assignment_id: int, evidence_id: int):
    """Get the URL for a specific evidence item."""
    user = _get_request_user(request)
    if not user:
        return 403, {"message": "Unauthorized"}

    evidence = (
        AssignmentEvidence.objects.filter(id=evidence_id, assignment_id=assignment_id)
        .select_related("assignment__assigned_to")
        .first()
    )
    if not evidence:
        return 404, {"message": "Evidence not found"}
    if is_child(user) and evidence.assignment.assigned_to_id != user.id:
        return 403, {"message": "Unauthorized"}
    if not (is_child(user) or is_parent(user)):
        return 403, {"message": "Unauthorized"}

    return _build_evidence_schema(request, evidence)


@router.delete(
    "/assignments/{assignment_id}/evidence/{evidence_id}",
    response={204: None, 403: AuthErrorSchema, 404: NotFoundSchema, 409: ErrorSchema},
)
def delete_assignment_evidence(request: HttpRequest, assignment_id: int, evidence_id: int):
    """Delete evidence before the assignment is complete or closed."""
    user = _get_request_user(request)
    if not user:
        return 403, {"message": "Unauthorized"}

    evidence = (
        AssignmentEvidence.objects.filter(id=evidence_id, assignment_id=assignment_id)
        .select_related("assignment__assigned_to")
        .first()
    )
    if not evidence:
        return 404, {"message": "Evidence not found"}

    assignment = evidence.assignment
    if is_child(user) and assignment.assigned_to_id != user.id:
        return 403, {"message": "Unauthorized"}
    if not (is_child(user) or is_parent(user)):
        return 403, {"message": "Unauthorized"}
    if assignment.is_completed or assignment.closed or assignment.approved:
        return 409, {"message": "Evidence cannot be deleted after completion"}

    evidence.delete()
    return 204, None
