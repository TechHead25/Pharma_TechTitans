from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ===== USER SCHEMAS =====
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str
    confirm_password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    is_admin: bool
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class RegisterResponse(BaseModel):
    message: str
    requires_verification: bool
    email: str
    dev_verification_code: Optional[str] = None


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


# ===== VCF RECORD SCHEMAS =====
class VCFRecordCreate(BaseModel):
    filename: str
    analyzed_drugs: str  # Comma-separated
    vcf_content: Optional[str] = None
    analysis_result: str  # JSON string
    phenotypes: str  # JSON string


class VCFRecordResponse(BaseModel):
    id: str
    user_id: int
    username: str
    filename: str
    analyzed_drugs: str
    status: str
    uploaded_at: datetime
    analyzed_at: Optional[datetime]

    class Config:
        from_attributes = True


class VCFRecordDetailResponse(VCFRecordResponse):
    analysis_result: Optional[str]
    phenotypes: Optional[str]


# ===== ADMIN DASHBOARD SCHEMAS =====
class AdminStats(BaseModel):
    total_users: int
    total_analyses: int
    total_completed: int
    total_failed: int
    most_analyzed_drugs: List[dict]
    recent_analyses: List[VCFRecordResponse]


class AdminUserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    is_admin: bool
    analysis_count: int
    created_at: datetime

    class Config:
        from_attributes = True
