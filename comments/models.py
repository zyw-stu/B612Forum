from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import signals
from django.urls import reverse_lazy

from blog.models import Notice


class Comment(models.Model):
    name = models.CharField(max_length=32)
    email = models.EmailField(max_length=60)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT) # 作者
    text = models.TextField()
    created_time = models.DateTimeField(auto_now=True) # 创建时间
    updated_time= models.DateTimeField(auto_now_add=True) # 更新时间
    blog = models.ForeignKey('blog.Blog',on_delete=models.CASCADE,)
    comment_parent = models.ForeignKey('self', blank=True, null=True, related_name='childcomment', on_delete=models.PROTECT) # 嵌套评论

    class Meta:
        db_table = 'comment'
        ordering = ['created_time']
        verbose_name_plural = u'评论'

    def __str__(self):
        return self.text[:20]

    def description(self):
        return u'%s 回复了您的帖子(%s) R:《%s》' % (self.name, self.blog, self.text)

    def get_absolute_url(self):
        return reverse_lazy('blog:detail', kwargs={"pk": self.blog.pk})

def comment_save(sender, instance, signal, *args, **kwargs):
    entity = instance
    if str(entity.created_time)[:19] == str(entity.updated_time)[:19]:
        if entity.author != entity.blog.author:  # 作者的回复不给作者通知
            event = Notice(
                sender=entity.author,
                receiver=entity.blog.author,
                event=entity,
                type=0)
            event.save()
        if entity.comment_parent is not None:  # 回复评论给要评论的人通知
            if entity.author.id != entity.comment_parent.author.id:  # 自己给自己写评论不通知
                event = Notice(
                    sender=entity.author,
                    receiver=entity.comment_parent.author,
                    event=entity,
                    type=0)
                event.save()

# 消息响应函数注册
signals.post_save.connect(comment_save, sender=Comment)

