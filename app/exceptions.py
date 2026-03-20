from fastapi import HTTPException, status


class DigestSystemException(HTTPException):
    status_code = 500
    detail = ""
    
    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class InvalidTelegramAuthorizationException(DigestSystemException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Invalid Telegram authorization"

class AuthorizationExpiredException(DigestSystemException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Authorization expired"

class InvalidTokenException(DigestSystemException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid token"

class UserNotFoundException(DigestSystemException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "User not found"

class UserNotAuthenticatedException(DigestSystemException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "User not authenticated"
