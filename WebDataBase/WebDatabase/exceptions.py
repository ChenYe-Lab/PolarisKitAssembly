from django.http import JsonResponse


class WebDatabaseException(Exception):
    default_error_code = "webdatabase_error"
    default_message = "WebDatabase app request failed"
    default_status_code = 400

    def __init__(self, message=None, error_code=None, status_code=None, details=None):
        self.message = message or self.default_message
        self.error_code = error_code or self.default_error_code
        self.status_code = status_code or self.default_status_code
        self.details = details
        super().__init__(self.message)

    def to_dict(self):
        payload = {
            "success": False,
            "error_code": self.error_code,
            "message": self.message,
        }
        if self.details is not None:
            payload["details"] = self.details
        return payload

    def to_response(self):
        return JsonResponse(self.to_dict(), status=self.status_code)


class WebDatabaseValidationException(WebDatabaseException):
    default_error_code = "validation_error"
    default_message = "Request parameters are invalid"
    default_status_code = 400
    
    def __init__(self,parameter):
        self.default_message = f"Request parameters {parameter} are invalid"


class WebDatabaseNotFoundException(WebDatabaseException):
    default_error_code = "not_found"
    default_message = "Requested resource does not exist"
    default_status_code = 404


class WebDatabasePermissionException(WebDatabaseException):
    default_error_code = "permission_denied"
    default_message = "You do not have permission to perform this action"
    default_status_code = 403


class WebDatabaseConflictException(WebDatabaseException):
    default_error_code = "conflict"
    default_message = "The request conflicts with current data"
    default_status_code = 409


class WebDatabaseServerException(WebDatabaseException):
    default_error_code = "internal_error"
    default_message = "Internal server error"
    default_status_code = 500

class WebDatabasePOSTMethodException(WebDatabaseException):
    default_error_code = "request_error"
    default_message = "Just POST Method"
    default_status_code = 500
    
class WebDatabaseGETMethodException(WebDatabaseException):
    default_error_code = "request_error"
    default_message = "JUST GET Method"
    default_status_code = 500

class WebDatabaseTimeoutException(WebDatabaseException):
    default_error_code = "internal_error"
    default_message = "TIME OUT"
    default_status_code = 500