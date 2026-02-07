from django.db import models
from django.core.validators import MinValueValidator
import datetime
# Create your models here.


class Chore(models.Model):
    # Chore Recurrence Types
    DAILY = 'D'
    WEEKLY = 'W'
    MONTHLY = 'M'
    RECURRENCE_TYPE_CHOICES = (
        (DAILY, 'Daily'),
        (WEEKLY, 'Weekly'),
        (MONTHLY, 'Monthly'),
    )

    name = models.CharField(max_length=255, help_text='Short label shown in chore lists.')
    description = models.TextField(blank=True, help_text='Optional details to help complete the chore.')
    points = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0)], help_text='Points awarded when the chore is completed.'
    )
    penalize_incomplete = models.BooleanField(
        default=False, help_text='Deduct points if the chore is not completed by the due date.'
    )
    penalty_amount = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Percent of points to deduct for incomplete chores (0-100).',
    )
    is_recurring = models.BooleanField(default=True)
    recurrence_day_of_week = models.CharField(
        max_length=60, blank=True, null=True, help_text='Weekly schedule label (e.g., "Monday").'
    )
    recurrence_day_of_month = models.CharField(
        max_length=90, blank=True, null=True, help_text='Monthly schedule label (e.g., "15").'
    )
    recurrence = models.CharField(
        max_length=1,
        choices=RECURRENCE_TYPE_CHOICES,
        default=None,
        null=True,
        blank=True,
        help_text='Recurrence cadence when the chore is recurring.',
    )
    instructions_video = models.FileField(
        upload_to='chore/instruction/videos/', null=True, blank=True, help_text='Optional video stored in the system.'
    )
    instructions_video_name = models.CharField(
        max_length=255, blank=True, help_text='Filename to show in the UI for the instructions video.'
    )
    instructions_video_source = models.URLField(
        null=True, blank=True, help_text='External video link if not stored locally.'
    )
    location = models.ForeignKey(
        'Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chores',
        help_text='Where the chore is usually done.',
    )
    equipment = models.ManyToManyField(
        'Equipment', blank=True, related_name='chores', help_text='Equipment required for this chore.'
    )
    tasks = models.ManyToManyField(
        'Task', blank=True, related_name='chores', help_text='Optional steps that make up this chore.'
    )
    notes = models.JSONField(blank=True, null=True, help_text='Optional structured metadata for the chore.')
    time_due = models.TimeField(null=True, blank=True, help_text='Optional time of day when the chore is due.')
    age_restricted = models.BooleanField(
        default=False, help_text='Whether this chore should be restricted based on user age.'
    )
    minimum_age = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text='Minimum age required to be assigned this chore (if age_restricted is True).',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(is_recurring=True, recurrence__isnull=True), name='chore_recurrence_consistency'
            ),
            models.CheckConstraint(
                condition=~models.Q(recurrence='W', recurrence_day_of_week__isnull=True),
                name='chore_weekly_requires_day_of_week',
            ),
            models.CheckConstraint(
                condition=~models.Q(recurrence='W', recurrence_day_of_week=''),
                name='chore_weekly_day_of_week_not_empty',
            ),
            models.CheckConstraint(
                condition=~models.Q(recurrence='W', recurrence_day_of_month__isnull=False),
                name='chore_weekly_day_of_month_must_be_null',
            ),
            models.CheckConstraint(
                condition=~models.Q(recurrence='M', recurrence_day_of_month__isnull=True),
                name='chore_monthly_requires_day_of_month',
            ),
            models.CheckConstraint(
                condition=~models.Q(recurrence='M', recurrence_day_of_month=''),
                name='chore_monthly_day_of_month_not_empty',
            ),
            models.CheckConstraint(
                condition=~models.Q(recurrence='M', recurrence_day_of_week__isnull=False),
                name='chore_monthly_day_of_week_must_be_null',
            ),
            models.CheckConstraint(
                # minimum_age may have a value only when age_restricted is True
                condition=~models.Q(minimum_age__isnull=False, age_restricted=False),
                name='chore_minimum_age_requires_age_restricted',
            ),
            models.CheckConstraint(
                # if age_restricted is True then minimum_age must be set (not null)
                condition=~models.Q(age_restricted=True, minimum_age__isnull=True),
                name='chore_age_restricted_requires_minimum_age',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.name}'


class Equipment(models.Model):
    name = models.CharField(max_length=255, help_text='Short label shown in equipment lists.', unique=True)
    description = models.TextField(blank=True, help_text='Optional details about the equipment.')
    location = models.ForeignKey(
        'Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='equipment',
        help_text='Where the equipment is stored.',
    )
    notes = models.JSONField(blank=True, null=True, help_text='Optional structured metadata for the equipment.')
    image = models.ImageField(
        upload_to='chore/equipment/images/', null=True, blank=True, help_text='Optional photo of the equipment.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.name}'


class Location(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text='Short label shown in location lists.')
    description = models.TextField(blank=True, help_text='Optional details about the location.')
    notes = models.JSONField(blank=True, null=True, help_text='Optional structured metadata for the location.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.name}'


class Task(models.Model):
    name = models.CharField(max_length=255, unique=True, help_text='Short label shown in task lists.')
    description = models.TextField(blank=True, help_text='Optional details to help complete the task.')
    equipment = models.ManyToManyField(
        'Equipment', blank=True, related_name='tasks', help_text='Equipment required for this task.'
    )
    steps = models.JSONField(blank=True, null=True, help_text='Optional structured steps and media links.')
    notes = models.JSONField(blank=True, null=True, help_text='Optional structured metadata for the task.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.name}'


class AssignmentEvidence(models.Model):
    assignment = models.ForeignKey(
        'Assignment',
        on_delete=models.CASCADE,
        related_name='evidence',
        help_text='Assignment this evidence belongs to.',
    )
    photo = models.ImageField(
        upload_to='chore/evidence/photos/', null=True, blank=True, help_text='Optional photo evidence.'
    )
    video = models.FileField(
        upload_to='chore/evidence/videos/', null=True, blank=True, help_text='Optional video evidence.'
    )
    notes = models.JSONField(blank=True, null=True, help_text='Optional structured metadata for the evidence.')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'Evidence for assignment {self.assignment.id} created at {self.created_at}'


class Assignment(models.Model):
    chore = models.ForeignKey(
        Chore, on_delete=models.CASCADE, related_name='assignments', help_text='Chore being assigned.'
    )
    assigned_to = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='chore_assignments',
        help_text='User responsible for completing the chore.',
    )
    due_date = models.DateTimeField(help_text='Date and time when the assignment is due.')
    pending_approval = models.BooleanField(default=False, help_text='Awaiting approval before points are awarded.')
    approved = models.BooleanField(default=False, help_text='Approved and points have been awarded.')
    approved_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.JSONField(blank=True, null=True, help_text='Optional structured metadata for the assignment.')
    closed = models.BooleanField(default=False, help_text='Closed assignments cannot be completed or approved.')
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        chore_name = self.chore.name if self.chore else 'Unknown'
        return f'Assignment of chore {chore_name} due on {self.due_date}'
