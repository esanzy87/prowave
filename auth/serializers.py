"""
auth.serializers
"""
from rest_framework import serializers
from prowave.models import UserInfo


class UserSerializer(serializers.ModelSerializer):
    """
    회원
    """
    name = serializers.ReadOnlyField()
    email = serializers.ReadOnlyField()
    is_active = serializers.ReadOnlyField()

    class Meta:
        model = UserInfo
        fields = ('country', 'state', 'city', 'organization', 'department',
                  'title', 'name', 'email', 'is_active')
