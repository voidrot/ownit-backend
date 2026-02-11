from datetime import date

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.chores.models import Chore, Equipment, Location, Task
from apps.users.models import User

try:
    from allauth.account.models import EmailAddress
except Exception:  # pragma: no cover - optional dependency
    EmailAddress = None


DEFAULT_PARENT_COUNT = 2
DEFAULT_CHILD_COUNT = 3
DEFAULT_SINGLE_CHILD_AGE = 10
MIN_PARENT_COUNT = 1
MAX_PARENT_COUNT = 2
MIN_CHILD_COUNT = 1
MAX_CHILD_COUNT = 8

LOCATION_DEFINITIONS = [
    ('Kitchen', 'Main kitchen and food prep area.', ['indoor', 'high-traffic']),
    ('Dining Room', 'Dining area including table and chairs.', ['indoor', 'medium-traffic']),
    ('Living Room', 'Shared living space and seating.', ['indoor', 'high-traffic']),
    ('Bathroom', 'Primary bathroom and fixtures.', ['indoor', 'high-traffic']),
    ('Laundry Room', 'Laundry area and storage.', ['indoor', 'utility']),
    ('Primary Bedroom', 'Main bedroom.', ['indoor', 'low-traffic']),
    ('Kids Bedroom', 'Children bedroom.', ['indoor', 'medium-traffic']),
    ('Home Office', 'Workspace and desk area.', ['indoor', 'low-traffic']),
    ('Entryway', 'Front entryway and landing.', ['indoor', 'medium-traffic']),
    ('Hallway', 'Main hallway and connectors.', ['indoor', 'low-traffic']),
    ('Garage', 'Garage and storage space.', ['indoor', 'storage']),
    ('Backyard', 'Backyard and lawn.', ['outdoor', 'yard']),
    ('Front Yard', 'Front yard and lawn.', ['outdoor', 'yard']),
    ('Patio', 'Patio or deck area.', ['outdoor', 'patio']),
    ('Driveway', 'Driveway and curb area.', ['outdoor', 'driveway']),
]

EQUIPMENT_DEFINITIONS = [
    ('Vacuum', 'Vacuum cleaner.', 'Garage', ['electric', 'weekly-use']),
    ('Broom', 'Standard broom.', 'Garage', ['daily-use']),
    ('Dustpan', 'Dustpan for sweeping.', 'Garage', ['daily-use']),
    ('Mop', 'Floor mop.', 'Laundry Room', ['weekly-use']),
    ('Bucket', 'Cleaning bucket.', 'Laundry Room', ['10-liter']),
    ('Microfiber Cloths', 'Reusable microfiber cloths.', 'Laundry Room', ['6-pack']),
    ('Sponge', 'Cleaning sponges.', 'Kitchen', ['replace-monthly']),
    ('Dish Soap', 'Dishwashing soap.', 'Kitchen', ['liquid']),
    ('All-purpose Cleaner', 'All-purpose spray cleaner.', 'Laundry Room', ['spray']),
    ('Glass Cleaner', 'Glass and mirror cleaner.', 'Laundry Room', ['spray']),
    ('Toilet Brush', 'Toilet cleaning brush.', 'Bathroom', ['weekly-use']),
    ('Disinfectant Cleaner', 'Disinfecting cleaner.', 'Laundry Room', ['spray']),
    ('Laundry Detergent', 'Laundry detergent.', 'Laundry Room', ['liquid']),
    ('Trash Bags', 'Trash and recycling bags.', 'Garage', ['13-gallon']),
    ('Garden Hose', 'Outdoor hose.', 'Backyard', ['50-ft']),
    ('Watering Can', 'Watering can.', 'Backyard', ['5-liter']),
    ('Lawn Mower', 'Push lawn mower.', 'Garage', ['gas']),
    ('Rake', 'Yard rake.', 'Garage', ['seasonal']),
    ('Leaf Blower', 'Leaf blower.', 'Garage', ['electric']),
    ('Weed Trimmer', 'Weed trimmer.', 'Garage', ['electric']),
    ('Gloves', 'Work gloves.', 'Garage', ['adult-size']),
]

