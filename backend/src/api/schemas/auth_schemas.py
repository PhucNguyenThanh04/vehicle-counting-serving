import re
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginPayload(BaseModel):
    identifier: str #username hay email dieu duoc
    password: str


class ResetPassRequest(BaseModel):
    email: EmailStr


class ResetPassConfirm(BaseModel):
    otp: str
    new_pass: str

    @field_validator("new_pass")
    @classmethod
    def validation_password(cls, v: str) -> str:
        if v and len(v) < 8:
            raise ValueError("mat khau phai nhieu hon 8 ky tu")
        if v and not all([
            re.search(r"[A-Z]", v),
            re.search(r"[a-z]", v),
            re.search(r"[0-9]", v),
            re.search(r"[^a-zA-Z0-9]", v)
        ]):
            raise ValueError("mat khau phai co it nhat 1 chu hoa, 1 chu thuong, 1 chu so va 1 ky tu dac biet")
        return v

class CreateAuth(BaseModel):
    username: str = Field(..., min_length=5, max_length=50)
    email: EmailStr
    fullname: str = Field(..., min_length=4, max_length=200)
    phone: str | None
    password: str

    @field_validator("username")
    @classmethod
    def username_must_be_valid(cls, v: str ) -> str:
        if v and len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if v and not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username must contain only letters, numbers, and underscores")
        return v

    @field_validator("password")
    @classmethod
    def validation_password(cls, v: str) -> str:
        if v and len(v) < 8:
            raise ValueError("mat khau phai nhieu hon 8 ky tu")
        if v and not all([
            re.search(r"[A-Z]", v),
            re.search(r"[a-z]", v),
            re.search(r"[0-9]", v),
            re.search(r"[^a-zA-Z0-9]", v)
        ]):
            raise ValueError("mat khau phai co it nhat 1 chu hoa, 1 chu thuong, 1 chu so va 1 ky tu dac biet")
        return v

    @field_validator("phone")
    @classmethod
    def phone_must_be_valid(cls, v: str | None) -> str | None:
        if v and not re.match(r"^\+?[0-9]{9,15}$", v):
            raise ValueError("Invalid phone number format")
        return v


class UpdateAuth(BaseModel):
    username: str | None = Field(..., min_length=5, max_length=50)
    email: EmailStr | None
    fullname: str | None = Field(..., min_length=4, max_length=200)
    phone: str | None

    @field_validator("username")
    @classmethod
    def username_must_be_valid(cls, v: str | None) -> str | None:
        if v and len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if v and not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Username must contain only letters, numbers, and underscores")
        return v

    @field_validator("phone")
    @classmethod
    def phone_must_be_valid(cls, v: str | None) -> str | None:
        if v and not re.match(r"^\+?[0-9]{9,15}$", v):
            raise ValueError("Invalid phone number format")
        return v


class ResponseAuth(BaseModel):
    id: UUID
    username: str
    email:str
    phone: str
    is_active : bool
    created_at: datetime
    updated_at: datetime | None








