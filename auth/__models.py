from django.contrib.auth.models import User
from django.db import models


class UserInfo(models.Model):
    """
    Extension for Django User Model
    """
    class Meta:
        db_table = 'prowave_userinfo'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_info')
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    department = models.CharField(max_length=200, blank=True)
    title = models.CharField(max_length=100, blank=True)