CHORE_DEFINITIONS = [
    {
        'name': 'Wash Dishes',
        'description': 'Clean dishes and load the dishwasher if available.',
        'location': 'Kitchen',
        'equipment': ['Dish Soap', 'Sponge'],
        'points': 5,
        'recurrence': Chore.DAILY,
        'notes': ['difficulty: easy', 'estimated-minutes: 15'],
        'steps': [
            'Clear leftovers into the trash.',
            'Wash dishes with soap and rinse.',
            'Put clean dishes away.',
        ],
    },
    {
        'name': 'Wipe Kitchen Counters',
        'description': 'Wipe down counters and kitchen surfaces.',
        'location': 'Kitchen',
        'equipment': ['All-purpose Cleaner', 'Microfiber Cloths'],
        'points': 4,
        'recurrence': Chore.DAILY,
        'notes': ['difficulty: easy', 'estimated-minutes: 10'],
        'steps': [
            'Remove items from counters.',
            'Spray cleaner on surfaces.',
            'Wipe surfaces until dry.',
        ],
    },
    {
        'name': 'Sweep Kitchen Floor',
        'description': 'Sweep the kitchen floor to remove crumbs.',
        'location': 'Kitchen',
        'equipment': ['Broom', 'Dustpan'],
        'points': 4,
        'recurrence': Chore.DAILY,
        'steps': [
            'Sweep crumbs toward the dustpan.',
            'Empty dustpan into trash.',
            'Return broom and dustpan.',
        ],
    },
    {
        'name': 'Mop Kitchen Floor',
        'description': 'Mop the kitchen floor.',
        'location': 'Kitchen',
        'equipment': ['Mop', 'Bucket', 'All-purpose Cleaner'],
        'points': 6,
        'recurrence': Chore.WEEKLY,
        'recurrence_day_of_week': 'Saturday',
        'notes': ['difficulty: medium', 'estimated-minutes: 20'],
        'steps': [
            'Fill bucket with warm water and cleaner.',
            'Mop the floor from back to front.',
            'Empty and rinse bucket.',
        ],
    },
    {
        'name': 'Clean Bathroom Sink',
        'description': 'Clean sink and countertop in the bathroom.',
        'location': 'Bathroom',
        'equipment': ['All-purpose Cleaner', 'Sponge'],
        'points': 5,
        'recurrence': Chore.WEEKLY,
        'recurrence_day_of_week': 'Sunday',
        'steps': [
            'Remove items from sink area.',
            'Spray cleaner and scrub surfaces.',
            'Rinse and wipe dry.',
        ],
    },
    {
        'name': 'Scrub Toilet',
        'description': 'Scrub toilet bowl and wipe exterior.',
        'location': 'Bathroom',
        'equipment': ['Toilet Brush', 'Disinfectant Cleaner', 'Gloves'],
        'points': 6,
        'recurrence': Chore.WEEKLY,
        'recurrence_day_of_week': 'Sunday',
        'notes': ['difficulty: medium', 'estimated-minutes: 15', 'safety: use gloves'],
        'steps': [
            'Apply disinfectant to toilet bowl.',
            'Scrub bowl with toilet brush.',
            'Wipe seat and exterior.',
        ],
    },
    {
        'name': 'Tidy Living Room',
        'description': 'Pick up clutter and straighten the living room.',
        'location': 'Living Room',
        'equipment': ['Trash Bags'],
        'points': 4,
        'recurrence': Chore.DAILY,
        'steps': [
            'Return items to their homes.',
            'Throw away trash and recyclables.',
            'Straighten pillows and blankets.',
        ],
    },
    {
        'name': 'Vacuum Living Room',
        'description': 'Vacuum the living room carpets or rugs.',
        'location': 'Living Room',
        'equipment': ['Vacuum'],
        'points': 6,
        'recurrence': Chore.WEEKLY,
        'recurrence_day_of_week': 'Saturday',
        'notes': ['difficulty: medium', 'estimated-minutes: 20'],
        'steps': [
            'Clear the floor area.',
            'Vacuum carpets and rugs.',
            'Return vacuum to storage.',
        ],
    },
    {
        'name': 'Take Out Trash',
        'description': 'Take trash and recycling bins to the curb.',
        'location': 'Entryway',
        'equipment': ['Trash Bags', 'Gloves'],
        'points': 5,
        'recurrence': Chore.WEEKLY,
        'recurrence_day_of_week': 'Wednesday',
        'notes': ['difficulty: easy', 'estimated-minutes: 10', 'safety: use gloves'],
        'steps': [
            'Tie up trash bags securely.',
            'Move bins to curb.',
            'Return bins after pickup.',
        ],
    },
    {
        'name': 'Start Laundry',
        'description': 'Start a load of laundry.',
        'location': 'Laundry Room',
        'equipment': ['Laundry Detergent'],
        'points': 4,
        'recurrence': Chore.WEEKLY,
        'recurrence_day_of_week': 'Monday',
        'steps': [
            'Sort laundry by color.',
            'Add detergent and start machine.',
            'Set timer for switch to dryer.',
        ],
    },
    {
        'name': 'Fold Laundry',
        'description': 'Fold and put away clean laundry.',
        'location': 'Laundry Room',
        'equipment': ['Laundry Detergent'],
        'points': 4,
        'recurrence': Chore.WEEKLY,
        'recurrence_day_of_week': 'Monday',
        'steps': [
            'Remove laundry from dryer.',
            'Fold items neatly.',
            'Put clothes away.',
        ],
    },
    {
        'name': 'Mow Lawn',
        'description': 'Mow the backyard lawn.',
        'location': 'Backyard',
        'equipment': ['Lawn Mower', 'Gloves'],
        'points': 8,
        'recurrence': Chore.WEEKLY,
        'recurrence_day_of_week': 'Saturday',
        'age_restricted': True,
        'minimum_age': 12,
        'notes': ['difficulty: hard', 'estimated-minutes: 30', 'safety: use hearing protection'],
        'steps': [
            'Clear yard of obstacles.',
            'Mow lawn in straight passes.',
            'Put mower back in garage.',
        ],
    },
    {
        'name': 'Rake Leaves',
        'description': 'Rake leaves in the front yard.',
        'location': 'Front Yard',
        'equipment': ['Rake', 'Gloves'],
        'points': 6,
        'recurrence': Chore.WEEKLY,
        'recurrence_day_of_week': 'Saturday',
        'steps': [
            'Rake leaves into a pile.',
            'Bag leaves or move to compost.',
            'Return rake to storage.',
        ],
    },
    {
        'name': 'Weed Trim Edges',
        'description': 'Trim weeds along edges and fence lines.',
        'location': 'Front Yard',
        'equipment': ['Weed Trimmer', 'Gloves'],
        'points': 7,
        'recurrence': Chore.WEEKLY,
        'recurrence_day_of_week': 'Sunday',
        'age_restricted': True,
        'minimum_age': 12,
        'steps': [
            'Check area for debris.',
            'Trim along edges carefully.',
            'Store trimmer safely.',
        ],
    },
    {
        'name': 'Water Plants',
        'description': 'Water plants in the patio and yard.',
        'location': 'Patio',
        'equipment': ['Garden Hose', 'Watering Can'],
        'points': 3,
        'recurrence': Chore.DAILY,
        'notes': ['difficulty: easy', 'estimated-minutes: 10'],
        'steps': [
            'Check soil moisture.',
            'Water plants evenly.',
            'Turn off hose and store.',
        ],
    },
    {
        'name': 'Clean Windows',
        'description': 'Clean windows and glass doors.',
        'location': 'Living Room',
        'equipment': ['Glass Cleaner', 'Microfiber Cloths'],
        'points': 5,
        'recurrence': Chore.MONTHLY,
        'recurrence_day_of_month': '1',
        'notes': ['difficulty: easy', 'estimated-minutes: 20'],
        'steps': [
            'Spray glass cleaner.',
            'Wipe glass in circular motions.',
            'Dry edges and frames.',
        ],
    },
]


