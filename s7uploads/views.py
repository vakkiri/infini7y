from django.db.models import Count
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.urls import path
from django.views import generic

from .models import Upload, Review, S7User, Tag
from .forms import ReviewForm, SearchForm, SignUpForm, UploadFileForm

from .filehandler import handle_uploaded_file, handle_uploaded_screenshot, handle_download_file
from .authorization import authorize_file_upload


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


def download_file(request, pk):
    upload = Upload.objects.get(pk=pk)
    upload.version_downloads += 1
    upload.total_downloads += 1
    upload.save(update_fields=['version_downloads', 'total_downloads'])
    print(upload.total_downloads)
    return handle_download_file(upload.url)


def upload_file(request):

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid() and authorize_file_upload(request):
            # upload file
            upload = handle_uploaded_file(form, request.FILES['file'], request.user)

            # upload screenshots
            for s in request.FILES.getlist('screenshots'):
                handle_uploaded_screenshot(form, s, upload)

            return redirect('s7uploads:index')
        # TODO: else tell the user to log in
    else:
        form = UploadFileForm()

    return render(request, 's7uploads/newupload.html', {'form': form})


class IndexView(generic.ListView):
    model = Upload
    template_name = 's7uploads/index.html'
    context_object_name = 'latest_upload_list'


    def get_queryset(self):
        num_uploads = 10
        uploads = Upload.objects.filter(uploadDate__lte=timezone.now())

        order_by = self.request.GET.get('order_by')
        order_by = '-uploadDate' if order_by is None else order_by

        target_slug = self.request.GET.get('filter')
        filter_tag = Tag.objects.filter(slug=target_slug).first()
       
        # check if we are trying to filter by a tag which does not exist
        if target_slug is not None and filter_tag is None:
            return None

        elif target_slug is not None and filter_tag is not None:
            uploads = uploads.filter(tags__id=filter_tag.id)

        if (order_by == 'ratings'):
            return sorted(uploads, key=lambda u: -u.avg_review())[:num_uploads]
        else:
            return uploads.order_by(order_by)[:num_uploads]


    def get_context_data(self, **kwargs):
        c = super(generic.ListView, self).get_context_data(**kwargs)
        user = self.request.user

        if not user.is_anonymous:
            s7user = S7User.objects.filter(user=user)[:1]
            if s7user:
                c['s7user'] = s7user.get()

        c['search_form'] = SearchForm()
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

