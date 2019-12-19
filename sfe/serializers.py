"""
sfe.serializers
"""
from rest_framework import serializers
from auth.serializers import UserSerializer
from prowave.models import History, WorkHistory, Work


class HistorySerializer(serializers.ModelSerializer):
    """
    접속 History
    """
    class Meta:
        """
        HistorySerializer.Meta
        """
        model = History
        fields = '__all__'


class WorkHistorySerializer(serializers.ModelSerializer):
    """
    ProWaVE 계산 History
    """
    class Meta:
        """
        WorkHistorySerializer.Meta
        """
        model = WorkHistory
        fields = '__all__'


class WorkSerializer(serializers.ModelSerializer):
    """
    ProWaVE 계산
    """
    owner = UserSerializer(many=False, read_only=True)
    history = WorkHistorySerializer(many=False, read_only=True)
    result = serializers.JSONField()
    status = serializers.JSONField()
    pdb = serializers.ReadOnlyField()
    # plot = serializers.ReadOnlyField()

    class Meta:
        """
        WorkSerializer.Meta
        """
        model = Work
        fields = '__all__'
