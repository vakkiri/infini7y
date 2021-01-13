import datetime
from django.db.models import Count, Sum, Avg
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render
from django.db import models
from django.db.models.signals import post_save
from django.core.validators import MinValueValidator, MaxValueValidator
from django.dispatch import receiver
from django.utils.text import slugify


class S7User(models.Model):
    user = models.OneToOneField(User, unique=True, on_delete=models.CASCADE)

    def num_uploads(self):
        return Upload.objects.filter(user=self).count()

    def num_reviews(self):
        return Review.objects.filter(user=self).count()

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def update_user(sender, instance, created, **kwargs):
    if created:
        S7User.objects.create(user=instance)


class Upload(models.Model):
    user = models.ForeignKey(S7User, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    description = models.TextField(verbose_name="Upload Description")
    total_downloads = models.IntegerField()

    def indexScreenshot(self):
        return Screenshot.objects.filter(upload=self)[0].url

    def avg_review(self):
        reviews = Review.objects.filter(upload=self)
        num_reviews = reviews.count()
        if num_reviews == 0:
            return 0
        else:
            return reviews.aggregate(Sum('rating'))['rating__sum'] / reviews.count()

    def num_reviews(self):
        return review_set.count()

    def __str__(self):
        return self.title


class File(models.Model):
    url = models.CharField(max_length=100)


class UploadVersion(models.Model):
    upload_id = models.ForeignKey(Upload, on_delete=models.CASCADE)
    file_id = models.ForeignKey(File, on_delete=models.CASCADE)
    date_added = models.DateTimeField()
    version_notes = models.TextField()
    version_name = models.CharField(max_length=10)
    num_downloads = models.IntegerField()
    ranking = models.IntegerField()
    avg_rating = models.DecimalField(decimal_places=2, max_digits=10)

    def total_stars(self):
        reviews = Review.objects.filter(upload=self)
        num_reviews = reviews.count()
        if num_reviews == 0:
            return 0
        else:
            return reviews.aggregate(Sum('rating'))['rating__sum']

    def update_ranking(self):
        reviews = Review.objects.filter(upload=self)
        _avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']
        new_ranking = 0
        #TODO:... new smart ranking
        self.ranking = new_ranking
        self.avg_rating = _avg_rating
        self.save()


class Tag(models.Model):
    name = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    uploads = models.ManyToManyField(Upload, related_name='tags')

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Tag, self).save(*args, **kwargs)


class Screenshot(models.Model):
    url = models.CharField(max_length = 100)
    upload = models.ForeignKey(Upload, on_delete=models.CASCADE)

    def __str__(self):
        return self.url


class Review(models.Model):
    title = models.CharField(max_length = 50)
    text = models.TextField(max_length = 2048, verbose_name="Review Text")
    upload = models.ForeignKey(UploadVersion, on_delete=models.CASCADE)
    user = models.ForeignKey(S7User, on_delete=models.CASCADE)
    pubDate = models.DateTimeField('date published')
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(5)])

    def __str__(self):
        return self.user.user.username + self.upload.title


