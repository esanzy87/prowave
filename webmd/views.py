import os
import yaml
from django.conf import settings
from django.core.files.base import ContentFile
from django.http.response import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from yaml import Loader


# Create your views here.
@csrf_exempt
def userdata(request, user_id, filename):
    file_path = os.path.join(settings.WEBMD_USERDATA_DIR,
                             '{user_id}/{filename}'.format(user_id=user_id, filename=filename))

    if request.method == 'POST':
        file = request.FILES.get('file')
        try:
            work_dir = os.path.dirname(file_path)
            if not os.path.exists(work_dir):
                os.makedirs(work_dir, exist_ok=True)

            with open(file_path, 'wb') as f:
                for chunk in file.chunks():
                    f.write(chunk)
                return HttpResponse("File uploaded successfully.", status=201)
        except OSError:
            return HttpResponse("Request failed due to OSError.", status=500)
    else:
        try:
            file_ext = file_path.split('.')[-1]
            if file_ext == 'yml' and request.GET.get('parse'):
                with open(file_path, 'r') as f:
                    data = yaml.load(f, Loader=Loader)
                    return JsonResponse(data)

            with open(file_path, 'rb') as f:
                file_to_send = ContentFile(f.read())
                response = HttpResponse(file_to_send, 'application/octet-stream')
                response['Content-Length'] = file_to_send.size
                response['Content-Disposition'] = 'attachment; filename="%s"' % filename
                return response
        except FileNotFoundError:
            return HttpResponse("File not found.", status=404)
