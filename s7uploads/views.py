import math

from django.db.models import Count, Q, Sum
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.urls import path
from django.views import generic

import operator

from .models import *
from .forms import *

from .authorization import authorize_file_upload
from .filehandler import *


def about_view(request):
    return render(request, "s7uploads/about.html")


def community_view(request):
    if request.method == "POST":
        return render(request, "s7uploads/community.html")
    else:
        searchform = SearchForm()
        return render(request, "s7uploads/community.html", {"search_form": searchform})


def search_uploads(request, params="", page=0):
    if request.method == "POST":
        form = SearchForm(request.POST)

        if form.is_valid():
            search_tags = form.cleaned_data.get("search_line")
            sort_by = request.POST["searchorder"]
            filter_by = request.POST["searchcategory"]

            tag_line = "tags=" + search_tags
            sort_line = "sort=" + sort_by
            filter_line = "filter=" + filter_by

            get_line = "?" + "&".join([tag_line, sort_line, filter_line])
            url = "/s7uploads/" + get_line
            return HttpResponseRedirect(url)

    else:
        form = SearchForm()
        url = "/s7uploads/" + params
        return HttpResponseRedirect(url)


def add_review(request, pk):
    if not request.user.is_anonymous:
        if request.method == "POST":
            form = ReviewForm(request.POST)

            if form.is_valid():
                review = form.save(commit=False)
                review.pubDate = timezone.now()
                review.upload = UploadVersion.objects.get(pk=pk)
                review.user = S7User.objects.get(user=request.user)
                review.save()
                review.upload.update_ranking()

                url = "/s7uploads/uploads/" + str(pk)
                return HttpResponseRedirect(url)

        else:
            form = ReviewForm()
            searchform = SearchForm(request.POST)
            return render(
                request,
                "s7uploads/upload.html",
                {
                    "upload": UploadVersion.objects.get(pk=pk),
                    "form": form,
                    "search_form": searchform,
                },
            )
    else:
        return redirect("s7uploads:signup")


def delete_upload(request, pk):
    user = request.user
    upload = UploadVersion.objects.get(pk=pk)

    if (
        not user.is_anonymous
        and upload is not None
        and upload.upload_id.user.user.id == user.id
    ):
        upload.delete()
    else:
        print("Unauthorized attempt to delete upload.")

    return redirect("s7uploads:index")


def delete_screenshot(request, pk):
    user = request.user
    ss = Screenshot.objects.get(pk=pk)

    if not user.is_anonymous and ss is not None and ss.upload.user.user.id == user.id:
        ss.delete()
    else:
        print("Unauthorized attempt to delete upload.")

    # TODO: redirect to previously viewed upload
    return redirect("s7uploads:index")


def delete_review(request, pk):
    user = request.user
    review = Review.objects.get(pk=pk)
    upload_id = review.upload.id

    if not user.is_anonymous and review is not None and review.user.user.id == user.id:
        review.delete()
    else:
        print("Unauthorized attempt to delete review")

    # TODO: just refresh instead?
    return redirect("s7uploads:upload", upload_id)


def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("s7uploads:index")
        else:
            form = AuthenticationForm()
            return render(
                request, "s7uploads/login.html", {"form": form, "invalid": True}
            )
    else:
        form = AuthenticationForm()

    return render(request, "s7uploads/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("s7uploads:index")


def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect("s7uploads:index")
    else:
        form = SignUpForm()

    return render(request, "s7uploads/signup.html", {"form": form})


def download_file(request, pk):
    version = UploadVersion.objects.get(pk=pk)
    upload = version.upload_id
    upload.total_downloads += 1
    version.num_downloads += 1
    version.save(update_fields=["num_downloads"])
    upload.save(update_fields=["total_downloads"])
    return handle_download_file(version.file_id.url)


def upload_file(request):

    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)

        if (
            form.is_valid()
            and authorize_file_upload(request)
            and valid_upload_ext(request.FILES["file"].name)
        ):
            # upload file
            upload = handle_uploaded_file(form, request.FILES["file"], request.user)

            # upload screenshots
            for s in request.FILES.getlist("screenshots"):
                if valid_screenshot_ext(s.name):
                    handle_uploaded_screenshot(form, s, upload)
                else:
                    # TODO: Let user know the extension was valid
                    print("Invalid image extension.")

            return redirect("s7uploads:index")
        # TODO: else tell the user to log in
    else:
        form = UploadFileForm()

    return render(request, "s7uploads/newupload.html", {"form": form})


