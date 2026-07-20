from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

class PermissionManager:
    """权限管理器"""
    
    @staticmethod
    def setup_default_groups_and_permissions():
        """设置默认的用户组和权限"""
        
        # 1. 超级管理员组 - 拥有所有权限
        admin_group, _ = Group.objects.get_or_create(name='超级管理员')
        admin_group.permissions.set(Permission.objects.all())
        
        # 2. 管理员组
        manager_group, _ = Group.objects.get_or_create(name='管理员')
        manager_permissions = Permission.objects.filter(
            codename__in=[
                'can_view_admin_dashboard',
                'can_manage_users',
                'can_manage_content',
                'can_view_reports',
                'can_export_data',
            ]
        )
        manager_group.permissions.set(manager_permissions)
        
        # 3. 编辑组
        editor_group, _ = Group.objects.get_or_create(name='编辑')
        editor_permissions = Permission.objects.filter(
            codename__in=[
                'can_manage_content',
                'can_view_reports',
            ]
        )
        editor_group.permissions.set(editor_permissions)
        
        # 4. 用户组
        user_group, _ = Group.objects.get_or_create(name='普通用户')
        # 普通用户组默认不分配特殊权限
        
        return {
            'admin': admin_group,
            'manager': manager_group,
            'editor': editor_group,
            'user': user_group,
        }
    
    @staticmethod
    def create_custom_permission(codename, name, content_type):
        """创建自定义权限"""
        permission, created = Permission.objects.get_or_create(
            codename=codename,
            name=name,
            content_type=content_type,
        )
        return permission
    
    @staticmethod
    def assign_user_to_group(user, group_name):
        """将用户分配到组"""
        try:
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
            return True
        except Group.DoesNotExist:
            return False
    
    @staticmethod
    def update_user_role(user, new_role):
        """更新用户角色"""
        from .models import CustomUser
        
        if user.role != new_role:
            user.role = new_role
            user.save(update_fields=['role'])
            
            # 根据角色自动分配组
            group_mapping = {
                CustomUser.UserRole.ADMIN: '超级管理员',
                CustomUser.UserRole.MANAGER: '管理员',
                CustomUser.UserRole.EDITOR: '编辑',
                CustomUser.UserRole.USER: '普通用户',
            }
            
            if new_role in group_mapping:
                # 清除现有组
                user.groups.clear()
                # 分配新组
                PermissionManager.assign_user_to_group(user, group_mapping[new_role])
            
            return True
        return False