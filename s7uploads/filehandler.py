import os
from django.conf import settings
from django.http import HttpResponse, Http404
from django.utils import timezone
from .models import Upload, User, S7User, Screenshot, File, UploadVersion
from .taghandler import add_tag


def add_version_to_db(form, filepath, upload):
    url = filepath
    version_notes = form.cleaned_data["versionNotes"]
    version_name = form.cleaned_data["versionNumber"]

    file_model = File(url=url)

    print(version_notes)
    print(version_name)

    file_model.save()

    version = UploadVersion(
        upload_id=upload,
        file_id=file_model,
        date_added=timezone.now(),
        version_notes=version_notes,
        version_name=version_name,
        num_downloads=0,
        avg_rating=0.0,
    )

    version.save()


def add_upload_to_db(form, filepath, user):
    upload = Upload(
        user=S7User.objects.get(user=User.objects.get(id=user.id)),
        title=form.cleaned_data["title"],
        description=form.cleaned_data["description"],
        total_downloads=0,
    )

    upload.save()

    # add the corresponding UploadVersion
    add_version_to_db(form, filepath, upload)

    # add tags
    add_tag(str(form.cleaned_data["tagline"]), upload)

    return upload


def add_screenshot_to_db(form, filepath, upload):
    screenshot = Screenshot(url=filepath, upload=upload)

    screenshot.save()


def valid_upload_ext(filename):
    extension = filename.split(".")[-1]
    return extension in ["zip", "tgz", "tar", "gz"]


def valid_screenshot_ext(filename):
    extension = filename.split(".")[-1]
    return extension in ["png", "jpg", "jpeg", "gif", "bmp"]


def handle_uploaded_file(form, f, user):
    filepath = settings.MEDIA_ROOT + f.name
    filename = f.name.split(".", 1)
    inc = 0

    # generate unique filename if the given name already exists
    # form is filename(n).ext
    while os.path.isfile(filepath):
        filepath = settings.MEDIA_ROOT + filename[0] + "(" + str(inc) + ")"
        if len(filename) > 1:
            filepath += "." + filename[1]
        inc += 1

    with open(filepath, "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    upload = add_upload_to_db(form, filepath, user)
    return upload


def handle_uploaded_screenshot(form, f, upload):
    filepath = f.name
    filename = f.name.split(".", 1)
    inc = 0

    # generate unique filename if the given name already exists
    # form is filename(n).ext
    while os.path.isfile(filepath):
        filepath = filename[0] + "(" + str(inc) + ")"
        if len(filename) > 1:
            filepath += "." + filename[1]
        inc += 1

    with open(settings.MEDIA_ROOT + filepath, "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    add_screenshot_to_db(form, filepath, upload)


def handle_download_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/zip")
            response["Content-Disposition"] = "inline; filename=" + os.path.basename(
                file_path
            )
            return response
    else:
        print("File does not exist! ", file_path)

    # todo: instead of 404 we should let the user now the file couldn't be found and redirect to index
    raise Http404


def handle_edit_upload(form, upload):
    data = form.cleaned_data
    tagline = data.pop("tagline")
    print(data)
    version = UploadVersion.objects.filter(pk=upload.id)
    upload_id = UploadVersion.objects.get(pk=upload.id).upload_id.id
    upload = Upload.objects.filter(pk=upload_id)
    upload.update(**{"title": data["title"]})
    version.update(**{"version_notes": data["versionNotes"]})
    version.update(**{"version_name": data["versionNumber"]})

    if len(tagline) > 0:
        add_tag(str(tagline), Upload.objects.get(pk=upload_id))


def handle_version_upload(form, filepath, upload):
    data = form.cleaned_data
    tagline = str(form.cleaned_data["tagline"])
    print(data)
    upload_id = UploadVersion.objects.get(pk=upload.id).upload_id.id
    upload = Upload.objects.get(pk=upload_id)
    Upload.objects.filter(pk=upload_id).update(**{"description": data["description"]})

    # add the corresponding UploadVersion
    add_version_to_db(form, filepath, upload)

    # add tags
    add_tag(tagline, upload)
