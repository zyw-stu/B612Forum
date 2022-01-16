from django.test import TestCase
from django.contrib import admin
from .models import Comment

class BlogAdmin (admin.ModelAdmin):
    list_display=("title","created_time","modified_time","category","author","views",)
admin.site.register(Comment)

# Create your tests here.
