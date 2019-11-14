"""
ProWaVE Admin
"""
from django.contrib import admin
from .models import UserInfo, WorkHistory

# Register your models here.
@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    """
    UserInfoAdmin
    """
    list_display = ['email', 'name', 'country', 'state', 'city',
                    'organization', 'title', 'is_active']
    list_display_links = ['email']

@admin.register(WorkHistory)
class SFEWorkHistoryAdmin(admin.ModelAdmin):
    """
    SFEWorkHistoryAdmin
    """
    list_display = ['id', 'filename', 'title', 'solvent', 'box_size', 'grid_size',
                    'name', 'email', 'position', 'country_name', 'org1']
