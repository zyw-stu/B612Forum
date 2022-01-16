import os
import time
import logging
from io import BytesIO
from django.http.response import Http404, HttpResponseRedirect, JsonResponse

from django.shortcuts import render,redirect,HttpResponse,get_object_or_404
from django.template import RequestContext
from django.views.decorators.http import require_http_methods

from . import models
from comments.forms import CommentForm
from django.views.generic import ListView,DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.contrib.auth.models import auth
from django.urls import reverse_lazy, reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.utils.timezone import now, timedelta
from django.core.cache import cache

from django.db.models import Q
from blog.models import Application, Category, Notice, loguser, Tag, Message, Notice, Blog, UserProfile
from comments.models import Comment
from .forms import PostForm, MessageForm, ProfileForm, ChangepwdForm
from .validate import create_validate_code

PAGE_NUM = 50
logger = logging.getLogger(__name__)

def get_online_ips_count():
    """统计当前在线人数（5分钟内，中间件实现于middle.py）"""
    online_ips = cache.get("online_ips", [])
    if online_ips:
        online_ips = cache.get_many(online_ips).keys()
        return len(online_ips)
    return 0

def get_forum_info():
    """获取 论坛信息，贴子数，用户数，昨日发帖数，今日发帖数"""
    # 请使用缓存
    oneday = timedelta(days=1)
    today = now().date()
    lastday = today - oneday
    todayend = today + oneday
    post_number = Blog.objects.count()
    account_number = loguser.objects.count()

    lastday_post_number = cache.get('lastday_post_number', None)
    today_post_number = cache.get('today_post_number', None)

    if lastday_post_number is None:
        lastday_post_number = Blog.objects.filter(
            created_time__range=[lastday, today]).count()
        cache.set('lastday_post_number', lastday_post_number, 60 * 60)

    if today_post_number is None:
        today_post_number = Blog.objects.filter(
            created_time__range=[today, todayend]).count()
        cache.set('today_post_number', today_post_number, 60 * 60)

    info = {
        "post_number": post_number,
        "account_number": account_number,
        "lastday_post_number": lastday_post_number,
        "today_post_number": today_post_number
    }
    return info

class BaseMixin(object):
    def get_context_data(self, *args, **kwargs):
        context = super(BaseMixin, self).get_context_data(**kwargs)
        try:
            context['last_comments'] = Comment.objects.all().order_by( # 最新评论
                "-created_time")[0:10]
            if self.request.user.is_authenticated:
                k = Notice.objects.filter(
                    receiver=self.request.user, status=False).count()
                context['message_number'] = k

        except Exception as e:
            logger.error(u'[BaseMixin]加载基本信息出错', e)
        return context

class indexview(BaseMixin,ListView): # Home分页
    model = models.Blog
    queryset = Blog.objects.all()
    template_name = 'blog/index.html'
    context_object_name = 'blog_list'
    paginate_by = 5

    def get_context_data(self, **kwargs):
        # 首先获得父类生成的传递给模板的字典。
        context = super().get_context_data(**kwargs)
        kwargs['foruminfo'] = get_forum_info()
        kwargs['online_ips_count'] = get_online_ips_count()
        kwargs['hot_posts'] = self.queryset.order_by("-response_times")[0:10]

        paginator = context.get('paginator')
        pageobj = context.get('page_obj')
        is_paginated = context.get('is_paginated')
        #设置每页显示的页码标签数
        show_pagenumber=7
        # 调用自定义 get_page_data 方法获得显示分页导航条需要的数据
        page_data = self.get_page_data(is_paginated, paginator, pageobj, show_pagenumber)
        # 将page_data变量更新到 context 中，注意 page_data 是一个字典。
        context.update(page_data)
        context['tabname'] = 'firsttab'
        # 将更新后的 context 返回，以便 ListView 使用这个字典中的模板变量去渲染模板。
        # 注意此时 context 字典中已有了显示分页导航条所需的数据。
        return super(indexview, self).get_context_data(**kwargs)

    def get_page_data(self,is_pageinated,paginator,pageobj,show_pagenumber):
        # 如果没有分页，返加空字典
        if not is_pageinated:
            return {}
        """
        分页数据有三部分组成，
        左边用left存页码,右边用right存页码，中间部分就是当前页page_obje.number
        lefe,right都初始列表
        """
        left=[]
        right=[]

        #当前页面数值的获取,得用户当前请求的页码号
        cur_page=pageobj.number
        print('cur_page',cur_page)
        #取出分页中最后的页码
        total=paginator.num_pages
        #得到显示页数的一半，‘//’可以取得两数相除的商的整数部分
        half=show_pagenumber//2
        print(half)
        #取出当前页面前(letf)显示页标签个数,注意range(）如：range(start, stop)用法，计数从 start 开始， 计数到 stop 结束但不包括 stop
        for i in range(cur_page - half,cur_page):
        #数值大于等于1时，才取数值放到left列表中
            if i>=1:
                left.append(i)
        # 取出当前页后前(right)显示页标签个数,再次提示注意range()用法
        for i in range(cur_page+1, cur_page + half +1):
            # 数值小于等于页数的最大页数时，才取数值放到right列表中
            if i <= total:
                right.append(i)
        page_data={
            'left':left,
            'right':right,
        }
        return page_data


