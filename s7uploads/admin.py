from django.contrib import admin
from .models import S7User, Upload, Screenshot, Review

admin.site.register(S7User)
admin.site.register(Upload)
admin.site.register(Screenshot)
admin.site.register(Review)
