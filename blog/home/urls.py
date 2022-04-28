# -*- coding: utf-8 -*-
# @Time : 2022/4/28 10:44
# @Author : Mr Huang
# @Email : hjg211218@163.com
# @File : urls.py
# @Software: PyCharm

from django.urls import path

from .views import homeIndex

urlpatterns = [
    path('',homeIndex.as_view(),name='index')
]