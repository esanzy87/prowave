"""
auth.serializers
"""
from rest_framework import serializers


class UserSerializer(serializers.Serializer):
    """
    사용자 (인증)
    """
    user_id = serializers.IntegerField(source='id')
    name = serializers.CharField(source='first_name')
    email = serializers.EmailField()
    country = serializers.CharField(source='info.country')
    organization = serializers.CharField(source='info.organization')
    title = serializers.CharField(source='info.title')
