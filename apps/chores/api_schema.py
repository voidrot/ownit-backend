from datetime import datetime, time
from typing import Optional

from ninja import Schema


class ErrorSchema(Schema):
    message: str


class ChoreSummarySchema(Schema):
    id: int
    name: str
    description: str
    points: int


class EvidenceSchema(Schema):
    id: int
    photo_url: Optional[str]
    video_url: Optional[str]
    created_at: datetime


class AssignmentSummarySchema(Schema):
    assignment_id: int
    due_date: datetime
    is_completed: bool
    pending_approval: bool
    approved: bool
    closed: bool
    chore: ChoreSummarySchema


class AssignmentDetailSchema(AssignmentSummarySchema):
    approved_at: Optional[datetime]
    completed_at: Optional[datetime]
    closed_at: Optional[datetime]
    evidence: list[EvidenceSchema]


class LocationSchema(Schema):
    id: int
    name: str
    description: str
    notes: Optional[dict]


class EquipmentSchema(Schema):
    id: int
    name: str
    description: str
    location: Optional[LocationSchema]
    notes: Optional[dict]
    image_url: Optional[str]


class TaskSchema(Schema):
    id: int
    name: str
    description: str
    notes: Optional[dict]
    steps: Optional[dict]
    equipment: list[EquipmentSchema]


class ChoreDetailSchema(Schema):
    id: int
    name: str
    description: str
    points: int
    penalize_incomplete: bool
    penalty_amount: int
    is_recurring: bool
    recurrence: Optional[str]
    recurrence_day_of_week: Optional[str]
    recurrence_day_of_month: Optional[str]
    instructions_video_url: Optional[str]
    instructions_video_name: str
    instructions_video_source: Optional[str]
    location: Optional[LocationSchema]
    equipment: list[EquipmentSchema]
    tasks: list[TaskSchema]
    notes: Optional[dict]
    time_due: Optional[time]
    age_restricted: bool
    minimum_age: Optional[int]
    assign_to_all: bool
    disabled: bool
