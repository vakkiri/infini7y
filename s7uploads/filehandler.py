import os
from django.conf import settings
from django.http import HttpResponse, Http404
from django.utils import timezone
from .models import Upload, User, S7User


def add_upload_to_db(form, filepath, user):
    upload = Upload(
                url = filepath,
                user = S7User.objects.get(user=User.objects.get(id=user.id)),
                title = form.cleaned_data['title'],
                description = form.cleaned_data['description'],
                versionNotes = form.cleaned_data['versionNotes'],
                # todo: unittest this, make sure upload time is always correct
                uploadDate = timezone.now(),
                versionNumber = form.cleaned_data['versionNumber'],
                tagline = ""
            )

    upload.save()


def handle_uploaded_file(form, f, user):
    filepath = settings.MEDIA_ROOT + f.name
    filename = f.name.split('.', 1)
    inc = 0

    # generate unique filename if the given name already exists
    # form is filename(n).ext
    while os.path.isfile(filepath):
        filepath = settings.MEDIA_ROOT + filename[0] + '(' + str(inc) + ').'
        if len(filename) > 1:
            filepath += filename[1]
        inc += 1
    
    with open(filepath, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    add_upload_to_db(form, filepath, user)


def handle_download_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type="application/zip")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response

    raise Http404

