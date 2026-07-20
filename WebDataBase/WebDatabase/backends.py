from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """支持邮箱或用户名登录的认证后端"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # 尝试用邮箱或用户名查找用户
            user = User.objects.get(
                Q(username=username) | Q(email=username)
            )
            # print(user.uid)
        except User.DoesNotExist:
            return None
        
        # 验证密码
        if user.check_password(password):
            print("check_password")
            return user
        
        # 增加登录失败次数
        if hasattr(user, 'increment_failed_attempts'):
            user.increment_failed_attempts()
        
        return None