def _birth_date_for_age(age: int, today: date) -> date:
    """
    Convert an age in years to an approximate birth date.
    """
    try:
        return date(today.year - age, today.month, today.day)
    except ValueError:
        return date(today.year - age, today.month, 28)


def _validate_counts(parents: int, children: int) -> None:
    """
    Validate provided parent and child counts.
    """
    if parents < MIN_PARENT_COUNT or parents > MAX_PARENT_COUNT:
        raise CommandError(f'--parents must be between {MIN_PARENT_COUNT} and {MAX_PARENT_COUNT}.')
    if children < MIN_CHILD_COUNT or children > MAX_CHILD_COUNT:
        raise CommandError(f'--children must be between {MIN_CHILD_COUNT} and {MAX_CHILD_COUNT}.')


def _build_child_ages(children: int, child_age: int | None) -> list[int]:
    """
    Build a list of child ages that satisfies the requested constraints.
    """
    if children == 1:
        if child_age is not None and (child_age < 1 or child_age > 17):
            raise CommandError('--child-age must be between 1 and 17 when --children is 1.')
        return [child_age or DEFAULT_SINGLE_CHILD_AGE]

    base_ages = [10, 13, 8, 15, 6, 12, 9, 11]
    return base_ages[:children]


def _mark_email_verified(user: User, email: str) -> None:
    if not EmailAddress or not email:
        return
    obj, _ = EmailAddress.objects.get_or_create(user=user, email=email)
    if not obj.verified or not obj.primary:
        obj.verified = True
        obj.primary = True
        obj.save(update_fields=['verified', 'primary'])