class blogdetailview(BaseMixin,DetailView): # 文章详情页
    model = models.Blog
    template_name = 'blog/detail.html'
    context_object_name = 'blog'
    pk_url_kwarg = 'pk'
    queryset = Blog.objects.all()
    def get_object(self,queryset=None):
        blog=super(blogdetailview,self).get_object(queryset=None)
        blog.increase_views()
        return blog
    def get_context_data(self,**kwargs):
        context=super(blogdetailview,self).get_context_data(**kwargs)
        form=CommentForm()
        comment_list=self.object.comment_set.all()
        context.update({
            'form':form,
            'comment_list':comment_list,
            'foruminfo':get_forum_info(),
            'online_ips_count':get_online_ips_count(),
            'hot_posts':self.queryset.order_by("-response_times")[0:10]
        })
        return context

def postdetail(request, post_pk):
    """帖子详细页面"""
    post_pk = int(post_pk)
    blog = Blog.objects.get(pk=post_pk)
    comment_list = blog.comment_set.all()
    if request.user.is_authenticated:
        k = Notice.objects.filter(receiver=request.user, status=False).count()
    else:
        k = 0
    # 统计帖子的访问访问次数
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        ip = request.META['HTTP_X_FORWARDED_FOR']
    else:
        ip = request.META['REMOTE_ADDR']
    title = blog.title
    visited_ips = cache.get(title, [])

    if ip not in visited_ips:
        blog.views += 1
        blog.save()
        visited_ips.append(ip)
    cache.set(title, visited_ips, 15 * 60)
    return render(request, 'blog/detail.html', {
        'post':blog,
        'comment_list':comment_list,
        'message_number':k
    })


def archives(request, year, month):
   blog_list = models.Blog.objects.filter(created_time__year=year,
                                    created_time__month=month
                                    ).order_by('-created_time')
   return render(request, 'blog/index.html', context={'blog_list':blog_list})

def category(request, pk):
    cate = get_object_or_404(Category, pk=pk)
    blog_list = models.Blog.objects.filter(category=cate).order_by('-created_time')
    return render(request, 'blog/index.html', context={'Blog_list':blog_list})

class categoryview(ListView):
    model=models.Blog
    template_name='blog/index.html'
    context_object_name='blog_list'
    def get_queryset(self):
        cate=get_object_or_404(models.Category,pk=self.kwargs.get('pk'))
        return super(categoryview,self).get_queryset().filter(category=cate).order_by('-created_time')

class tagview(ListView):
    model=models.Blog
    template_name='blog/index.html'
    context_object_name='blog_list'
    def get_queryset(self):
        tag=get_object_or_404(models.Tag,pk=self.kwargs.get('pk'))
        return super(tagview,self).get_queryset().filter(tags=tag).order_by('created_time')

def search(request):
    print('qqqqq')
    q = request.GET.get('q')
    error_msg = ''
    if not q:
        error_msg = "请输入关键词"
        return render(request, 'blog/index.html', {'error_msg': error_msg})
    blog_list = models.Blog.objects.filter(Q(title__icontains=q) | Q(body__icontains=q))
    return render(request, 'blog/index.html', {'error_msg': error_msg,'blog_list':blog_list})


def login(request):
    if request.method == "POST":
        username = request.POST.get("username") #从提交过来的数据提取用户名和密码
        pwd = request.POST.get("password")
        user = auth.authenticate(username=username, password=pwd) # 利用auth模块做用户名和密码的校验
        #print(type(user),user)
        if user:
            auth.login(request, user)  # 用户登录，并将登录用户赋值给request.user
            user.levels += 1  # 登录一次积分加 1
            user.save()
            return redirect("/")
        else:
            errormsg="用户名或密码错误！"
            return render(request,'blog/login.html',{'error':errormsg})
    return render(request,'blog/login.html')

# 注册的视图函数
from . import forms

