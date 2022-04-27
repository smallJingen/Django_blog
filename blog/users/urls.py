# -*- coding: utf-8 -*-
# @Time : 2022/4/27 15:43
# @Author : Mr Huang
# @Email : hjg211218@163.com
# @File : urls.py
# @Software: PyCharm
from django.urls import path
from users.views import RegisterView

urlpatterns = [
    path('register/',RegisterView.as_view(),name='register')
]