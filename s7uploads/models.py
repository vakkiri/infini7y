import datetime
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class User(models.Model):
	username = models.CharField(max_length = 50)

	def num_uploads(self):
		return Upload.objects.filter(user=self).count()

	def num_reviews(self):
		return Review.objects.filter(user=self).count()

	def __str__(self):
		return self.username

class Upload(models.Model):
	url = models.CharField(max_length = 100)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	title = models.CharField(max_length = 50)
	description = models.TextField(verbose_name="Upload Description")
	versionNotes = models.TextField(verbose_name="Version Notes")
	uploadDate = models.DateTimeField('date published')
	versionNumber = models.DecimalField(max_digits=5, decimal_places = 1)

	def indexScreenshot(self):
		return Screenshot.objects.filter(upload=self)[0].url
	def __str__(self):
		return self.title


class Screenshot(models.Model):
	url = models.CharField(max_length = 100)
	upload = models.ForeignKey(Upload, on_delete=models.CASCADE)
	def __str__(self):
		return self.url

class Review(models.Model):
	title = models.CharField(max_length = 50)
	text = models.TextField(max_length = 2048, verbose_name="Review Text")
	upload = models.ForeignKey(Upload, on_delete=models.CASCADE)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	pubDate = models.DateTimeField('date published')
	rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])
	def __str__(self):
		return self.user.username + self.upload.title
