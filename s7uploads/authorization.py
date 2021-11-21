def authorize_file_upload(request):
    return request.user.is_authenticated
