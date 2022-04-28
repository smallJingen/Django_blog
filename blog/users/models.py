from django.contrib.auth.models import AbstractUser
from django.db import models


# Create your models here.
class user(AbstractUser):
    # 电话
    mobile = models.CharField(max_length=11, unique=True, blank=True)

    # 头像
    avatar = models.ImageField(upload_to='avatar/%Y%m%d/', blank=True)

    # 简介
    user_desc = models.CharField(max_length=512, blank=True)

    # 将默认的认证字段为mobile，默认的为username
    USERNAME_FIELD = 'mobile'

    class Meta:
        db_table = 'blog_users'
        verbose_name = '用户管理'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.mobile
