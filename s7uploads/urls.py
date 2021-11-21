from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path
from . import views

app_name = "s7uploads"

urlpatterns = [
    re_path(r"^$", views.IndexView.as_view(), name="index"),
    path("<int:page>/", views.IndexView.as_view(), name="index"),
    path("search_uploads/", views.search_uploads, name="search_uploads"),
    path("<int:page>/search_uploads/", views.search_uploads, name="search_uploads"),
    path("search_uploads/<str:params>", views.search_uploads, name="search_uploads"),
    path("signup/", views.signup, name="signup"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("uploads/<int:pk>/", views.UploadView.as_view(), name="upload"),
    path("edit/<int:pk>/", views.EditUploadView.as_view(), name="edit"),
    path("newversion/<int:pk>/", views.NewVersionView.as_view(), name="newversion"),
    path("delete/<int:pk>/", views.delete_upload, name="delete"),
    path("delete_review/<int:pk>/", views.delete_review, name="delete_review"),
    path("delete_ss/<int:pk>/", views.delete_screenshot, name="delete_ss"),
    path("new_upload/", views.upload_file, name="new_upload"),
    path("uploads/<int:pk>/add_review", views.add_review, name="add_review"),
    path("reviews/", views.ReviewView.as_view(), name="reviews"),
    path("users/", views.UserListView.as_view(), name="users"),
    path("about/", views.about_view, name="about"),
    path("community/", views.community_view, name="community"),
    path("download/<int:pk>", views.download_file, name="download"),
]
