from django.http import request
from django.shortcuts import render

# Create your views here.
from django.views import View


# 实现注册功能的view

class RegisterView(View):

    def get(self, request):
        return render(request, 'register.html')
