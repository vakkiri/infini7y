from django.urls import path

from . import views

app_name = 's7uploads'

urlpatterns = [
	path('', views.IndexView.as_view(), name='index'),
	path('<int:pk>/', views.UploadView.as_view(), name='upload'),
]
