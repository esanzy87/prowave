"""
webmd.serializers
"""
from rest_framework import serializers
from .models import Project, Work as Trajectory


class TrajectorySerializer(serializers.ModelSerializer):
    """
    WebmdWork Serializer
    """
    class Meta:
        """
        Meta
        """
        model = Trajectory
        fields = '__all__'


class ProjectSerializer(serializers.ModelSerializer):
    """
    Project Serializer
    """
    trajectories = TrajectorySerializer(many=True)

    class Meta:
        """
        Meta
        """
        model = Project
        fields = '__all__'
