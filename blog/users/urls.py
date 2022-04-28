# -*- coding: utf-8 -*-
# @Time : 2022/4/27 15:43
# @Author : Mr Huang
# @Email : hjg211218@163.com
# @File : urls.py
# @Software: PyCharm
from django.urls import path
from users.views import RegisterView, ImgCodeView, SmsCodeView,loginView,logoutView,forgetView

urlpatterns = [
    # 注册页面处理
    path('register/', RegisterView.as_view(), name='register'),
    #  注册页面验证码处理
    path('imagecode/', ImgCodeView.as_view(), name='imagecode'),

    #    手机验证码处理
    path('smscode/', SmsCodeView.as_view(), name='smscode'),

    path('login/',loginView.as_view(),name='login'),

    path('logout/',logoutView.as_view(),name='logout'),

    path('forget_password/',forgetView.as_view(),name='forget')
]