class IndexView(generic.ListView):
    model = UploadVersion
    template_name = "s7uploads/index.html"
    context_object_name = "latest_upload_list"
    total_num_uploads = 0
    uploads_per_page = 7

    # select option -> filter param
    order_dict = {
        "newest": "-date_added",
        "oldest": "date_added",
        "bestrated": "-avg_rating",
        "mostrated": "-num_reviews",
        "mostdownloads": "-upload_id__total_downloads",
    }

    def get_uploads_in_range(self, uploads):
        # the -1 is due to displaying start page as 1 instead of 0 in browser
        start_page = self.kwargs["page"] - 1 if "page" in self.kwargs else 0
        start_index = start_page * self.uploads_per_page
        end_index = start_index + self.uploads_per_page
        return uploads[start_index:end_index]

    def get_queryset(self):
        get = self.request.GET

        uploads = Upload.objects.none()
        tagged_uploads = Upload.objects.none()
        named_uploads = Upload.objects.none()
        tagged_versions = UploadVersion.objects.none()
        named_versions = UploadVersion.objects.none()

        # default ordering if no order is supplied
        order_by = IndexView.order_dict["newest"]

        if len(get) == 0:
            uploads = UploadVersion.objects.filter(date_added__lte=timezone.now())
        else:
            order_by = get.get("sort")
            filter_by = get.get("filter")
            search_tag = get.get("tags")

            if order_by in IndexView.order_dict:
                order_by = IndexView.order_dict[order_by]

            if filter_by != None and filter_by in (
                "maps",
                "scenarios",
                "plugins",
                "scripts",
                "utilities",
                "physics",
            ):
                try:
                    tag_obj = Tag.objects.get(slug=filter_by)
                except:
                    all_uploads = Upload.objects.none()
            else:
                all_uploads = Upload.objects.all()

            if len(search_tag) > 0:
                tags = [tag.strip() for tag in search_tag.split()]

                for tag in tags:
                    # get uploads with matching tags
                    try:
                        tag_obj = Tag.objects.get(slug=tag)
                        if tag_obj:
                            tagged_uploads = tagged_uploads | all_uploads.filter(
                                tags=tag_obj
                            )
                    except:
                        continue

                tagged_versions = UploadVersion.objects.filter(
                    upload_id__in=tagged_uploads
                )

                # get uploads with matching name
                for tag in tags:
                    if len(tag) >= 3:
                        named_uploads = named_uploads | all_uploads.filter(
                            title__contains=tag
                        )

                named_versions = UploadVersion.objects.filter(
                    upload_id__in=named_uploads
                )

                uploads = (tagged_versions | named_versions).distinct()
            else:
                uploads = UploadVersion.objects.filter(upload_id__in=all_uploads)

        self.total_num_uploads = len(uploads)

        return self.get_uploads_in_range(
            uploads.annotate(num_reviews=Count("review")).order_by(order_by)
        )

    def get_page_list(self):
        num_pages = math.ceil(self.total_num_uploads / self.uploads_per_page)
        page_list = ""
        for i in range(num_pages):
            page_list = page_list + str(i + 1)
        return page_list

    def get_context_data(self, **kwargs):
        c = super(generic.ListView, self).get_context_data(**kwargs)
        user = self.request.user

        if not user.is_anonymous:
            s7user = S7User.objects.filter(user=user)[:1]
            if s7user:
                c["s7user"] = s7user.get()

        c["search_form"] = SearchForm()
        c["num_pages"] = self.get_page_list()

        return c


class ReviewView(generic.ListView):
    model = Review
    template_name = "s7uploads/reviews.html"
    context_object_name = "latest_review_list"

    def get_queryset(self):
        numReviews = 25
        return Review.objects.filter(pubDate__lte=timezone.now()).order_by("-pubDate")[
            :numReviews
        ]

    def get_context_data(self, **kwargs):
        c = super(generic.ListView, self).get_context_data(**kwargs)
        user = self.request.user
        if not user.is_anonymous:
            s7user = S7User.objects.filter(user=user)[:1]
            if s7user:
                c["s7user"] = s7user.get()
        c["search_form"] = SearchForm()
        return c


class UserListView(generic.ListView):
    model = S7User
    template_name = "s7uploads/users.html"
    context_object_name = "user_list"

    def get_queryset(self):
        return S7User.objects.all()

    def get_context_data(self, **kwargs):
        c = super(generic.ListView, self).get_context_data(**kwargs)
        user = self.request.user

        if not user.is_anonymous:
            s7user = S7User.objects.filter(user=user)[:1]
            if s7user:
                c["s7user"] = s7user.get()

        c["search_form"] = SearchForm()

        return c


