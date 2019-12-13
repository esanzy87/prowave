"""prowave URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
# from auth import apis as auth_apis
from auth import viewsets as auth_viewsets
from sfe import viewsets as sfe_viewsets
from webmd import views as webmd_views
from webmd import viewsets as webmd_viewsets
# from . import views

urlpatterns = [  # pylint: disable=invalid-name
    # auth
    # path('api/auth/check-email/', auth_apis.check_email_availability),
    # path('api/auth/create-user/', auth_apis.create_user),
    # path('api/auth/myinfo/', auth_apis.myinfo),
    # path('api/auth/verify-email/', auth_apis.verify_email),
    path('api/auth/', include(auth_viewsets.router.urls)),


    # solvation free energy
    # re_path(r^api/solvation-free-energy/files/(?P<work_id>\S+)/(?P<filename>\S+)$', sfe_views.files),
    path('api/solvation-free-energy/', include(sfe_viewsets.router.urls)),

    # webmd
    re_path(r'^api/webmd/files/(?P<traj_id>\S+)/(?P<filename>\S+)$', webmd_views.files),
    path('api/webmd/', include(webmd_viewsets.router.urls)),

    # admin
    path('admin/', admin.site.urls),

    # django-oauth2-toolkit
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),

    # global context
    # load react app
    # path('', views.home),
    # re_path('^.*/$', views.home),
]
