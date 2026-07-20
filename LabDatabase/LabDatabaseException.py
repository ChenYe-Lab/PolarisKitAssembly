from django.http import JsonResponse


class LabDatabaseException(Exception):
    default_error_code = "labdatabase_error"
    default_message = "LabDatabase app request failed"
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
    
class LabDatabasePOSTMethodException(LabDatabaseException):
    default_error_code = "request_error"
    default_message = "Just POST Method"
    default_status_code = 500

class LabDatabaseGETMethodException(LabDatabaseException):
    default_error_code = "request_error"
    default_message = "JUST GET Method"
    default_status_code = 500