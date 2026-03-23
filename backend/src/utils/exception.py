from fastapi import HTTPException, status

class CustomHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)

def raise_not_found(detail: str = "Resource not found"):
    raise CustomHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

def raise_bad_request(detail: str = "Bad request"):
    raise CustomHTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)



