from django.contrib import admin
from .models import Blog,Category,Tag,loguser,Notice,Application,Message
from comments.models import Comment

class BlogAdmin (admin.ModelAdmin):
    list_display=("title","created_time","modified_time","category","author","views",)
admin.site.register(loguser)
admin.site.register(Blog,BlogAdmin)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Comment)
admin.site.register(Message)
admin.site.register(Application)
admin.site.register(Notice)




