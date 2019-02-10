from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render
from django.views import generic
from django.utils import timezone
from django.urls import path

from .models import Upload, Review, User
from .forms import ReviewForm

def add_review(request, pk):
	if request.method == "POST":
		form = ReviewForm(request.POST)

		if form.is_valid():
			review = form.save(commit=False)
			review.pubDate = timezone.now()
			review.upload = Upload.objects.get(pk=pk)
			review.user = User.objects.get(pk=1)	# TODO: check that a usr is logged
			review.save()

			url = '/s7uploads/uploads/' + str(pk)
			return HttpResponseRedirect(url)

	else:
		form = ReviewForm()

	return render(request, 's7uploads/upload.html', {'upload': pk, 'form': form})


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

	def get_context_data(self, **kwargs):
		context = super(UploadView, self).get_context_data(**kwargs)
		context['form'] = ReviewForm()
		return context
