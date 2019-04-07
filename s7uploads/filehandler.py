from django.conf import settings
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
    filepath = str(timezone.now()) + f.name

    with open(filepath, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    add_upload_to_db(form, filepath, user)
