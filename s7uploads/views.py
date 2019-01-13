from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.views import generic
from django.utils import timezone

from .models import Upload, Review, User

class IndexView(generic.ListView):
	model = Upload
	template_name = 's7uploads/index.html'
	context_object_name = 'latest_upload_list'
	
	def get_queryset(self):
		numUploads = 10
		#return 10 most recent uploads
		return Upload.objects.filter(uploadDate__lte=timezone.now()).order_by('-uploadDate')[:numUploads]

class ReviewView(generic.ListView):
	model = Review
	template_name = 's7uploads/reviews.html'
	context_object_name = 'latest_review_list'

	def get_queryset(self):
		numReviews = 25
		return Review.objects.filter(pubDate__lte=timezone.now()).order_by('-pubDate')[:numReviews]

class UserListView(generic.ListView):
	model = User
	template_name = 's7uploads/users.html'
	context_object_name = 'user_list'

	def get_queryset(self):
		return User.objects.all().extra( select={'lower_name':'lower(username)'}).order_by('lower_name')

class UploadView(generic.DetailView):
	model = Upload
	template_name = 's7uploads/upload.html'
	def get_queryset(self):
		return Upload.objects.filter(uploadDate__lte=timezone.now())

