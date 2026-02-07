import dataclasses
import uuid
from typing import Any, List, Optional, Type

from django.contrib.auth import get_user_model
from django.db import models

from allauth.account import app_settings as account_settings
from allauth.account.models import EmailAddress
from allauth.account.utils import user_display, user_username
from allauth.headless.adapter import DefaultHeadlessAdapter


class GroupAwareHeadlessAdapter(DefaultHeadlessAdapter):
    """
    Headless adapter that includes group names in the serialized user payload.
    """

    def user_as_dataclass(self, user: Any) -> Any:
        """
        Return a dataclass instance that includes group names.
        """
        UserDc = self.get_user_dataclass()
        kwargs = {}
        User = get_user_model()
        pk_field_class = type(User._meta.pk)
        if not user.pk:
            id_dc = None
        elif issubclass(pk_field_class, models.IntegerField):
            id_dc = user.pk
        else:
            id_dc = str(user.pk)
        if account_settings.USER_MODEL_USERNAME_FIELD:
            kwargs['username'] = user_username(user)
        if user.pk:
            email = EmailAddress.objects.get_primary_email(user)
        else:
            email = None
        kwargs.update(
            {
                'id': id_dc,
                'email': email if email else None,
                'display': user_display(user),
                'has_usable_password': user.has_usable_password(),
                'groups': self._group_names(user),
            }
        )
        return UserDc(**kwargs)

    def get_user_dataclass(self) -> Type:
        """
        Return a user dataclass schema that includes group names.
        """
        fields = []
        User = get_user_model()
        pk_field_class = type(User._meta.pk)
        if issubclass(pk_field_class, models.UUIDField):
            id_type = str
            id_example = str(uuid.uuid4())
        elif issubclass(pk_field_class, models.IntegerField):
            id_type = int
            id_example = 123
        else:
            id_type = str
            id_example = 'uid'

        def dc_field(attr, typ, description, example):
            return (
                attr,
                typ,
                dataclasses.field(
                    metadata={
                        'description': description,
                        'example': example,
                    }
                ),
            )

        fields.extend(
            [
                dc_field('id', Optional[id_type], 'The user ID.', id_example),
                dc_field('display', str, 'The display name for the user.', 'Magic Wizard'),
                dc_field('email', Optional[str], 'The email address.', 'email@domain.org'),
                dc_field(
                    'has_usable_password',
                    bool,
                    'Whether or not the account has a password set.',
                    True,
                ),
                dc_field(
                    'groups',
                    List[str],
                    'The group names assigned to the user.',
                    ['parent', 'child'],
                ),
            ]
        )
        if account_settings.USER_MODEL_USERNAME_FIELD:
            fields.append(dc_field('username', str, 'The username.', 'wizard'))
        return dataclasses.make_dataclass('User', fields)

    def _group_names(self, user: Any) -> List[str]:
        """
        Return the user's group names as a list of strings.
        """
        if not user or not getattr(user, 'pk', None):
            # Avoid querying groups for unsaved users.
            return []
        return list(user.groups.values_list('name', flat=True))
