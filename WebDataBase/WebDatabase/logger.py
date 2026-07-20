import logging
import json
from datetime import datetime
from django.conf import settings

class DjangoLogger:
    """Django 日志工具类"""
    
    def __init__(self, name=None):
        self.logger = logging.getLogger(name or __name__)
        
    @staticmethod
    def get_logger(name=None):
        """获取日志记录器"""
        return logging.getLogger(name or __name__)
    
    def request_log(self, request, response, duration_ms):
        """记录请求日志"""
        try:
            user = request.user.username if request.user.is_authenticated else 'anonymous'
            
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'type': 'request',
                'request_id': getattr(request, 'request_id', 'unknown'),
                'user': user,
                'ip': self._get_client_ip(request),
                'method': request.method,
                'path': request.path,
                'status_code': response.status_code,
                'duration_ms': duration_ms,
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'query_params': dict(request.GET),
            }
            
            # 记录敏感信息时要小心
            if settings.DEBUG:
                log_data['post_data'] = self._sanitize_data(request.POST.dict())
            
            self.logger.info(json.dumps(log_data))
            
        except Exception as e:
            self.logger.error(f"记录请求日志失败: {e}")
    
    def business_log(self, action, user_id, details, result='success'):
        """记录业务日志"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'type': 'business',
            'action': action,
            'user_id': user_id,
            'details': details,
            'result': result,
        }
        
        self.logger.info(json.dumps(log_data))
    
    def error_log(self, error, request=None, extra=None):
        """记录错误日志"""
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'level': 'ERROR',
            'type': 'error',
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': self._get_traceback(),
            'extra': extra or {},
        }
        
        if request:
            error_data.update({
                'request_path': request.path,
                'request_method': request.method,
                'user': getattr(request.user, 'username', 'anonymous'),
            })
        
        self.logger.error(json.dumps(error_data))
    
    def _get_client_ip(self, request):
        """获取客户端IP"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _sanitize_data(self, data):
        """清理敏感数据"""
        sensitive_fields = ['password', 'token', 'secret', 'key', 'credit_card']
        sanitized = data.copy()
        
        for field in sensitive_fields:
            if field in sanitized:
                sanitized[field] = '***REDACTED***'
        
        return sanitized
    
    def _get_traceback(self):
        """获取堆栈跟踪"""
        import traceback
        return traceback.format_exc()

# 全局日志实例
request_logger = DjangoLogger('django.request')
business_logger = DjangoLogger('WebDatabase.business')
error_logger = DjangoLogger('django.error')