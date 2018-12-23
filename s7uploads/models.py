import datetime
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
		url = "/s7uploads/images/" + (Screenshot.objects.filter(upload=self)[0].url)
		return url

	def __str__(self):
		return self.title


class Screenshot(models.Model):
	url = models.CharField(max_length = 100)
	upload = models.ForeignKey(Upload, on_delete=models.CASCADE)
	def __str__(self):
		return self.url
