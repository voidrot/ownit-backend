import pytest
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.utils import timezone

from apps.chores import api
from apps.chores.models import Assignment, AssignmentEvidence, Chore
from apps.users.models import User

pytestmark = pytest.mark.django_db


@pytest.fixture()
def request_factory() -> RequestFactory:
    """Provide a request factory for building API requests."""
    return RequestFactory()


@pytest.fixture()
def groups(db) -> dict[str, Group]:
    """Ensure the parent and child groups exist."""
    child_group, _ = Group.objects.get_or_create(name="child")
    parent_group, _ = Group.objects.get_or_create(name="parent")
    return {"child": child_group, "parent": parent_group}


@pytest.fixture()
def child_user(groups) -> User:
    """Create an active child user."""
    user = User.objects.create_user(username="child", password="pass")
    user.groups.add(groups["child"])
    return user


@pytest.fixture()
def parent_user(groups) -> User:
    """Create an active parent user."""
    user = User.objects.create_user(username="parent", password="pass")
    user.groups.add(groups["parent"])
    return user


def _create_assignment(child: User) -> Assignment:
    """Create a basic assignment for the provided child."""
    chore = Chore.objects.create(name="Clean room", disabled=False, is_recurring=False)
    return Assignment.objects.create(chore=chore, assigned_to=child, due_date=timezone.now())


def test_list_child_assignments_as_child(request_factory: RequestFactory, child_user: User):
    """Return active assignments when the child requests their own list."""
    assignment = _create_assignment(child_user)
    request = request_factory.get("/api/v1/chores/children/{}/assignments".format(child_user.id))
    request.auth = child_user

    result = api.list_child_assignments(request, child_user.id)

    assert isinstance(result, list)
    assert result[0].assignment_id == assignment.id
    assert result[0].chore.id == assignment.chore_id


def test_list_child_assignments_for_other_child_denied(
    request_factory: RequestFactory, child_user: User
):
    """Reject child access to another child's assignments."""
    other_child = User.objects.create_user(username="other-child", password="pass")
    other_child.groups.add(Group.objects.get(name="child"))

    request = request_factory.get("/api/v1/chores/children/{}/assignments".format(other_child.id))
    request.auth = child_user

    result = api.list_child_assignments(request, other_child.id)

    assert result[0] == 403


def test_get_assignment_detail_includes_evidence(
    request_factory: RequestFactory, parent_user: User, child_user: User
):
    """Include evidence URLs in the assignment detail response."""
    assignment = _create_assignment(child_user)
    evidence = AssignmentEvidence.objects.create(
        assignment=assignment,
        photo=SimpleUploadedFile("photo.jpg", b"photo-bytes", content_type="image/jpeg"),
    )

    request = request_factory.get("/api/v1/chores/assignments/{}".format(assignment.id))
    request.auth = parent_user

    result = api.get_assignment_detail(request, assignment.id)

    assert result.assignment_id == assignment.id
    assert result.evidence[0].id == evidence.id
    assert "/chore/evidence/photos/" in (result.evidence[0].photo_url or "")


def test_child_marks_ready_for_approval(request_factory: RequestFactory, child_user: User):
    """Allow a child to mark an assignment ready for approval."""
    assignment = _create_assignment(child_user)
    request = request_factory.patch(
        "/api/v1/chores/assignments/{}/ready-for-approval".format(assignment.id)
    )
    request.auth = child_user

    result = api.mark_assignment_ready_for_approval(request, assignment.id)
    assignment.refresh_from_db()

    assert result.pending_approval is True
    assert assignment.is_completed is True


def test_parent_marks_incomplete(request_factory: RequestFactory, parent_user: User, child_user: User):
    """Allow a parent to reset an assignment back to incomplete."""
    assignment = _create_assignment(child_user)
    assignment.is_completed = True
    assignment.pending_approval = True
    assignment.completed_at = timezone.now()
    assignment.save(update_fields=["is_completed", "pending_approval", "completed_at"])

    request = request_factory.patch(
        "/api/v1/chores/assignments/{}/mark-incomplete".format(assignment.id)
    )
    request.auth = parent_user

    result = api.mark_assignment_incomplete(request, assignment.id)
    assignment.refresh_from_db()

    assert result.is_completed is False
    assert assignment.pending_approval is False
    assert assignment.completed_at is None


