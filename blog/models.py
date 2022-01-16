import datetime
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import signals
from django.urls import reverse, reverse_lazy
from django.utils.html import strip_tags
from ckeditor_uploader.fields import RichTextUploadingField
from django.contrib.auth.models import User

#用户信息，继承AbstractUser，可以生成系统用户

class loguser(AbstractUser):
    nikename=models.CharField(max_length=32,verbose_name="昵称",blank=True)
    telephone = models.CharField(max_length=11, null=True, unique=True)
    head_img = models.ImageField(upload_to='headimage', blank=True, null=True, verbose_name='头像')  # 头像
    levels = models.PositiveIntegerField(default=0, verbose_name=u'积分')  #新添加
    friends = models.ManyToManyField('self', blank=True, null=True, related_name='friends')
    def __str__(self):
        return self.username
    class Meta:
        verbose_name = "用户信息表"
        verbose_name_plural = verbose_name
        ordering = ['-date_joined']

    def checkfriend(self, username):  # 查看好友
        if username in self.friends.all():
            return True
        else:
            return False


class UserProfile(models.Model):
    user = models.OneToOneField(loguser, on_delete=models.CASCADE, related_name='profile')
    nikename = models.CharField(max_length=32,verbose_name="昵称",blank=True)
    telephone = models.CharField(max_length=11, null=True, unique=True)
    #　head_img = models.ImageField(upload_to='headimage', blank=True, null=True, verbose_name='头像')  # 头像
    levels = models.PositiveIntegerField(default=0, verbose_name=u'积分')  #新添加
    friends = models.ManyToManyField('self', blank=True, null=True, related_name='friends')
    mod_date = models.DateTimeField('Last modified', auto_now=True)
    class Meta:
        verbose_name = 'User Profile'
    def __str__(self):
        return "{}".format(self.user.__str__())

class Category(models.Model): #一定要继承 models.Model 类！
    name = models.CharField(max_length=32,verbose_name='分类名')#CharField 的 max_length 参数指定其最大长度
    des=models.CharField(max_length=100,verbose_name='备注',null=True)
    post_number = models.IntegerField(default=0)  # 主题数
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='category_manager', on_delete=models.PROTECT)  # 版主
    parent = models.ForeignKey('self', blank=True, null=True, related_name='childCategory', on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    class Meta:
        # ordering = ['-post_number']
        verbose_name='分类'
        verbose_name_plural='分类'

    def get_absolute_url(self):
        return reverse_lazy('column_detail', kwargs={"column_pk": self.pk})


class Tag(models.Model):
    name = models.CharField(max_length=32,verbose_name='标签名')
    des = models.CharField(max_length=100, verbose_name='备注', null=True)
    def __str__(self):
        return self.name
    class Meta:
        verbose_name='标签'
        verbose_name_plural='标签'

class Blog(models.Model):
    title = models.CharField(max_length=70,verbose_name='文章标题')# 文章标题
    body = RichTextUploadingField(verbose_name='文本内容')# 文章正文，我们使用了 RichTextUploadingField
    created_time = models.DateTimeField(verbose_name='创建时间',default=datetime.datetime.now)# 文章的创建时间,存储时间的字段用 DateTimeField 类型。
    modified_time = models.DateTimeField(verbose_name='修改时间',default=datetime.datetime.now)# 文章的最后一次修改时间，存储时间的字段用 DateTimeField 类型。
    excerpt = models.CharField(max_length=200, blank=True,verbose_name='文章摘要') # 指定blank=True 参数值后就可以允许空值了。
    category = models.ForeignKey(Category,on_delete=models.CASCADE,verbose_name='分类')
    tags = models.ManyToManyField(Tag, blank=True,verbose_name='标签')
    author = models.ForeignKey(loguser,on_delete=models.CASCADE,verbose_name='作者',related_name='b_author')
    views = models.IntegerField(default=0,verbose_name='查看次数')
    response_times = models.IntegerField(default=0)  # 回复次数
    last_response = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT,related_name='c_author',blank=True)  # 最后回复者

    def get_absolute_url(self):
        return reverse('blog:detail', kwargs={'pk': self.pk})
    def description(self):
        return u'%s 发表了主题《%s》' % (self.author, self.title)
    def increase_views(self):
        self.views += 1
        self.save(update_fields=['views'])

    def save(self, *args, **kwargs):
        if not self.excerpt:   # 如果没有填写摘要
            self.excerpt = strip_tags(self.body)[:118]
            super(Blog, self).save(*args, **kwargs)  # 调用父类的 save 方法将数据保存到数据库中
        else:
            super(Blog, self).save(*args, **kwargs)  # 调用父类的 save 方法将数据保存到数据库中

    def __str__(self):
        return self.title

    class Meta:
        ordering=['-created_time']
        verbose_name = '文档管理表'
        verbose_name_plural = '文档管理表'