def registe(request):   # 要点击图片换头像
    if request.method == "POST":
        form_obj = forms.reg_form(request.POST,request.FILES)
        if form_obj.is_valid(): # 判断校验是否通过
            form_obj.cleaned_data.pop("repassword")
            head_img = request.FILES.get("head_img")

            user_obj=models.loguser.objects.create_user(**form_obj.cleaned_data,is_staff=1,is_superuser=1)
            # obj.is_staff
            auth.login(request, user_obj)  # 用户登录，可将登录用户赋值给request.user
            return redirect('/')
        else:
            #print(form_obj['repassword'].errors)
            return render(request, "blog/registe.html", {"formobj": form_obj})
    form_obj = forms.reg_form()# 生成一个form对象
    return render(request, "blog/registe.html", {"formobj": form_obj})



def myindex(request,userid):
   blog_list = Blog.objects.filter(id=userid).order_by('-created_time')
   tabname='mytab'
   return render(request, 'blog/index.html', context={'blog_list':blog_list,'tabname':tabname})

class myindex(ListView):
    model = models.Blog
    template_name = 'blog/index.html'
    context_object_name = 'blog_list'
    def get_queryset(self):
        loguser=get_object_or_404(models.loguser,pk=self.kwargs.get('loguserid'))
        return super(myindex,self).get_queryset().filter(author=loguser).order_by('-created_time')
    def get_context_data(self, **kwargs):
        context=super(myindex,self).get_context_data(**kwargs)
        context['tabname']='mytab'
        return context

class authorindex(ListView):
    model = models.Blog
    template_name = 'blog/index.html'
    context_object_name = 'blog_list'
    def get_queryset(self):
        user=get_object_or_404(models.loguser,pk=self.kwargs.get('id'))
        return super(authorindex,self).get_queryset().filter(author=user).order_by('-created_time')
    def get_context_data(self, **kwargs):
        context=super(authorindex,self).get_context_data(**kwargs)
        context['tabname']='firsttab'
        return context


def logout(request):  # 用户注销
    auth.logout(request)
    return redirect("/")

#-------------------测试前台使用django ckeditor-----------
def test_ckeditor_front(request):
    user_obj = models.loguser.objects.all().first()
    auth.login(request, user_obj)

    blog=models.Blog.objects.get(id=1)
    return render(request,'blog/test_ckeditor_front.html',{'blog':blog})
"""
"""
def makefriend(request, sender, receiver):
    """加好友"""
    sender = loguser.objects.get(username=sender)
    receiver = loguser.objects.get(username=receiver)
    application = Application(sender=sender, receiver=receiver, status=0)
    application.save()
    return HttpResponse(
        "OK申请发送成功！%s-->%s;<a href='/'>返回</a>" % (sender, receiver))

@login_required(login_url=reverse_lazy('user_login'))
def shownotice(request):
    """消息通知"""
    notice_list = Notice.objects.filter(receiver=request.user, status=False)
    myfriends = loguser.objects.get(username=request.user).friends.all()
    return render(request, 'notice_list.html', {
        'notice_list': notice_list,
        'myfriends': myfriends
    })


def noticedetail(request, pk):
    """具体通知"""
    pk = int(pk)
    notice = Notice.objects.get(pk=pk)
    notice.status = True
    notice.save()
    if notice.type == 0:  # 评论通知
        post_id = notice.event.post.id
        return HttpResponseRedirect(
            reverse_lazy('post_detail', kwargs={"post_pk": post_id}))
    message_id = notice.event.id  # 消息通知
    return HttpResponseRedirect(
        reverse_lazy('message_detail', kwargs={"pk": message_id}))


def friendagree(request, pk, flag):
    """好友同意/拒绝（flag 1同意，2拒绝）"""
    flag = int(flag)
    pk = int(pk)
    entity = Notice.objects.get(pk=pk)
    entity.status = True
    application = entity.event
    application.status = flag

    application.receiver.friends.add(application.sender)
    application.save()
    entity.save()

    if flag == 1:
        str = "已加好友"
    else:
        str = "拒绝加好友"
    return HttpResponse(str)

class UserPostView(ListView):
    """用户已发贴"""
    template_name = 'user_posts.html'
    context_object_name = 'user_posts'
    paginate_by = PAGE_NUM
    def get_queryset(self):
        user_posts = Blog.objects.filter(author=self.request.user)
        return user_posts

class PostCreate(CreateView):
    """发帖"""
    model = Blog
    template_name = 'form.html'
    form_class = PostForm
    # fields = ('title', 'column', 'type_name','content')
    # SAE django1.5中fields失效，不知原因,故使用form_class
    success_url = reverse_lazy('user_post')

    # 这里我们必须使用reverse_lazy() 而不是reverse，因为在该文件导入时URL 还没有加载。

    def form_valid(self, form):
        # 此处有待加强安全验证
        validate = self.request.POST.get('validate', None)
        formdata = form.cleaned_data
        # if self.request.session.get('validate', None) != validate:
            # return HttpResponse("验证码错误！<a href='/'>返回</a>")
        user = loguser.objects.get(username=self.request.user.username)
        # form.instance.author = user
        # form.instance.last_response  = user
        formdata['author'] = user
        formdata['last_response'] = user
        p = Blog(**formdata)
        p.save()
        user.levels += 5  # 发帖一次积分加 5
        user.save()
        return HttpResponse("发贴成功！<a href='/'>返回</a>")


