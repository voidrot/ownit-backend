from apps.users.models import User


def is_member(user: User, group_name: str) -> bool:
    """Check if a user is a member of a group."""
    return user.groups.filter(name=group_name).exists()

def is_parent(user: User) -> bool:
    """Check if a user is a parent."""
    return is_member(user, 'parent')

def is_child(user: User) -> bool:
    """Check if a user is a child."""
    return is_member(user, 'child')
