# webdatabase/admin.py
from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from .models import CustomUser

# from django.contrib.admin.models import LogEntry
# from django.contrib.admin import site


# # # 注册自定义用户模型
# admin.site.register(CustomUser, UserAdmin)

# # 如果仍然有问题，可以尝试重新注册admin

# # 取消注册LogEntry
# admin.site.unregister(LogEntry)

# # 如果需要，重新注册LogEntry（会使用当前用户模型）
# class CustomLogEntryAdmin(admin.ModelAdmin):
#     list_display = ['action_time', 'user', 'content_type', 'object_repr', 'action_flag']
    
# admin.site.register(LogEntry, CustomLogEntryAdmin)