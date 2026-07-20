from datetime import datetime
from platform import uname
from django.contrib.auth import authenticate, login, logout,get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm,PasswordResetForm
from django.contrib.auth.views import LoginView,LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, FormView
from django.views.decorators.csrf import csrf_protect
# from anaconda_navigator.api.external_apps.exceptions import ValidationError
from django.contrib import admin, messages
from django.http import JsonResponse
from django.urls import reverse_lazy
from .models import Parttable,Backbonetable,Plasmidneed,CustomUser
import hashlib
from django.shortcuts import render, HttpResponse,redirect
from django import forms
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import Q

#md5加密
def md5(data):
    m = hashlib.md5()
    m.update(data.encode('utf-8'))
    return m.hexdigest()

# User = get_user_model()
class ResetPasswordForm(PasswordResetForm):
    email = forms.EmailField(
        label='邮箱地址',
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入注册时使用的邮箱（选填）',
            'autocomplete': 'email',
        }),
    )
    uname = forms.CharField(
        label=_('用户名'),
        widget=forms.TextInput(attrs={
            'class':'form-control',
            'placeholder':'请输入用户名（选填）',
            'autocomplete':'uname'
        })
    )
    
    password1 = forms.CharField(
        label=_('密码'),
        widget=forms.PasswordInput(attrs={
            'class':'form-control',
            'placeholder':'请输入密码',
            'autocomplete':'new-password'
        })
    )
    
    password2 = forms.CharField(
        label = _('确认密码'),
        widget=forms.PasswordInput(attrs={
            'class':'form-control',
            'placeholder':'请再次输入密码',
            'autocomplete':'new-password'
        })
    )
    def clean_email_username(self):
        email = self.cleaned_data.get('email')
        uname = self.cleaned_data.get('uname')
        if(email != "" and uname != ""):
            # 检查邮箱是否存在
            print(CustomUser.objects.filter(email=email, is_active=True).exists())
            print(CustomUser.objects.filter(uname=uname, is_active =True).exists())
            if not CustomUser.objects.filter(email=email, is_active=True).exists() and not CustomUser.objects.filter(uname = uname, is_active=True).exists():
                self.add_error("email","用户名或邮箱不存在")
                self.add_error("uname","用户名或邮箱不存在")
                return False
            if(self.cleaned_data.get("password1") != self.cleaned_data.get("password2")):
                self.add_error("password1","两次输入的密码不一致")
                self.add_error("password2","两次输入的密码不一致")
                return False
                    # with transaction.atomic():
                    #     the_user = CustomUser.objects.select_for_update(Q(email__iexact = email) | Q(uname__iexact = uname))
                    #     the_user.password = md5(self.cleaned_data.get("password1"))
                    #     the_user.save()
            return self.cleaned_data
        else:
            self.add_error("email","用户名或密码至少填写一项")
            self.add_error("uname","用户名或密码至少填写一项")
            return False
        
    def authenticate_user(self, username, email, password):
        """认证用户（支持邮箱或用户名登录）"""
        from django.contrib.auth import authenticate
        from .models import CustomUser
        print("authenticated_user")
        # 先尝试用用户名认证
        print(username)
        print(password)
        user = authenticate(username=username, password=md5(password))
        if user != None:
            self.cleaned_data['uid'] = user.uid
            return user
        # 如果失败，尝试用邮箱认证
        if user is None and '@' in email:
            try:
                user_obj = CustomUser.objects.get(email=email)
                user = authenticate(username=user_obj.username, password=md5(password))
                self.cleaned_data['uid'] = user.uid
                return user
            except CustomUser.DoesNotExist:
                pass
        else:
            print("用户不存在")
            self.add_error("username","用户不存在")
            return user
        