class PostUpdate(UpdateView):
    """编辑贴"""
    form_class =PostForm
    model =Blog
    template_name = 'form.html'
    success_url = reverse_lazy('blog:user_post')


class PostDelete(DeleteView):
    """删贴"""
    model = Blog
    template_name = 'delete_confirm.html'
    success_url = reverse_lazy('blog:user_post')


@login_required(login_url=reverse_lazy('blog:login'))
def makecomment(request):
    """评论"""
    if  request.method == 'POST':
        comment = request.POST.get("comment", "")
        blog_id = request.POST.get("blog_id", "")
        comment_id = request.POST.get("comment_id", "")

        user = loguser.objects.get(username=request.user)
        p = Blog.objects.get(pk=blog_id)
        p.response_times += 1
        p.last_response = user

        if comment_id:
            p_comment = Comment.objects.get(pk=comment_id)
            c = Comment(
                blog=p, author=user, comment_parent=p_comment, text=comment)
            c.save()
        else:
            c = Comment(blog=p, author=user, text=comment)
            c.save()
        p.save()
        user.levels += 3  # 评论一次积分加 3
        user.save()
    return HttpResponse("评论成功! ")

class MessageCreate(CreateView):
    """发送消息"""
    model = Message
    template_name = 'form.html'
    form_class = MessageForm
    # fields = ('content',)
    # SAE django1.5中fields失效，不知原因,故使用form_class
    success_url = reverse_lazy('show_notice')

    def form_valid(self, form):
        # 此处有待加强安全验证
        sender = loguser.objects.get(username=self.request.user)
        receiver_id = int(self.kwargs.get('pk'))
        receiver = loguser.objects.get(id=receiver_id)
        formdata = form.cleaned_data
        formdata['sender'] = sender
        formdata['receiver'] = receiver
        m = Message(**formdata)
        m.save()
        return HttpResponse("消息发送成功！<a href='/'>返回</a>")


class MessageDetail(DetailView):
    """具体消息"""
    model = Message
    template_name = 'message.html'
    context_object_name = 'message'

def validate(request):
    """验证码"""
    m_stream = BytesIO()
    validate_code = create_validate_code()
    img = validate_code[0]
    img.save(m_stream, "GIF")
    request.session['validate'] = validate_code[1]
    return HttpResponse(m_stream.getvalue(), "image/gif")

@login_required(login_url=reverse_lazy('blog:login'))
def profile(request, pk):
    user = get_object_or_404(loguser,pk=pk)
    return render(request, 'profile.html', {'user': user})

def profile_update(request, pk):
    user = get_object_or_404(loguser,pk=pk)
    # user_profile = get_object_or_404(UserProfile, user=user)

    if request.method == "POST":
        form = ProfileForm(request.POST)
        if form.is_valid():
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email=form.cleaned_data['email']
            user.nikename= form.cleaned_data['nikename']
            user.telephone = form.cleaned_data['telephone']
            # user_profile.head_img= form.cleaned_data['head_img']
            user.save()
            return HttpResponseRedirect(reverse('blog:profile', args=[user.id]))
    else:
        default_data = {'first_name': user.first_name, 'last_name': user.last_name,'email': user.email,
                        'nikename': user.nikename, 'telephone': user.telephone,}
        form = ProfileForm(default_data)
    return render(request, 'profile_update.html', {'form': form, 'user': user})




def changepwd(request,pk):
    if request.method == 'GET':
        form = ChangepwdForm()
        return render(request,'changepwd.html', {'form': form,})
    else:
        form = ChangepwdForm(request.POST)
        if form.is_valid():
            username = request.user.username
            oldpassword = request.POST.get('oldpassword', '')
            user = auth.authenticate(username=username, password=oldpassword)
            if user is not None and user.is_active:
                newpassword = request.POST.get('newpassword1', '')
                user.set_password(newpassword)
                user.save()
                return render(request,'blog/index.html', {'changepwd_success':True})
            else:
                return render(request,'changepwd.html',{'form': form,'oldpassword_is_wrong':True})
        else:
            return render(request,'changepwd.html', request, {'form': form,})


from django.db.models import Count
from django.db.models.functions import TruncMonth






