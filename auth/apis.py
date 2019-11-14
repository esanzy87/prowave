"""
auth.apis
"""
import re
import smtplib
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.db import transaction
from django.db.utils import IntegrityError, DatabaseError
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

# from auth.models import UserInfo
from prowave.models import UserInfo
from auth.serializers import UserSerializer


# private functions
def send_email_verification(email, fail_silently=False):
    user = User.objects.get(email=email)
    message = """
        verification URL: http://127.0.0.1:8000/api/auth/verify-email/?u={}&t={}
    """.format(user.id, PasswordResetTokenGenerator().make_token(user))

    send_mail(
        'Email verification',
        message,
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=fail_silently,
    )


# Create your views here.
@api_view(['GET'])
@permission_classes((AllowAny,))
def check_email_availability(request):
    email = request.GET.get('email')

    msg_check_email_availability__available = '사용 가능한 이메일입니다.'
    msg_check_email_availability__not_available = '사용중인 이메일입니다.'
    msg_check_email_availability__not_valid = '유효한 이메일 형식이 아닙니다.'

    if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return Response({'available': False, 'message': msg_check_email_availability__not_valid})
    try:
        User.objects.get(email=email)
        return Response({'available': False, 'message': msg_check_email_availability__not_available})
    except User.DoesNotExist:
        return Response({'available': True, 'message': msg_check_email_availability__available})


@api_view(['POST'])
@permission_classes((AllowAny,))
@transaction.atomic()
def create_user(request):
    email = request.data['email']
    password = request.data['password']

    try:
        first_name = request.data['name']
        user = User.objects.create_user(username=email, email=email, password=password, is_active=False,
                                        first_name=first_name)
        organization = request.data['organization']
        title = request.data['title']
        UserInfo.objects.create(user=user, organization=organization, title=title)
        send_email_verification(user.email, fail_silently=True)
        return Response({'created': True, 'user': UserSerializer(user).data, 'message': '''User account created 
        successfully, Please check your e-mail inbox and follow instruction to verify your e-mail address and 
        activate account.'''})
    except IntegrityError:
        return Response({'created': False, 'message': '''
            User account creation failed. Your e-mail address is already registered.'''})
    except DatabaseError:
        pass
    return Response({'created': False, 'message': 'User account creation failed.'})


@api_view(['GET'])
def myinfo(request):
    if request.user.is_authenticated:
        user_info = UserInfo.objects.get(user=request.user)
        return Response(UserSerializer(user_info).data)
    raise PermissionDenied


@api_view(['POST'])
def change_password(request):
    if not request.user.is_authenticated:
        return Response({'success': False, 'message': 'Unauthorized'}, status=401)

    new_password = request.POST['password']
    request.user.set_password(new_password)
    request.user.save()
    return Response({'success': True})


@api_view(['POST'])
def send_email_verification_api(request):
    email = request.POST['email']
    try:
        send_email_verification(email)
        return Response({'success': True})
    except smtplib.SMTPException:
        return Response({'success': False, 'message': 'sending email with SMTP failed.'}, status=500)
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'email not found.'}, status=404)


@api_view(['GET'])
def verify_email(request):
    user_id = request.GET.get('u')
    token = request.GET.get('t', '')

    try:
        user = User.objects.get(id=user_id)
        if PasswordResetTokenGenerator().check_token(user, token):
            user.is_active = True
            user.save()
        return Response({'success': True, 'message': 'email verified successfully.'})
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'email not found.'}, status=404)
