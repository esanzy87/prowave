"""
auth.serializers
"""
from django.contrib.auth.models import User
from rest_framework import serializers
from prowave.models import UserInfo


class ProfileSerializer(serializers.ModelSerializer):
    """
    사용자 정보
    """
    class Meta:
        model = UserInfo
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    """
    사용자 (인증)
    """
    profile = ProfileSerializer()

    class Meta:
        model = User
        fields = '__all__'