def _create_users(
    parents: int, child_ages: list[int], today: date, command: BaseCommand
) -> tuple[list[User], list[User]]:
    """
    Create parent and child users and assign them to groups.
    """
    parent_group, _ = Group.objects.get_or_create(name='parent')
    child_group, _ = Group.objects.get_or_create(name='child')

    parent_users = []
    for index in range(parents):
        username = f'parent{index + 1}'
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'first_name': f'Parent{index + 1}',
                'last_name': 'Owner',
            },
        )
        if created:
            user.set_password('password')
            user.save(update_fields=['password'])
            command.stdout.write(command.style.SUCCESS(f'Created parent user {username}.'))
        user.groups.add(parent_group)
        _mark_email_verified(user, user.email)
        parent_users.append(user)

    child_users = []
    for index, age in enumerate(child_ages):
        username = f'child{index + 1}'
        birth_date = _birth_date_for_age(age, today)
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'first_name': f'Child{index + 1}',
                'last_name': 'Helper',
                'birth_date': birth_date,
            },
        )
        if created:
            user.set_password('password')
            user.save(update_fields=['password'])
            command.stdout.write(command.style.SUCCESS(f'Created child user {username}.'))
        else:
            if user.birth_date is None:
                user.birth_date = birth_date
                user.save(update_fields=['birth_date'])
        user.groups.add(child_group)
        _mark_email_verified(user, user.email)
        child_users.append(user)

    return parent_users, child_users


def _create_locations(command: BaseCommand) -> dict[str, Location]:
    """
    Create common household locations.
    """
    locations = {}
    for name, description, notes in LOCATION_DEFINITIONS:
        location, created = Location.objects.get_or_create(
            name=name,
            defaults={'description': description, 'notes': notes},
        )
        if created:
            command.stdout.write(command.style.SUCCESS(f'Created location {name}.'))
        locations[name] = location
    return locations


