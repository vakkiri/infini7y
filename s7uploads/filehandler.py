from django.conf import settings

def handle_uploaded_file(f):
	with open(f.name, 'wb+') as destination:
		for chunk in f.chunks():
			destination.write(chunk)
