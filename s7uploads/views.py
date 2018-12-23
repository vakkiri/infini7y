from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.views import generic
from django.utils import timezone

from .models import Upload

# Create your views here.
class IndexView(generic.ListView):
	model = Upload
	template_name = 's7uploads/index.html'
	context_object_name = 'latest_upload_list'

	def get_queryset(self):
		numUploads = 10
		#return 10 most recent uploads
		return Upload.objects.filter(uploadDate__lte=timezone.now()).order_by('-uploadDate')[:numUploads]
