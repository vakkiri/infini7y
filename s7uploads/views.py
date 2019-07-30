import math

from django.db.models import Count, Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.urls import path
from django.views import generic

from .models import Upload, Review, S7User, Tag
from .forms import ReviewForm, SearchForm, SignUpForm, UploadFileForm

from .authorization import authorize_file_upload
from .filehandler import handle_uploaded_file, handle_uploaded_screenshot, handle_download_file
from .urltools import strip_get_tags


def search_uploads(request, params='', page=0):
    if request.method == 'POST':
        form = SearchForm(request.POST)

        if form.is_valid():
            params = strip_get_tags(params)
            get_line = '?tags=' + str(form.cleaned_data.get('search_line'))
            get_line = get_line + '&' + params if len(params) > 0 else get_line
            url = '/s7uploads/' + get_line
            return HttpResponseRedirect(url)

    else:
        form = SearchForm()
        url = '/s7uploads/' + params
        return HttpResponseRedirect(url)


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
    total_num_uploads = 0
    uploads_per_page = 2


    def get_uploads_in_range(self, uploads):
        # the -1 is due to displaying start page as 1 instead of 0 in browser
        start_page = self.kwargs['page'] - 1 if 'page' in self.kwargs else 0
        print("page ", start_page)
        start_index = start_page * self.uploads_per_page
        print("start index: ", start_index)
        end_index = start_index + self.uploads_per_page
        print("end index: ", end_index)
        return uploads[start_index:end_index]


    def get_queryset(self):
        uploads = Upload.objects.filter(uploadDate__lte=timezone.now())
        get = self.request.GET

        order_by = get.get('order_by')
        filter_slug = get.get('filter')
        tags = get.get('tags')

        order_by = '-uploadDate' if order_by is None else order_by

        filter_tag = Tag.objects.filter(slug=filter_slug).first()

        # Return None if there are no items with the specified tags
        if filter_slug is not None and filter_tag is None:
            self.total_num_uploads = 0
            return None

        elif filter_slug is not None and filter_tag is not None:
            tag_id = filter_tag.id
            uploads = uploads.filter(tags__id=tag_id).distinct()

        if (order_by == 'ratings'):
            uploads = sorted(uploads, key=lambda u: -u.avg_review())
        else:
            uploads =  uploads.order_by(order_by)

        # Filter based on tags
        if tags is not None:
            print("tags: ", tags)

        self.total_num_uploads = len(uploads)
        return self.get_uploads_in_range(uploads)


    def get_page_list(self):
        num_pages = math.ceil(self.total_num_uploads / self.uploads_per_page)
        page_list = ''
        for i in range(num_pages):
            page_list = page_list + str(i + 1)
        return page_list

    def get_context_data(self, **kwargs):
        c = super(generic.ListView, self).get_context_data(**kwargs)
        user = self.request.user

        if not user.is_anonymous:
            s7user = S7User.objects.filter(user=user)[:1]
            if s7user:
                c['s7user'] = s7user.get()

        c['search_form'] = SearchForm()
        c['num_pages'] = self.get_page_list()

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