def test_parent_approves_assignment(request_factory: RequestFactory, parent_user: User, child_user: User):
    """Allow a parent to approve and close an assignment."""
    assignment = _create_assignment(child_user)

    request = request_factory.patch("/api/v1/chores/assignments/{}/approve".format(assignment.id))
    request.auth = parent_user

    result = api.approve_assignment(request, assignment.id)
    assignment.refresh_from_db()

    assert result.approved is True
    assert assignment.closed is True


def test_upload_evidence_requires_file(request_factory: RequestFactory, child_user: User):
    """Reject evidence uploads with no file payload."""
    assignment = _create_assignment(child_user)
    request = request_factory.post("/api/v1/chores/assignments/{}/evidence".format(assignment.id))
    request.auth = child_user

    result = api.upload_assignment_evidence(request, assignment.id)

    assert result[0] == 400


def test_upload_evidence_rejects_photo_and_video(
    request_factory: RequestFactory, child_user: User
):
    """Reject evidence uploads that include both photo and video."""
    assignment = _create_assignment(child_user)
    request = request_factory.post("/api/v1/chores/assignments/{}/evidence".format(assignment.id))
    request.auth = child_user

    photo = SimpleUploadedFile("photo.jpg", b"photo-bytes", content_type="image/jpeg")
    video = SimpleUploadedFile("video.mp4", b"video-bytes", content_type="video/mp4")

    result = api.upload_assignment_evidence(request, assignment.id, photo=photo, video=video)

    assert result[0] == 400


def test_delete_evidence_blocked_after_completion(
    request_factory: RequestFactory, parent_user: User, child_user: User
):
    """Prevent evidence deletion after completion."""
    assignment = _create_assignment(child_user)
    evidence = AssignmentEvidence.objects.create(
        assignment=assignment,
        photo=SimpleUploadedFile("photo.jpg", b"photo-bytes", content_type="image/jpeg"),
    )
    assignment.is_completed = True
    assignment.save(update_fields=["is_completed"])

    request = request_factory.delete(
        "/api/v1/chores/assignments/{}/evidence/{}".format(assignment.id, evidence.id)
    )
    request.auth = parent_user

    result = api.delete_assignment_evidence(request, assignment.id, evidence.id)

    assert result[0] == 409


def test_upload_evidence_batch_requires_files(request_factory: RequestFactory, child_user: User):
    """Reject batch uploads without photo or video files."""
    assignment = _create_assignment(child_user)
    request = request_factory.post(
        "/api/v1/chores/assignments/{}/evidence/batch".format(assignment.id)
    )
    request.auth = child_user

    result = api.upload_assignment_evidence_batch(request, assignment.id)

    assert isinstance(result, tuple)
    assert result[0] == 400


def test_upload_evidence_batch_adds_multiple_files(
    request_factory: RequestFactory, child_user: User
):
    """Create evidence records for multiple uploaded files."""
    assignment = _create_assignment(child_user)
    request = request_factory.post(
        "/api/v1/chores/assignments/{}/evidence/batch".format(assignment.id)
    )
    request.auth = child_user

    photos = [
        SimpleUploadedFile("photo-1.jpg", b"photo-1", content_type="image/jpeg"),
        SimpleUploadedFile("photo-2.jpg", b"photo-2", content_type="image/jpeg"),
    ]
    videos = [
        SimpleUploadedFile("video-1.mp4", b"video-1", content_type="video/mp4"),
    ]

    result = api.upload_assignment_evidence_batch(
        request,
        assignment.id,
        photos=photos,
        videos=videos,
    )

    assert isinstance(result, tuple)
    assert result[0] == 201
    assert len(result[1]) == 3
    assert AssignmentEvidence.objects.filter(assignment=assignment).count() == 3
