class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details=None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class UnauthorizedError(AppError):
    def __init__(self, message="Authentication required"):
        super().__init__("UNAUTHORIZED", message, 401)


class ForbiddenError(AppError):
    def __init__(self, message="Access denied"):
        super().__init__("FORBIDDEN", message, 403)


class NotFoundError(AppError):
    def __init__(self, message="Resource not found"):
        super().__init__("NOT_FOUND", message, 404)


class ConflictError(AppError):
    def __init__(self, message="Resource conflict"):
        super().__init__("CONFLICT", message, 409)
