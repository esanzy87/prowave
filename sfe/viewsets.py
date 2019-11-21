"""
sfe.viewsets
"""
import os
# django modules
from django.contrib.auth.models import User
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.http import Http404
from django.http.response import HttpResponse
# django 3rd party modules
from rest_framework import routers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
# in project modules
from prowave.models import History, WorkHistory, Work
from auth.serializers import UserSerializer
from .serializers import (
    HistorySerializer,
    WorkHistorySerializer,
    WorkSerializer
)


class HistoryViewSet(viewsets.ModelViewSet):
    """
    접속 History
    """
    serializer_class = HistorySerializer
    queryset = History.objects.order_by('-created_at').all()


class WorkHistoryViewSet(viewsets.ModelViewSet):
    """
    ProWaVE 계산 History
    """
    serializer_class = WorkHistorySerializer
    queryset = WorkHistory.objects.order_by('-created_at').all()


class WorkViewSet(viewsets.ModelViewSet):
    """
    ProWaVE 계산
    """
    queryset = Work.objects.order_by('-created_at').all()
    serializer_class = WorkSerializer
    permission_classes = (AllowAny,)

    @transaction.atomic()
    def create(self, request, *args, **kwargs):
        """
        ProWaVE 계산 작업 생성

        :param request:
        :return:
        """
        try:
            # validate request
            assert request.data.get('mode') and request.data.get('mode') in ('m', 't', 'a', 'x')
            assert request.data.get('source') and request.data.get('source') in ('rcsb', 'upload')
            assert (request.data.get('source') == 'rcsb' and request.data.get('pdb_id')) or (request.data.get('source') == 'upload' and request.FILES.get('file'))
            assert request.data.get('email') and request.data.get('name') and request.data.get('title') and request.data.get('organization')

            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            remote_ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

            name = request.data['name']
            email = request.data['email']
            title = request.data['title']
            organization = request.data['organization']
            owner = request.user if request.user.is_authenticated else None

            if request.data['source'] == 'rcsb':                
                pdb_id = request.data['pdb_id']
                work = Work.create(
                    owner=owner,
                    source=request.data['source'],
                    mode=request.data['mode'],
                    remote_ip=remote_ip,
                    name=name,
                    email=email,
                    title=title,
                    pdb_id=pdb_id,
                    organization=organization
                )
            else:
                pdb_file = request.FILES['file']
                work = Work.create(
                    owner=owner,
                    source=request.data['source'],
                    mode=request.data['mode'],
                    remote_ip=remote_ip,
                    name=name,
                    email=email,
                    title=title,
                    file=pdb_file,
                    organization=organization
                )
            return Response(work.run(), status=201)
        except AssertionError:
            return Response(data={'created': False, 'work': None}, status=400)

    def list(self, request, *args, **kwargs):
        """
        SFEWorkList
        """
        if not request.user.is_authenticated:
            return Response(data=[])

        works = Work.objects.filter(owner=request.user).order_by('-created_at')
        return Response(data=self.serializer_class(works, many=True).data)

    @action(methods=['POST'], url_path='files', detail=True)
    def upload(self, request, pk=None):
        """
        process file upload to SEFWork's work_dir
        """
        base_dir = os.path.join(settings.PROWAVE_DATA_DIR, pk)
        file = request.FILES.get('file')
        try:
            os.makedirs(base_dir, exist_ok=True)
            full_file_path = os.path.join(base_dir, file.name)
            with open(full_file_path, 'wb') as stream:
                for chunk in file.chunks():
                    stream.write(chunk)
            return Response({'success': True}, status=201)
        except OSError:
            return HttpResponse({'success': False}, status=500)

    @action(methods=['GET'], url_path='files/model', detail=True)
    def model(self, request, pk=None):
        """
        model.pdb
        """
        base_dir = os.path.join(settings.PROWAVE_DATA_DIR, pk)
        pdb_file_path = os.path.join(base_dir, 'model.pdb')
        if not os.path.exists(pdb_file_path):
            raise Http404
        with open(pdb_file_path, 'rb') as stream:
            file_to_send = ContentFile(stream.read())
            response = HttpResponse(file_to_send, 'chemical/x-pdb')
            response['Content-Length'] = file_to_send.size
            response['Content-Disposition'] = 'attachment; filename="prowave_SFE_%s_model.pdb"' % pk
            return response

    @action(methods=['GET'], url_path='files/plot', detail=True)
    def plot(self, request, pk=None):
        """
        plot.svg
        """
        base_dir = os.path.join(settings.PROWAVE_DATA_DIR, pk)
        pdb_file_path = os.path.join(base_dir, 'plot.svg')
        if not os.path.exists(pdb_file_path):
            raise Http404
        with open(pdb_file_path, 'rb') as stream:
            file_to_send = ContentFile(stream.read())
            response = HttpResponse(file_to_send, 'image/svg+xml')
            response['Content-Length'] = file_to_send.size
            response['Content-Disposition'] = 'attachment; filename="prowave_SFE_%s_plot.svg"' % pk
            return response


router = routers.DefaultRouter()
router.register(r'histories', HistoryViewSet)
router.register(r'work-histories', WorkHistoryViewSet)
router.register(r'works', WorkViewSet)