class Message(models.Model):  # 好友消息
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='message_sender', on_delete=models.PROTECT)  # 发送者
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='message_receiver', on_delete=models.PROTECT)  # 接收者
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def description(self):
        return u'%s 给你发送了消息《%s》' % (self.sender, self.content)

    class Meta:
        db_table = 'message'
        verbose_name = '好友消息'
        verbose_name_plural = u'好友消息'



class Application(models.Model):  # 好友申请
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='appli_sender', on_delete=models.PROTECT)  # 发送者
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='appli_receiver', on_delete=models.PROTECT)  # 接收者
    status = models.IntegerField(default=0)  # 申请状态 0:未查看 1:同意 2:不同意
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def description(self):
        return u'%s 申请加好友' % self.sender

    class Meta:
        managed = True
        db_table = 'application'
        verbose_name = '好友申请'
        verbose_name_plural = '好友申请'


class Notice(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='notice_sender', on_delete=models.PROTECT)  # 发送者
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='notice_receiver', on_delete=models.PROTECT)  # 接收者
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.PositiveIntegerField()
    event = GenericForeignKey('content_type', 'object_id')

    status = models.BooleanField(default=False)  # 是否阅读
    type = models.IntegerField()  # 通知类型 0:评论 1:好友消息 2:好友申请
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'notice'
        ordering = ['-created_at']
        verbose_name = '通知'
        verbose_name_plural = '通知'

    def __str__(self):
        return u"%s的事件: %s" % (self.sender, self.description())

    def description(self):
        if self.event:
            return self.event.description()
        return "No Event"

    def reading(self):
        if not status:
            status = True


def post_save(sender, instance, signal, *args, **kwargs):
    entity = instance
    if str(entity.created_time)[:19] == str(entity.modified_time)[:19]:  # 第一次发帖操作，编辑不操作
        category = entity.category
        category.post_number += 1
        category.save()

def post_delete(sender, instance, signal, *args, **kwargs):  # 删帖触发板块帖子数减1
    entity = instance
    category = entity.category
    category.post_number -= 1
    category.save()

def application_save(sender, instance, signal, *args, **kwargs):
    entity = instance
    if str(entity.created_at)[:19] == str(entity.updated_at)[:19]:
        event = Notice(
            sender=entity.sender,
            receiver=entity.receiver,
            event=entity,
            type=1)
        event.save()


def message_save(sender, instance, signal, *args, **kwargs):
    entity = instance
    if str(entity.created_at)[:19] == str(entity.updated_at)[:19]:
        event = Notice(
            sender=entity.sender,
            receiver=entity.receiver,
            event=entity,
            type=2)
        event.save()

# 消息响应函数注册
signals.post_save.connect(application_save, sender=Message)
signals.post_save.connect(message_save, sender=Application)
signals.post_save.connect(post_save, sender=Blog)
signals.post_delete.connect(post_delete, sender=Blog)



