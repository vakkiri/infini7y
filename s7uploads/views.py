import math

from django.db.models import Count, Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.urls import path
from django.views import generic

from .models import Upload, UploadVersion, Review, S7User, Tag, Screenshot
from .forms import ReviewForm, SearchForm, SignUpForm, UploadFileForm, EditUploadForm, AddScreenshotForm

from .authorization import authorize_file_upload
from .filehandler import handle_uploaded_file, handle_uploaded_screenshot, handle_download_file, handle_edit_upload, valid_upload_ext, valid_screenshot_ext

from .urltools import strip_get_tags


def about_view(request):
    return render(request, 's7uploads/about.html')


def community_view(request):
    return render(request, 's7uploads/community.html')


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
    if not request.user.is_anonymous:
        if request.method == 'POST':
            form = ReviewForm(request.POST)

            if form.is_valid():
                review = form.save(commit=False)
                review.pubDate = timezone.now()
                review.upload = UploadVersion.objects.get(pk=pk)
                review.user = S7User.objects.get(pk=1)
                review.save()

                url = '/s7uploads/uploads/' + str(pk)
                return HttpResponseRedirect(url)

        else:
            form = ReviewForm()
            return render(request, 's7uploads/upload.html', {'upload': UploadVersion.objects.get(pk=pk), 'form': form})
    else:
        return redirect('s7uploads:signup')


def delete_upload(request, pk):
    user = request.user
    upload = UploadVersion.objects.get(pk=pk)

    if not user.is_anonymous and upload is not None and upload.user.user.id == user.id:
        upload.delete()
    else:
        print("Unauthorized attempt to delete upload.")

    return redirect('s7uploads:index')


def delete_screenshot(request, pk):
    user = request.user
    ss = Screenshot.objects.get(pk=pk)

    if not user.is_anonymous and ss is not None and ss.upload.user.user.id == user.id:
        ss.delete()
    else:
        print("Unauthorized attempt to delete upload.")

    # TODO: redirect to previously viewed upload
    return redirect('s7uploads:index')


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
    upload = UploadVersion.objects.get(pk=pk)
    upload.num_downloads += 1
    upload.save(update_fields=['num_downloads'])
    return handle_download_file(upload.url)


def upload_file(request):

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid() and authorize_file_upload(request) and valid_upload_ext(request.FILES['file'].name):
            # upload file
            upload = handle_uploaded_file(form, request.FILES['file'], request.user)

            # upload screenshots
            for s in request.FILES.getlist('screenshots'):
                if valid_screenshot_ext(s.name):
                    handle_uploaded_screenshot(form, s, upload)
                else:
                    # TODO: Let user know the extension was valid
                    print("Invalid image extension.")

            return redirect('s7uploads:index')
        # TODO: else tell the user to log in
    else:
        form = UploadFileForm()

    return render(request, 's7uploads/newupload.html', {'form': form})


class IndexView(generic.ListView):
    model = UploadVersion
    template_name = 's7uploads/index.html'
    context_object_name = 'latest_upload_list'
    total_num_uploads = 0
    uploads_per_page = 7


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
        uploads = UploadVersion.objects.filter(date_added__lte=timezone.now())
        get = self.request.GET

        order_by = get.get('order_by')
        filter_tag = get.get('filter')
        search_tag = get.get('tags')

        order_by = '-date_added' if order_by is None else order_by


        # filter based on selected filters
        if filter_tag is not None:
            filter_tag = Tag.objects.filter(slug=filter_tag).first()
            if filter_tag is not None:
                tag_id = filter_tag.id
                uploads = uploads.filter(tags__id=tag_id).distinct()
            else:
                self.total_num_uploads = 0
                return None

        if (order_by == 'ratings'):
            uploads = sorted(uploads, key=lambda u: -u.avg_review())
        else:
            uploads =  uploads.order_by(order_by)

        # Filter based on tags
        if search_tag is not None:
            print("tags: ", search_tag)
            search_user = S7User.objects.filter(user__username=search_tag).first()
            search_tag = Tag.objects.filter(slug=search_tag).first()

            tag_matches = None
            user_matches = None

            if search_tag is not None:
                tag_id = search_tag.id
                tag_matches = uploads.filter(tags__id=tag_id).distinct()
            if search_user is not None:
                user_id = search_user.id
                if order_by == 'ratings':
                    user_matches = [upload for upload in uploads if upload.user.id == user_id]
                else:
                    user_matches = uploads.filter(user__id=user_id).distinct()

            if tag_matches is not None and user_matches is not None:
                uploads = tag_matches | user_matches
            elif tag_matches is not None:
                uploads = tag_matches
            elif user_matches is not None:
                uploads = user_matches
            else:
                uploads = []

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


class EditUploadView(generic.DetailView):
    model = Upload
    template_name = 's7uploads/editupload.html'

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            # TODO: redirect to forbidden page instead of index
            if not self.request.user.is_authenticated or self.object.user.user.id != self.request.user.id:
                return redirect('s7uploads:index')
        except:
            return redirect('s7uploads:index')

        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


    def handle_edit_form(self, request):
        form = EditUploadForm(request.POST, request.FILES)
        if form.is_valid():
            handle_edit_upload(form, self.get_object())
            return redirect('s7uploads:upload', pk=self.get_object().id)
        else:
            # TODO: Give some kind of notification of which fields were wrong, redirect to edit page
            return redirect('s7uploads:index')


    def handle_ss_form(self, request):
        form = AddScreenshotForm(request.POST, request.FILES)
        if form.is_valid():

            for s in request.FILES.getlist('screenshots'):
                if valid_screenshot_ext(s.name):
                    handle_uploaded_screenshot(form, s, self.get_object())
                else:
                    # TODO: Let user know the extension was valid
                    print("Invalid image extension.")

            return redirect('s7uploads:upload', pk=self.get_object().id)
        else:
            # TODO: Give some kind of notification of which fields were wrong, redirect to edit page
            return redirect('s7uploads:index')


    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.id == self.get_object().user.user.id:
            print(request.POST)
            if 'submit-ss' in request.POST:
                return self.handle_ss_form(request)
            elif 'submit-edit' in request.POST:
                return self.handle_edit_form(request)
        else:
            return redirect('s7uploads:index')


    def get_queryset(self):
        return UploadVersion.objects.filter(date_added__lte=timezone.now())

    def get_context_data(self, **kwargs):
        c = super(generic.DetailView, self).get_context_data(**kwargs)
        user = self.request.user

        if not user.is_anonymous:
            s7user = S7User.objects.filter(user=user)[:1]
            if s7user:
                c['s7user'] = s7user.get()

        # set initial values of the form to the object values
        initials = {}
        initials['title'] = self.object.title
        initials['description'] = self.object.description
        initials['versionNotes'] = self.object.versionNotes
        initials['versionNumber'] = self.object.versionNumber
       
        # TODO: populate initials with existing tags

        form = EditUploadForm(initial=initials)
        c['form'] = form
        c['screenshotform'] = AddScreenshotForm()
        return c

class UploadView(generic.DetailView):
    model = Upload
    template_name = 's7uploads/upload.html'

    def get_queryset(self):
        return UploadVersion.objects.filter(date_added__lte=timezone.now())

    def get_context_data(self, **kwargs):
        c = super(generic.DetailView, self).get_context_data(**kwargs)
        user = self.request.user
        if not user.is_anonymous:
            s7user = S7User.objects.filter(user=user)[:1]
            if s7user:
                c['s7user'] = s7user.get()

        return c