class EditUploadView(generic.DetailView):
    model = UploadVersion
    template_name = "s7uploads/editupload.html"

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            # TODO: redirect to forbidden page instead of index
            if (
                not self.request.user.is_authenticated
                or self.object.upload_id.user.user.id != self.request.user.id
            ):
                return redirect("s7uploads:index")
        except Exception as e:
            print("Exception editing upload: ", e)
            return redirect("s7uploads:index")

        context = self.get_context_data(upload=self.object)
        return self.render_to_response(context)

    def handle_edit_form(self, request):
        form = EditUploadForm(request.POST, request.FILES)
        if form.is_valid():
            handle_edit_upload(form, self.get_object())
            return redirect("s7uploads:upload", pk=self.get_object().id)
        else:
            # TODO: Give some kind of notification of which fields were wrong, redirect to edit page
            print("Error: Invalid edit form.")
            return redirect("s7uploads:index")

    def handle_ss_form(self, request):
        form = AddScreenshotForm(request.POST, request.FILES)
        if form.is_valid():

            for s in request.FILES.getlist("screenshots"):
                if valid_screenshot_ext(s.name):
                    handle_uploaded_screenshot(form, s, self.get_object())
                else:
                    # TODO: Let user know the extension was valid
                    print("Invalid image extension.")

            return redirect("s7uploads:upload", pk=self.get_object().id)
        else:
            # TODO: Give some kind of notification of which fields were wrong, redirect to edit page
            return redirect("s7uploads:index")

    def post(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and request.user.id == self.get_object().upload_id.user.user.id
        ):
            if "submit-ss" in request.POST:
                return self.handle_ss_form(request)
            elif "submit-edit" in request.POST:
                return self.handle_edit_form(request)
        else:
            return redirect("s7uploads:index")

    def get_queryset(self):
        return UploadVersion.objects.filter(date_added__lte=timezone.now())

    def get_context_data(self, **kwargs):
        c = super(generic.DetailView, self).get_context_data(**kwargs)
        user = self.request.user

        if not user.is_anonymous:
            s7user = S7User.objects.filter(user=user)[:1]
            if s7user:
                c["s7user"] = s7user.get()

        # set initial values of the form to the object values
        initials = {}
        initials["title"] = self.object.upload_id.title
        initials["description"] = self.object.upload_id.description
        initials["versionNotes"] = self.object.version_notes
        initials["versionNumber"] = self.object.version_name
        tags = Tag.objects.filter(uploads__exact=self.object.upload_id)
        tags = " ".join(["#" + tag.name for tag in tags])
        initials["tagline"] = tags
        form = EditUploadForm(initial=initials)
        c["form"] = form
        c["screenshotform"] = AddScreenshotForm()
        c["search_form"] = SearchForm()
        return c


class NewVersionView(generic.DetailView):
    model = UploadVersion
    template_name = "s7uploads/newversion.html"

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            # TODO: redirect to forbidden page instead of index
            if (
                not self.request.user.is_authenticated
                or self.object.upload_id.user.user.id != self.request.user.id
            ):
                return redirect("s7uploads:index")
        except Exception as e:
            print("Exception editing upload: ", e)
            return redirect("s7uploads:index")

        c = self.get_context_data(upload=self.object)
        c["search_form"] = SearchForm()
        return self.render_to_response(c)

    def handle_edit_form(self, request):
        form = NewVersionForm(request.POST, request.FILES)
        if form.is_valid():
            handle_version_upload(form, request.FILES["file"], self.get_object())
            return redirect("s7uploads:upload", pk=self.get_object().id)
        else:
            # TODO: Give some kind of notification of which fields were wrong, redirect to edit page
            print("Error: Invalid edit form.")
            return redirect("s7uploads:index")

    def handle_ss_form(self, request):
        form = AddScreenshotForm(request.POST, request.FILES)
        if form.is_valid():

            for s in request.FILES.getlist("screenshots"):
                if valid_screenshot_ext(s.name):
                    handle_uploaded_screenshot(form, s, self.get_object())
                else:
                    # TODO: Let user know the extension was valid
                    print("Invalid image extension.")

            return redirect("s7uploads:upload", pk=self.get_object().id)
        else:
            # TODO: Give some kind of notification of which fields were wrong, redirect to edit page
            return redirect("s7uploads:index")

    def post(self, request, *args, **kwargs):
        if (
            request.user.is_authenticated
            and request.user.id == self.get_object().upload_id.user.user.id
        ):
            if "submit-ss" in request.POST:
                return self.handle_ss_form(request)
            elif "submit-edit" in request.POST:
                return self.handle_edit_form(request)
        else:
            return redirect("s7uploads:index")

    def get_queryset(self):
        return UploadVersion.objects.filter(date_added__lte=timezone.now())

    def get_context_data(self, **kwargs):
        c = super(generic.DetailView, self).get_context_data(**kwargs)
        user = self.request.user

        if not user.is_anonymous:
            s7user = S7User.objects.filter(user=user)[:1]
            if s7user:
                c["s7user"] = s7user.get()

        # set initial values of the form to the object values
        initials = {}
        initials["description"] = self.object.upload_id.description
        tags = Tag.objects.filter(uploads__exact=self.object.upload_id)
        tags = " ".join(["#" + tag.name for tag in tags])
        initials["tagline"] = tags
        form = NewVersionForm(initial=initials)
        c["form"] = form
        c["search_form"] = SearchForm()
        c["screenshotform"] = AddScreenshotForm()
        return c


class UploadView(generic.DetailView):
    model = UploadVersion
    template_name = "s7uploads/upload.html"
    context_object_name = "upload"

    def get_queryset(self):
        return UploadVersion.objects.filter(date_added__lte=timezone.now())

    def get_context_data(self, **kwargs):
        c = super(generic.DetailView, self).get_context_data(**kwargs)
        user = self.request.user
        if not user.is_anonymous:
            s7user = S7User.objects.filter(user=user)[:1]
            if s7user:
                c["s7user"] = s7user.get()

        c["search_form"] = SearchForm()

        return c
