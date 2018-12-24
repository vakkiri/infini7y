import datetime
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render
from django.db import models

class User(models.Model):
	username = models.CharField(max_length = 50)
	def __str__(self):
		return self.username

class Upload(models.Model):
	url = models.CharField(max_length = 100)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	title = models.CharField(max_length = 50)
	description = models.CharField(max_length = 2048)
	versionNotes = models.CharField(max_length = 512)
	uploadDate = models.DateTimeField('date published')
	versionNumber = models.DecimalField(max_digits=5, decimal_places = 1)
	#ratings..

	def indexScreenshot(self):
		screenshot = get_object_or_404(Screenshot, upload=self);
		try:
			url = "/s7uploads/images/" + screenshot.url
		except (KeyError, Screenshot.DoesNotExist):
			#ummm just don't render anything? how 2 do
			return url
		else:
			return url

	def __str__(self):
		return self.title


class Screenshot(models.Model):
	url = models.CharField(max_length = 100)
	upload = models.ForeignKey(Upload, on_delete=models.CASCADE)
	def __str__(self):
		return self.url
