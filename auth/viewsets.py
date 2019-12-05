"""
auth.viewsets
"""
from django.contrib.auth.models import User
from django.db import transaction, IntegrityError
from rest_framework import viewsets, routers, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from prowave.models import UserInfo
from .serializers import UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    회원
    """
    serializer_class = UserSerializer
    queryset = User.objects.all()
    permission_classes = (AllowAny,)

    def get_queryset(self):
        """
        UserViewSet.get_queryset
        """
        if self.request.user.is_authenticated:
            if self.request.user.is_superuser:
                return self.queryset
            return self.queryset.filter(user=self.request.user)
        raise PermissionDenied

    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        """
        UserViewSet.create
        """
        try:
            create_user_args = {
                'username': request.data['email'],
                'email': request.data['email'],
                'password': request.data['password'],
                'first_name': request.data['name'],
            }

            instance = User.objects.create_user(**create_user_args)

            create_user_info_args = {
                'country': request.data['country'],
                'organization': request.data['organization'],
                'title': request.data['title'],
                'user': instance
            }

            UserInfo.objects.create(**create_user_info_args)
        except KeyError as error:
            return Response({
                'success': False,
                'detail': 'Required field %s is not provided.' % error
            }, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response({
                'success': False,
                'detail': 'The email you have entered (%s) already exists.' % request.data['email']
            }, status=status.HTTP_403_FORBIDDEN)
        except:
            return Response({
                'success': False,
                'detail': 'Sorry, We have failed to register your information. We will try to fix this issue as soon as possible.'
            })

        return Response({
            'success': True,
            'created_user': self.serializer_class(instance).data,
        }, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        raise PermissionDenied(detail="This API is not supported.")

    def retrieve(self, request, *args, **kwargs):
        """
        UserViewSet.retrieve
        """
        instance = self.get_object()
        if request.user.is_authenticated and instance.id == request.user.id:
            return super().retrieve(request, *args, **kwargs)
        raise PermissionDenied

    @action(detail=False, methods=['get'])
    def whoami(self, request):
        """
        UserViewSet.whoami
        """
        if not request.user.is_authenticated:
            raise PermissionDenied
        return Response(self.serializer_class(request.user).data)


router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
