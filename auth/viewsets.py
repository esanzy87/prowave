"""
auth.viewsets
"""
from rest_framework import viewsets, routers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from prowave.models import UserInfo
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    회원
    """
    serializer_class = UserSerializer
    queryset = UserInfo.objects.all()
    permission_classes = (AllowAny,)

    def get_queryset(self):
        if self.request.user.is_authenticated:
            if self.request.user.is_superuser:
                return self.queryset
            return self.queryset.filter(user=self.request.user)
        raise PermissionDenied

    def retrieve(self, request, *args, **kwargs):
        user_info = self.get_object()
        if request.user.is_authenticated and user_info.user.id == request.user.id:
            return super().retrieve(request, *args, **kwargs)
        raise PermissionDenied


router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
