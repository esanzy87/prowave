"""
webmd.views

파일 경로를 인자로 받아서 파일을 스트림하는 endpoint
"""
import os
from django.conf import settings
from django.core.files.base import ContentFile
from django.http.response import HttpResponse
from django.views.decorators.csrf import csrf_exempt


# Create your views here.
@csrf_exempt
def files(request, traj_id, filename):
    """
    webmd_data direcotory의 파일을 스트림하는 view
    """
    file_path = os.path.join(settings.WEBMD_DATA_DIR, traj_id, filename)

    if request.method == 'POST':
        file = request.FILES.get('file')
        base_dir = os.path.dirname(file_path)
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        with open(file_path, 'wb') as stream:
            for chunk in file.chunks():
                stream.write(chunk)
            return HttpResponse("File uploaded successfully.", status=201)    

    if not os.path.exists(file_path):
        return HttpResponse("File not found.", status=404)

    with open(file_path, 'rb') as stream:
        file_to_send = ContentFile(stream.read())
        response = HttpResponse(file_to_send, 'application/octet-stream')
        response['Content-Length'] = file_to_send.size
        response['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(file_path)
        return response
