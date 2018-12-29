from django.contrib import admin
from .models import User, Upload, Screenshot, Review


admin.site.register(User)
admin.site.register(Upload)
admin.site.register(Screenshot)
admin.site.register(Review)
