from django.urls import path

from . import views

app_name = 's7uploads'

urlpatterns = [
	path('', views.IndexView.as_view(), name='index'),
	path('uploads/<int:pk>/', views.UploadView.as_view(), name='upload'),
	path('uploads/<int:pk>/add_review', views.add_review),
	path('reviews/', views.ReviewView.as_view(), name='reviews'),
	path('users/', views.UserListView.as_view(), name='users'),
]
