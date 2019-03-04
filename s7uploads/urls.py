from django.urls import path
from . import views

app_name = 's7uploads'

urlpatterns = [
	path('', views.IndexView.as_view(), name='index'),
	path('signup/', views.signup, name='signup'),
	path('login/', views.user_login, name='login'),
	path('logout/', views.logout_view, name='logout'),
	path('uploads/<int:pk>/', views.UploadView.as_view(), name='upload'),
	path('new_upload/', views.upload_file, name='new_upload'),
	path('uploads/<int:pk>/add_review', views.add_review, name='add_review'),
	path('reviews/', views.ReviewView.as_view(), name='reviews'),
	path('users/', views.UserListView.as_view(), name='users'),
]
