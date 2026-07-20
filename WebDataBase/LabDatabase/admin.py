from django.contrib import admin
from django.shortcuts import render,redirect
# Register your models here.
def login(request):
    print("redirect")
    return redirect("/WebDatabase/login")

def logout(request):
    return redirect("/WebDatabase/logout")

def register(request):
    return redirect("/WebDatabase/register")

def register_admin(request):
    return redirect("/WebDatabase/AdminRegister")