import random
import re
import time

from django.contrib.auth.models import User
from django.http import request
from django.shortcuts import render, redirect
# Create your views here.
from django.urls import reverse
from django.views import View
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse
from django_redis import get_redis_connection
from django.contrib.auth import login, logout
from django.contrib.auth import authenticate
from utils.response_code import RETCODE
from libs.yuntongxun.sms import CCP
from users.models import user

# 导入captcha中的实例对象captcha
from libs.captcha.captcha import captcha
import logging

logger = logging.getLogger('django')


# 实现注册功能的view
class RegisterView(View):

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):

        # 接收前端发送的post请求获取数据
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        sms_code = request.POST.get('sms_code')

        # 判断所传数据是否齐全
        if not all([mobile, password, password2, sms_code]):
            return HttpResponseBadRequest('所给参数不够哦！')
        # 对密码和确认密码进行判断操作
        if password != password2:
            return HttpResponseBadRequest('两次密码输入的不一致！')

        # 使用正则表达式判断用户注册密码是否符合要求
        if not re.match(r'^[0-9a-zA-Z]{8,20}$', password):
            return HttpResponseBadRequest('密码设置有误，密码由数字，字母组成！')
        # 使用正则判断手机号码驶入是否符合要求
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号码输入有误！')
        # 因为点击注册按钮时，前端发动了手机号码验证操作的请求，
        # 手机号码的验证码也已经保存在了redis中，此处可以直接获取就行

        redis_conn = get_redis_connection('default')
        redis_sms_code = redis_conn.get('sms_code:%s' % mobile)
        # 判断用户输入的手机验证码是否一致
        if redis_sms_code.decode() != sms_code:
            return HttpResponseBadRequest('手机验证码输入错误！')
        # 判断完用户输入的注册信息全部无误之后在数据库中保存用户注册信息
        usr = user.objects.create_user(
            username=mobile,
            mobile=mobile,
            password=password
        )
        # 通过django自带的方法进行保存
        login(request, usr)
        # 注册成功之后，设置重定向到首页，并为其添加cookie信息
        response = redirect(reverse('home:index'))
        response.set_cookie('is_login', True)
        response.set_cookie('username', user.username, max_age=60 * 60 * 24 * 7)
        return response


# 实现验证码的处理
class ImgCodeView(View):

    def get(self, request):
        """
        前端页面发送get请求，带上了参数uuid
        :param request:
        :return:
        """
        if not request.GET.get('uuid'):
            return HttpResponseBadRequest('没接收到uuid哦！')

        uuid = request.GET.get('uuid')

        text, image = captcha.generate_captcha()

        redis_conn = get_redis_connection('default')

        redis_conn.setex('img:%s' % uuid, 240, text)

        return HttpResponse(image, content_type='image/jpeg')


# 实现手机号码验证处理
class SmsCodeView(View):

    def get(self, request):
        """
        获取前端页面发来的get请求，
        电话号码：mobile
        图片验证码：image_code
        uuid
        :param request:
        """
        mobile = request.GET.get('mobile')
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('uuid')
        # 验证请求传来的参数是否都无误
        if not all([mobile, image_code, uuid]):
            return JsonResponse({
                'code': RETCODE.NECESSARYPARAMERR,
                'errmsg': '所传参数存在问题'}
            )
        # 在redis中获取图片验证码信息，并判断其是否存在，不存在说明已经过期
        redis_conn = get_redis_connection('default')
        redis_image_code = redis_conn.get('img:%s' % uuid)
        if not redis_image_code:
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图片验证码已经过期！'})

        # 比对图片验证码成功之后，将其删除
        try:
            redis_conn.delete('img:%s' % uuid)
        except Exception as e:
            logger.error(e)
        # 比对redis中的图片验证码和请求传过来的验证码
        if redis_image_code.decode().lower() != image_code:
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '验证码错误！'})
        # 使用随机函数生成六位的手机验证码
        sms_code = '%06d' % random.randint(1, 999999)

        logger.info(sms_code)
        # 在redis中创建键值用以存储生成的手机验证码吗，时间设置为4分钟，key为mobile，value为验证码
        redis_conn.setex('sms_code:%s' % mobile, 240, sms_code)
        # 调用验证码短信发送函数，设置有效时间期限为5分钟
        CCP().send_template_sms(mobile, [sms_code, 5], 1)

        return JsonResponse({
            'code': RETCODE.OK,
            'errmsg': '短信发送成功！'
        })