class UserRegisterForm(forms.Form):
    uname = forms.CharField(
        label=_('用户名'),
        widget=forms.TextInput(attrs={
            'class':'form-control',
            'placeholder':'请输入用户名',
            'autocomplete':'uname'
        })
    )
    
    email = forms.EmailField(
        label = _('邮箱'),
        widget=forms.EmailInput(attrs={
            'class':'form-control',
            'placeholder':'请输入邮箱地址',
            'autocomplete':'email'
        })
    )
    
    password1 = forms.CharField(
        label=_('密码'),
        widget=forms.PasswordInput(attrs={
            'class':'form-control',
            'placeholder':'请输入密码',
            'autocomplete':'new-password'
        })
    )
    
    password2 = forms.CharField(
        label = _('确认密码'),
        widget=forms.PasswordInput(attrs={
            'class':'form-control',
            'placeholder':'请再次输入密码',
            'autocomplete':'new-password'
        })
    )
    
    
    def clean_data(self):
        self.cleaned_data = super().clean()
        username = self.cleaned_data.get('uname')
        email = self.cleaned_data.get('email')
        print(self.cleaned_data)
        if username and CustomUser.objects.filter(uname = username).exists():
            print('该用户名已被注册')
            self.add_error('uname','该用户名已被注册')
            return False
        if(email and CustomUser.objects.filter(email = email).exists()):
            print('该邮箱已被注册')
            self.add_error('email','该邮箱已被注册')
            return False
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1!= password2:
            self.add_error('password2','两次输入密码不一致')
            return False
        return self.cleaned_data
    
    def save(self):
        print(self.cleaned_data)
        user = CustomUser.objects.create_user(
            uname = self.cleaned_data.get('uname'),
            email = self.cleaned_data.get('email'),
            password=md5(self.cleaned_data.get('password1'))
        )
        print(md5(self.cleaned_data.get('password1')))
        print(user)
        return user
    
    def save_superuser(self):
        print(self.cleaned_data)
        user = CustomUser.objects.create_superuser(
            uname = self.cleaned_data.get('uname'),
            email = self.cleaned_data.get('email'),
            password=md5(self.cleaned_data.get('password1'))
        )
        print(user)
        return user
    
    
    def authenticate_user(self, username, email, password):
        """认证用户（支持邮箱或用户名登录）"""
        from django.contrib.auth import authenticate
        from .models import CustomUser
        print("authenticated_user")
        # 先尝试用用户名认证
        print(username)
        print(password)
        user = authenticate(username=username, password=md5(password))
        if user != None:
            self.cleaned_data['uid'] = user.uid
            return user
        # 如果失败，尝试用邮箱认证
        if user is None and '@' in email:
            try:
                user_obj = CustomUser.objects.get(email=email)
                user = authenticate(username=user_obj.username, password=md5(password))
                self.cleaned_data['uid'] = user.uid
                return user
            except CustomUser.DoesNotExist:
                pass
        else:
            print("用户不存在")
            self.add_error("username","用户不存在")
            return user

    
