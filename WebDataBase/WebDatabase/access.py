"""Fail-closed session authentication and explicit API write roles."""
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_protect


class ApiAccessMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.path.startswith(('/WebDatabase/', '/LabDatabase/')):
            return None
        # Public account flows are intentionally kept separate from API policy.
        if view_func.__module__ == 'WebDatabase.account' and view_func.__name__ in {
            'login_view', 'register', 'admin_register', 'reset_password',
        }:
            return None
        if view_func.__module__ == 'LabDatabase.admin' and view_func.__name__ in {'login', 'register', 'register_admin'}:
            return None
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated or not user.is_active:
            return JsonResponse({'success': False, 'error_code': 'authentication_required',
                                 'message': 'Login required'}, status=401)
        # Never accept the legacy info dictionary as authentication or identity.
        request.session['info'] = {'uid': user.pk, 'uname': user.uname}
        privileged = user.is_superuser or user.role in {'editor', 'manager', 'admin'}
        function = view_func.__name__.lower()
        mutating_get = function.startswith(('add', 'update', 'delete', 'remove', 'set', 'create', 'save'))
        if request.method in {'GET', 'HEAD', 'OPTIONS'}:
            if mutating_get:
                return JsonResponse({'success': False, 'message': 'Use a write method'}, status=405)
            # Visitor details contain personal information, not public catalog data.
            if 'visitor' in function and not privileged:
                return JsonResponse({'success': False, 'message': 'Editor role required'}, status=403)
            return None
        if not privileged:
            return JsonResponse({'success': False, 'error_code': 'permission_denied',
                                 'message': 'Editor, manager or admin role required'}, status=403)
        # Protect even legacy csrf_exempt views using session authentication.
        protected = csrf_protect(lambda req, *args, **kwargs: None)
        return protected(request, *view_args, **view_kwargs)
