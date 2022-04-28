# -*- coding: utf-8 -*-
# @Time : 2022/4/27 22:26
# @Author : Mr Huang
# @Email : hjg211218@163.com
# @File : test.py
# @Software: PyCharm
import random
import re

print('%06d' % random.randint(1, 999))
mobile = '13633919878'
if re.match('^1[3-9]\d{9}$',mobile):
    print('手机号没问题')