class CustomLoginForm(AuthenticationForm):
    """自定义登录表单"""
    username = forms.CharField(
        label=_('用户名或邮箱'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入用户名或邮箱',
            'autocomplete': 'username'
        })
    )
    
    password = forms.CharField(
        label=_('密码'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入密码',
            'autocomplete': 'current-password'
        })
    )
    
    # remember_me = forms.BooleanField(
    #     required=False,
    #     label=_('记住我'),
    #     widget=forms.CheckboxInput(attrs={
    #         'class': 'form-check-input'
    #     })
    # )
    def __init__(self, request = None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        
    def clean(self):
        """表单验证"""
        # self.cleaned_data = super().clean()
        print("self.clean")
        # 如果表单验证失败，直接返回
        if 'username' not in self.cleaned_data or 'password' not in self.cleaned_data:
            self.add_error('username',"请输入用户名")
            self.add_error('password',"请输入密码")
            return self.cleaned_data
        
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        # print(username)
        # print(password)
        # 尝试认证
        user = self.authenticate_user(username, password)
        
        if user is None:
            raise forms.ValidationError(
                _('用户名或密码错误'),
                code='invalid_login'
            )
        
        # # 检查账户是否被锁定
        # if user.is_locked:
        #     raise forms.ValidationError(
        #         _('账户已被锁定，请稍后再试或联系管理员'),
        #         code='account_locked'
        #     )
        
        # # 检查账户是否激活
        # if not user.is_active:
        #     raise forms.ValidationError(
        #         _('账户已被禁用，请联系管理员'),
        #         code='account_disabled'
        #     )
        
        self.cleaned_data['user'] = user
        return self.cleaned_data
    
    def authenticate_user(self, username, password):
        """认证用户（支持邮箱或用户名登录）"""
        from django.contrib.auth import authenticate
        from .models import CustomUser
        print("authenticated_user")
        # 先尝试用用户名认证
        print(username)
        print(password)
        user = authenticate(username=username, password=md5(password))
        if user != None:
            self.cleaned_data['uid'] = user.uid
            return user
        # 如果失败，尝试用邮箱认证
        if user is None and '@' in username:
            try:
                user_obj = CustomUser.objects.get(email=username)
                print(user_obj)
                user = authenticate(username=user_obj.username, password=md5(password))
                print(user)
                self.cleaned_data['uid'] = user.uid
                return user
            except CustomUser.DoesNotExist:
                print("用户不存在")
                self.add_error("username","用户不存在")
                return user
            except Exception as e:
                print("1111111")
                print(e.args)
        else:
            print("用户不存在")
            self.add_error("username","用户不存在")
            return user
# @csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        next_url = request.GET.get("next","/LabDatabase/index")
        print("next_url: "+next_url)
        return redirect(next_url)
    if request.method == 'POST':
        next_url = request.GET.get("next","/LabDatabase/index")
        print("next_url: "+next_url)
        form = CustomLoginForm(request=request, data = request.POST)
        # print(form.errors)
        if(form.is_valid()):
            # form.clean()
            print(form.cleaned_data)
            # user = form.authenticate_user()
            # login(request, user)
            login(request, form.cleaned_data['user'])
            if('@' in form.cleaned_data["username"]):
                user_obj = CustomUser.objects.get(email = form.cleaned_data["username"])
            else:
                user_obj = CustomUser.objects.get(uname = form.cleaned_data["username"])
            if user_obj is not None:
                uid = user_obj.uid
                username = user_obj.uname
                print(form.cleaned_data['user'])
                request.session['info'] = {'uid':uid,'uname':username}
                print(form.cleaned_data)
                return redirect(next_url)
            else:
                form.add_error('username',"用户名或邮箱错误")
                form.add_error('password',"密码错误")
                return render(request, 'Login.html', {"form":form,"next_url":next_url})
        else:
            # print(form.cleaned_data)
            form.add_error('username',"用户名或邮箱错误")
            form.add_error('password',"密码错误")
            return render(request, 'Login.html', {"form":form,"next_url":next_url})
    else:
        form = CustomLoginForm(request=request)
        next_url = request.GET.get("next","/LabDatabase/index")
        return render(request, 'Login.html', {"form":form,"next_url":next_url})
    
    
        

def register(request):
    """用户注册视图"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.clean_data()
            if("uname" in form.cleaned_data and "email" in form.cleaned_data and "password1" in form.cleaned_data and "password2" in form.cleaned_data):
                
                # 创建用户
                user = form.save()
                # 自动登录
                # username, email, password
                user = form.authenticate_user(form.cleaned_data['uname'], form.cleaned_data['email'], form.cleaned_data['password1'])
                login(request, user)
                request.session['info'] = {'uid':form.cleaned_data['uid'],'uname':form.cleaned_data['uname']}

                # 发送欢迎邮件（可选）
                # send_welcome_email(user)
                messages.success(request, f'欢迎 {user.username}！注册成功！')
                # 重定向到首页
                return redirect('/LabDatabase/index')
            else:
                return render (request, 'Register.html',{"form":form})
        else:
            print("form is invalid")
        
    form = UserRegisterForm()
    return render(request, 'Register.html', {'form': form})

def logout(request):
    print("7777777")
    from django.contrib.auth import logout
    if request.user.is_authenticated:
        logout(request)
    return redirect("/LabDatabase/login")



def admin_register(request):
    """用户注册视图"""
    print("111111111111111111111111111111")
    print(request.method)
    if request.method == 'POST':
        print("balabala")
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.clean_data()
            if("uname" in form.cleaned_data and "email" in form.cleaned_data and "password1" in form.cleaned_data and "password2" in form.cleaned_data):
                
                # 创建用户
                user = form.save_superuser()
                # 自动登录
                # username, email, password
                user = form.authenticate_user(form.cleaned_data['uname'], form.cleaned_data['email'], form.cleaned_data['password1'])
                login(request, user)
                request.session['info'] = {'uid':form.cleaned_data['uid'],'uname':form.cleaned_data['uname']}

                # 发送欢迎邮件（可选）
                # send_welcome_email(user)
                messages.success(request, f'欢迎 {user.username}！注册成功！')
                # 重定向到首页
                return redirect('/LabDatabase/index')
            else:
                return render (request, 'Register_admin.html',{"form":form})
        else:
            print("form is invalid")
    else:
        print("77777777")
        form = UserRegisterForm()
        return render(request, 'Register_admin.html', {'form': form})


def reset_password(request):
    if(request.method == "GET"):
        form = ResetPasswordForm()
        return render(request, "reset_password.html",{'form':form})
    else:
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            clean_data = form.clean_email_username()
            print(f"clean_data is {clean_data}")
            if(clean_data != False and "uname" in clean_data and "email" in clean_data and "password1" in clean_data and "password2" in clean_data):
                with transaction.atomic():
                    the_user = CustomUser.objects.select_for_update().get(Q(email = clean_data.get("email")) | Q(uname = clean_data.get("uname")))
                    the_user.set_password(md5(clean_data.get("password1")))
                    the_user.save()
                
                # 自动登录
                # username, email, password
                user = form.authenticate_user(clean_data['uname'], clean_data['email'], clean_data['password1'])
                login(request, user)
                request.session['info'] = {'uid':form.cleaned_data['uid'],'uname':form.cleaned_data['uname']}
                # 发送欢迎邮件（可选）
                # send_welcome_email(user)
                messages.success(request, f'欢迎 {user.username}！注册成功！')
                # 重定向到首页
                return redirect('/LabDatabase/index')
            else:
                return render (request, 'reset_password.html',{"form":form})
# class LoginModelForm(forms.ModelForm):
#     password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'请输入密码','minlength':6,"maxlength":100,'required':True}))
#     class Meta:
#         model = User
#         fields = ['uname','password']
#     def clean_password(self):
#         pwd = self.cleaned_data.get('password')
#         return md5(pwd)

# class RegisterModelForm(forms.ModelForm):
#     password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'请输入密码','minlength':6,"maxlength":100,'required':True}))
#     password_Confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control','placeholder':'请再次输入密码','minlength':6,"maxlength":100,'required':True}))

#     class Meta:
#         model = User
#         fields = ['uname','email','password']
#     def clean_password(self):
#         pwd = self.cleaned_data.get('password')
#         if len(pwd)<6:
#             raise Exception("密码长度不能少于6位")
#         return md5(pwd)
#     def clean_password_Confirm(self):
#         pwd = self.cleaned_data.get('password_Confirm')
#         if len(pwd)<6:
#             raise Exception("密码长度不能少于6位")
#         return md5(pwd)
#     def validPassword(self):
#         # print("validPassword")
#         pwd = self.cleaned_data.get('password')
#         pwdConfirm = self.cleaned_data.get('password_Confirm')
#         if(pwd == pwdConfirm):
#             return True
#         else:
#             return False
        
# class UserRegisterView(CreateView):
#     form_class = UserRegisterForm
#     template_name = "Register.html"
#     success_url = reverse_lazy("index")
    
#     def form_valid(self, form):
#         response = super().form_valid(form)
        
#         from django.contrib.auth import login
#         user = form.save()
#         login(self.request, user)
        
#         messages.success(self.request, '注册成功！欢迎使用LabDatabase！')
#         return response
#     def form_invalid(self, form):
#         messages.error(self.request, "注册失败，请检查信息")
#         return super().form_invalid(form)

# class UserLoginView(LoginView):
#     """用户登录视图"""
#     form_class = UserLoginForm
#     template_name = "Login.html"
#     redirect_authenticated_user = True
    
#     def form_valid(self, form):
#         remember_me = form.cleaned_data.get("remember_me")
        
#         if not remember_me:
#             self.request.session.set_expiry(0)
#         else:
#             self.request.session.set_expiry(60*60*24*7)
#         messages.success(self.request, f'欢迎回来，{form.get_user().email}')
#         return super().form_valid(form)

#     def get_success_url(self):
#         user = self.request.user
#         print(user)
#         next_url = self.request.GET.get('next')
#         return next_url if next_url else super().get_success_url()

# class UserLogoutView(LogoutView):
#     next_page = reverse_lazy('home')
    
#     def dispatch(self, request, *args, **kwargs):
#         """登出前处理"""
#         if request.user.is_authenticated:
#             messages.success(request, '您已成功登出')
#         return super().dispatch(request, *args, **kwargs)

        
# '''用户登录'''
# def login(request):
#     """登录页面"""
#     next = request.GET.get('next','')
#     if(request.method == 'GET'):
#         form = LoginModelForm()
#         next = request.GET.get('next','')
#         return render(request,"Login.html",{'form':form})
#     form = LoginModelForm(data= request.POST)
#     if form.is_valid():
#         # print(next)
#         #数据库校验，获取用户对象,ERROR:None
#         user = authenticate(request,username = form.cleaned_data['uname'],password=form.cleaned_data['password'])
        
#         if user is not None:
#             print("登陆成功")
#             print(user)
#             login(request, user)
            
#             request.session.set_expiry(60*60*24*7)
            
#             next_url = request.POST.get('next','/index')
#             return redirect(next_url)
#             # request.session['info'] = {'uid':admin_object.uid,'uname':admin_object.uname}
#         # admin_object = User.objects.filter(uname=form.cleaned_data['uname'],password=form.cleaned_data['password']).first()
#         # if(not admin_object):
#         #     # print(form.cleaned_data)
#         #     form.add_error("uname","用户名或密码错误")
#         #     form.add_error("password","用户名或密码错误")
#         #     return render(request, "Login.html", {'form': form})
#         # #验证正确之后
#         # #网站生成随机字符串，写到浏览器cookie中；再写入session
#         else:
#             return render(request,"Login.html",{'form':form})


# def logout(request):
#     logout(request)
#     request.session.clear()
#     messages.success(request, "您已成功退出登录")
#     return redirect("/LabDatabase/login")


# def user_profile(request):
#     if not request.user.is_authenticated:
#         messages.error(request, '请先登录')
#         redirect("/LabDatabase/login")
#     return render(request, 'profile.html',{
#         'user':request.user
#     })

# def register(request):
#     if(request.method == 'GET'):
#         form = RegisterModelForm()
#         return render(request,"Register.html",{'form':form})
#     form = RegisterModelForm(data= request.POST)
#     # print(form)
#     if form.is_valid():
#         # print("AAAAAA")
#         # print(form.cleaned_data)
#         if not all([form.cleaned_data['uname'],form.cleaned_data['email'],form.cleaned_data['password'],form.cleaned_data['password_Confirm']]):
#             messages.error(request, '所有字段都必须填写')
#             return render(request,"Register.html",{'form':form})
        
#         if(form.validPassword() == False):
#             # print("111111111")
#             form.add_error("password","两次输入的密码不一致")
#             form.add_error("password_Confirm","两次输入的密码不一致")
#             messages.error(request, '两次输入密码不一致')
#             return render(request,"Register.html",{'form':form})
#         #数据库校验，获取用户对象,ERROR:None
#         admin_object = User.objects.filter(uname=form.cleaned_data['uname']).first()
#         # print(admin_object)
#         if(User.objects.filter(uname = form.cleaned_data['uname']).exists()):
#             form.add_error("uname","用户名已存在")
#             messages.error(request, '用户名已存在')
#             # form.add_error("uname","用户名已存在")
#             return render(request, "Register.html", {'success': False,'message':"用户名已存在",'form':form})
#         if(User.objects.filter(email = form.cleaned_data['email']).exists()):
#             form.add_error("email","邮箱已被注册")
#             messages.error(request, '邮箱已被注册')
#             return render(request, "Register.html",{'success':False,'message':"用户名已存在",'form':form})
#         #验证正确之后
#         #网站生成随机字符串，写到浏览器cookie中；再写入session
#         try:
#             # User.objects.create(uname=form.cleaned_data['uname'], email=form.cleaned_data['email'], password=form.cleaned_data['password'],create_time=datetime.now())
#             user = User.objects.create_user(
#                 username = form.cleaned_data['uname'],
#                 email = form.cleaned_data['email'],
#                 password = form.cleaned_data['password'],
#             )
#             user.create_time=datetime.now()
#             user.save()
#             login(request, user)
#             messages.success(request, '注册成功！')
#             return redirect("/LabDatabase/index")
#         except Exception as e:
#             # form.add_error("password","密码长度不能少于6位")
#             form.add_error("password",str(e))
#             return render(request,'Register.html',{'form':form})
#     else:
#         return render(request,"Register.html",{'form':form})
    
# def change_password(request):
#     if not request.user.is_authenticated:
#         messages.error(request, '请先登录')
#         return redirect("/LabDatabase/login")
#     if(request.method == "POST"):
#         old_password = request.POST.get('old_password')
#         new_password1 = request.POST.get('new_password1')
#         new_password2 = request.POST.get('new_password2')
        
#         if not request.user.check_password(old_password):
#             messages.error(request, '原密码错误')
#             return render(request, 'change_password.html')
#         if new_password1 != new_password2:
#             messages.error(request, '两次输入密码不一致')
#             return render(request, 'change_password.html')
#         if len(new_password1)<8:
#             messages.error(request, '新密码长度至少8位')
#             return render(request, 'change_password.html')
#         try:
#             request.user.set_password(new_password1)
#             request.user.save()
            
#             user = authenticate(
#                 username = request.user.username,
#                 password = new_password1
#             )
#             if(user is not None):
#                 login(request, user)
#             messages.success(request, '密码修改成功')
#             return redirect('/LabDatabase/profile')
#         except Exception as e:
#             messages.error(request, f"密码修改失败：{str(e)}")
#     return render(request, 'change_password.html')
