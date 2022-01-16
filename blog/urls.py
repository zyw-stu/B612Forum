from django.contrib.auth.decorators import login_required
from django.urls import path,re_path
from . import views
from .manager_delete_decorator import delete_permission
from blog.views import PostCreate, PostUpdate, PostDelete, MessageDetail, MessageCreate, UserPostView
from django.contrib import admin
from blog import views
from blog.manager_delete_decorator import delete_permission
admin.autodiscover()

app_name = 'blog'
urlpatterns = [
    path('',views.indexview.as_view(),name='index'),
    path('myindex/<int:loguserid>/',views.myindex.as_view(),name='myindex'),
    path('authorindex/<int:id>/',views.authorindex.as_view(),name='authorindex'),
    re_path('blog/(?P<pk>[0-9]+)/',views.blogdetailview.as_view(),name='detail'),
    re_path('postdetail/(?P<post_pk>\d+)/',views.postdetail,name='post_detail'),
    re_path('archives/(?P<year>[0-9]{4})/(?P<month>[0-9]{1,2})/', views.archives, name='archives'),
    re_path('category/(?P<pk>[0-9]+)/', views.categoryview.as_view(), name='category'),
    re_path('tag/(?P<pk>[0-9]+)/', views.tagview.as_view(), name='tag'),
    path('search/', views.search, name='search'),
    path('login/', views.login,name='login'),
    path('registe/', views.registe,name='registe'),
    path('logout/',views.logout,name='logout'),
    path('test_ckeditor_front/',views.test_ckeditor_front),
    path('makefriend/(?P<sender>\w+)/(?P<receiver>\w+)/',views.makefriend, name='make_friend'),
    re_path('makecomment/', views.makecomment, name='make_comment'),
    path('user/post_create/',login_required(views.PostCreate.as_view()),name='post_create'),  # 发帖
    re_path('user/postlist/', views.UserPostView.as_view(), name='user_post'),
    path('validate/', views.validate, name='validate'),
    re_path('user/post_update/(?P<pk>\d+)/',login_required(PostUpdate.as_view()),name='post_update'),
    re_path('user/post_delete/(?P<pk>\d+)/',delete_permission(login_required(PostDelete.as_view())),name='post_delete'),
    re_path('user/notices/', views.shownotice, name='show_notice'),
    re_path('user/notices/(?P<pk>\d+)/',views.noticedetail,name='notice_detail'),
    re_path('user/friend/(?P<pk>\d+)/(?P<flag>\d+)/',views.friendagree,name='friend_agree'),  # pk为对方用户id
    re_path('user/messagedetail/(?P<pk>\d+)/',views.MessageDetail.as_view(),name='message_detail'),  # pk为消息id
    re_path('user/message/sendto/(?P<pk>\d+)/',views.MessageCreate.as_view(),name='send_message'),  # pk为对方用户id
    re_path('user/profile/(?P<pk>\d+)/', views.profile, name='profile'),
    re_path('user/profile/update/(?P<pk>\d+)/', views.profile_update, name='profile_update'),
    re_path('user/pwdchange/(?P<pk>\d+)/', views.changepwd, name='pwd_change'),
]
