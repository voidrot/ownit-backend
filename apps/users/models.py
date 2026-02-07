from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser
from django.db import models 

class User(AbstractUser):
    """
    Default custom user model for project_name.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """
    # birth_date field is used to prevent assignment of age-restricted chores to users under a specified age. It is optional and can be left blank if not needed.
    birth_date = models.DateField(null=True, blank=True, help_text='Optional birth date of the user.')

    pass
