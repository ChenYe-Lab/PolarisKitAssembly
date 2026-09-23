from django.contrib import admin
from django.shortcuts import render,redirect
# Register your models here.
def login(request):
    print("redirect")
    return redirect("api:login")

def logout(request):
    return redirect("api:logout")

def register(request):
    return redirect("api:register")

def register_admin(request):
    return redirect("api:AdminRegister")
