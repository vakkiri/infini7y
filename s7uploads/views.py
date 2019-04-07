from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.views import generic
from django.utils import timezone
from django.urls import path

from .models import Upload, Review, S7User
from .forms import ReviewForm, SignUpForm, UploadFileForm

from .filehandler import handle_uploaded_file

def add_review(request, pk):
	if request.method == 'POST':
		form = ReviewForm(request.POST)

		if form.is_valid():
			review = form.save(commit=False)
			review.pubDate = timezone.now()
			review.upload = Upload.objects.get(pk=pk)
			review.user = S7User.objects.get(pk=1)	# TODO: check that a usr is logged
			review.save()

			url = '/s7uploads/uploads/' + str(pk)
			return HttpResponseRedirect(url)

	else:
		form = ReviewForm()

	return render(request, 's7uploads/upload.html', {'upload': Upload.objects.get(pk=pk), 'form': form})

def user_login(request):
	if request.method == 'POST':
		form = AuthenticationForm(data=request.POST)
		
		if form.is_valid():
			username = form.cleaned_data.get('username')
			password = form.cleaned_data.get('password')
			user = authenticate(request, username=username, password=password)
			if user is not None:
				login(request, user)
				return redirect('s7uploads:index')
			else:
				# TODO: display invalid login message
				form = AuthenticationForm()
				return render(request, 's7uploads/login.html', {'form': form})
	else:
		form = AuthenticationForm()

	return render(request, 's7uploads/login.html', {'form': form})

def logout_view(request):
	logout(request)
	return redirect('s7uploads:index')

def signup(request):
	if request.method == 'POST':
		form = SignUpForm(request.POST)

		if form.is_valid():
			form.save()
			username = form.cleaned_data.get('username')
			raw_password = form.cleaned_data.get('password1')
			user = authenticate(username=username, password=raw_password)
			login(request, user)
			return redirect('s7uploads:index')
	else:
		form = SignUpForm()

	return render(request, 's7uploads/signup.html', {'form' : form})

def upload_file(request):
	if request.method == 'POST':
		form = UploadFileForm(request.POST, request.FILES)
		if form.is_valid():
			handle_uploaded_file(form, request.FILES['file'], request.user)
			return redirect('s7uploads:index')
	else:
		form = UploadFileForm()
	return render(request, 's7uploads/newupload.html', {'form': form})

class IndexView(generic.ListView):
	model = Upload
	template_name = 's7uploads/index.html'
	context_object_name = 'latest_upload_list'
	
	def get_queryset(self):
		numUploads = 10
		#return 10 most recent uploads
		return Upload.objects.filter(uploadDate__lte=timezone.now()).order_by('-uploadDate')[:numUploads]

	def get_context_data(self, **kwargs):
		c = super(generic.ListView, self).get_context_data(**kwargs)
		user = self.request.user
		if not user.is_anonymous:
			s7user = S7User.objects.filter(user=user)[:1]
			if s7user:
				c['s7user'] = s7user.get()
		return c

class ReviewView(generic.ListView):
	model = Review
	template_name = 's7uploads/reviews.html'
	context_object_name = 'latest_review_list'

	def get_queryset(self):
		numReviews = 25
		return Review.objects.filter(pubDate__lte=timezone.now()).order_by('-pubDate')[:numReviews]

	def get_context_data(self, **kwargs):
		c = super(generic.ListView, self).get_context_data(**kwargs)
		user = self.request.user
		if not user.is_anonymous:
			s7user = S7User.objects.filter(user=user)[:1]
			if s7user:
				c['s7user'] = s7user.get()
		return c

class UserListView(generic.ListView):
	model = S7User
	template_name = 's7uploads/users.html'
	context_object_name = 'user_list'

	def get_queryset(self):
		# return S7User.objects.all().extra( select={'lower_name':'lower(user.username)'}).order_by('lower_name')
		return S7User.objects.all()

	def get_context_data(self, **kwargs):
		c = super(generic.ListView, self).get_context_data(**kwargs)
		user = self.request.user
		if not user.is_anonymous:
			s7user = S7User.objects.filter(user=user)[:1]
			if s7user:
				c['s7user'] = s7user.get()
		return c


class UploadView(generic.DetailView):
	model = Upload
	template_name = 's7uploads/upload.html'

	def get_queryset(self):
		return Upload.objects.filter(uploadDate__lte=timezone.now())
	
	def get_context_data(self, **kwargs):
		c = super(generic.DetailView, self).get_context_data(**kwargs)
		user = self.request.user
		if not user.is_anonymous:
			s7user = S7User.objects.filter(user=user)[:1]
			if s7user:
				c['s7user'] = s7user.get()
		return c