# 实现用户的登录功能
class loginView(View):

    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):

        # 前端发来请求，对其请求的参数进行接收
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        remember = request.POST.get('remember')
        # 判断手机号码和密码的输入合法性
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('电话号码出错！')
        if not re.match(r'[0-9a-zA-Z]{8,20}', password):
            return HttpResponseBadRequest('密码不符合要求，由数字、字母组成。')
        # 通过django自带的认证方式进行当前用户输入的用户信息是否正确
        if not user.objects.filter(mobile=mobile).exists():
            return HttpResponseBadRequest('用户不存在，请先注册')
        usr = authenticate(mobile=mobile, password=password)
        if usr is None:
            return HttpResponseBadRequest('用户名或者密码错误！')
        # 保存当前用户的登录信息
        login(request, usr)
        response = redirect(reverse('home:index'))
        # 根据用户是否选择保持登陆的状态进行判断是否将其状态保持
        if remember != 'on':
            request.session.set_expiry(0)
            response.set_cookie('is_login', True)
            response.set_cookie('username', usr.username, 14 * 24 * 3600)

        else:
            request.session.set_expiry(None)
            response.set_cookie('is_login', True, max_age=14 * 24 * 3600)
            response.set_cookie('username', usr.username, 14 * 2483600)

        return response


# 实现用户的退出登录功能
class logoutView(View):

    def get(self, request):

        logout(request)
        response = redirect(reverse('home:index'))
        response.delete_cookie('is_login')
        # response.delete_cookie('username')
        print('****',response)
        return response


class forgetView(View):
    def get(self, request):
        return render(request, 'forget_password.html')

    def post(self, request):

        # 接收前端发送的post请求获取数据
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        sms_code = request.POST.get('sms_code')

        # 判断所传数据是否齐全
        if not all([mobile, password, password2, sms_code]):
            return HttpResponseBadRequest('所给参数不够哦！')

        # 使用正则判断手机号码驶入是否符合要求
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号码输入有误！')
        # 使用正则表达式判断用户的新密码是否符合要求
        if not re.match(r'^[0-9a-zA-Z]{8,20}$', password):
            return HttpResponseBadRequest('密码设置有误，密码由数字，字母组成！')

        # 对密码和确认密码进行判断操作
        if password != password2:
            return HttpResponseBadRequest('新密码和确认密码输入的不一致！')

        # 因为点击获取手机号码验证按钮时，前端发动了手机号码验证操作的请求，
        # 手机号码的验证码也已经保存在了redis中，此处可以直接获取就行
        redis_conn = get_redis_connection('default')
        redis_sms_code = redis_conn.get('sms_code:%s' % mobile)
        # 判断用户输入的手机验证码是否一致
        if redis_sms_code.decode() != sms_code:
            return HttpResponseBadRequest('手机验证码输入错误！')
        # # 判断完用户输入的注册信息全部无误之后在数据库中保存用户注册信息
        # usr = user.objects.create_user(
        #     username=mobile,
        #     mobile=mobile,
        #     password=password
        # )
        # # 通过django自带的方法进行保存
        # login(request, usr)
        # # 注册成功之后，设置重定向到首页，并为其添加cookie信息
        # response = redirect(reverse('home:index'))
        # response.set_cookie('is_login', True)
        # response.set_cookie('username', user.username, max_age=60 * 60 * 24 * 7)
        # return response

        try:
            usr = user.objects.get(mobile=mobile)
        except User.DoesNotExist:
            try:
                user.objects.create_user(
                    username=mobile,
                    mobile=mobile,
                    password=password
                )
            except Exception:
                return HttpResponseBadRequest('修改失败，稍后再试！')
        else:
            # user.objects.filter(mobile=mobile).update(password=password)
            usr.set_password(password)
            usr.save()
        response = redirect(reverse('users:login'))
        return response