def _create_equipment(locations: dict[str, Location], command: BaseCommand) -> dict[str, Equipment]:
    """
    Create common household equipment.
    """
    equipment = {}
    for name, description, location_name, notes in EQUIPMENT_DEFINITIONS:
        location = locations.get(location_name)
        if location is None:
            raise CommandError(f'Missing location for equipment {name}: {location_name}')
        item, created = Equipment.objects.get_or_create(
            name=name,
            defaults={'description': description, 'location': location, 'notes': notes},
        )
        if created:
            command.stdout.write(command.style.SUCCESS(f'Created equipment {name}.'))
        equipment[name] = item
    return equipment


def _create_tasks(equipment_lookup: dict[str, Equipment], command: BaseCommand) -> dict[str, Task]:
    """
    Create chore task records with steps.
    """
    tasks = {}
    for chore in CHORE_DEFINITIONS:
        task_name = f'{chore["name"]} Steps'
        task, created = Task.objects.update_or_create(
            name=task_name,
            defaults={
                'description': chore['description'],
                'steps': chore['steps'],
                'notes': chore.get('notes'),
            },
        )
        if created:
            command.stdout.write(command.style.SUCCESS(f'Created task {task_name}.'))
        task_equipment = [equipment_lookup[name] for name in chore['equipment'] if name in equipment_lookup]
        task.equipment.set(task_equipment)
        tasks[chore['name']] = task
    return tasks


def _create_chores(
    locations: dict[str, Location],
    equipment_lookup: dict[str, Equipment],
    tasks: dict[str, Task],
    command: BaseCommand,
) -> None:
    """
    Create chores and attach equipment and tasks.
    """
    for chore in CHORE_DEFINITIONS:
        location = locations.get(chore['location'])
        if location is None:
            raise CommandError(f'Missing location for chore {chore["name"]}: {chore["location"]}')

        defaults = {
            'description': chore['description'],
            'points': chore['points'],
            'location': location,
            'is_recurring': True,
            'recurrence': chore['recurrence'],
            'recurrence_day_of_week': chore.get('recurrence_day_of_week'),
            'recurrence_day_of_month': chore.get('recurrence_day_of_month'),
            'age_restricted': chore.get('age_restricted', False),
            'minimum_age': chore.get('minimum_age'),
            'notes': chore.get('notes'),
        }

        chore_obj, created = Chore.objects.update_or_create(
            name=chore['name'],
            defaults=defaults,
        )
        if created:
            command.stdout.write(command.style.SUCCESS(f'Created chore {chore["name"]}.'))

        equipment_items = [equipment_lookup[name] for name in chore['equipment'] if name in equipment_lookup]
        chore_obj.equipment.set(equipment_items)
        task = tasks.get(chore['name'])
        if task:
            chore_obj.tasks.set([task])


class Command(BaseCommand):
    help = 'Sets up fake data for testing and development purposes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--parents',
            type=int,
            default=DEFAULT_PARENT_COUNT,
            help='Number of parent users to create (1-2).',
        )
        parser.add_argument(
            '--children',
            type=int,
            default=DEFAULT_CHILD_COUNT,
            help='Number of child users to create (1-8).',
        )
        parser.add_argument(
            '--child-age',
            type=int,
            default=None,
            help='Age for the single child when --children is 1.',
        )

    def handle(self, *args, **options) -> None:
        """
        Seed the database with initial development data.
        """
        parents = options['parents']
        children = options['children']
        child_age = options['child_age']

        _validate_counts(parents, children)
        if children > 1 and child_age is not None:
            self.stdout.write(self.style.WARNING('--child-age is ignored when --children is greater than 1.'))

        child_ages = _build_child_ages(children, child_age)
        if children >= 2 and not any(5 <= age <= 12 for age in child_ages):
            raise CommandError('At least one child must be between ages 5 and 12 when --children is >= 2.')

        today = timezone.localdate()

        with transaction.atomic():
            _create_users(parents, child_ages, today, self)
            locations = _create_locations(self)
            equipment = _create_equipment(locations, self)
            tasks = _create_tasks(equipment, self)
            _create_chores(locations, equipment, tasks, self)

        self.stdout.write(self.style.SUCCESS('Fake data setup completed.'))
