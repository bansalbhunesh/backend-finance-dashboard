from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RoleEnum(str, Enum):
    viewer = "viewer"
    analyst = "analyst"
    admin = "admin"


class TransactionTypeEnum(str, Enum):
    income = "income"
    expense = "expense"


# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: int
    role: RoleEnum


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


# --- Users ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(default="", max_length=255)
    role: RoleEnum = RoleEnum.viewer
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = Field(default=None, max_length=255)
    role: RoleEnum | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    full_name: str
    role: RoleEnum
    is_active: bool
    created_at: datetime


# --- Financial records ---
class FinancialRecordBase(BaseModel):
    amount: Decimal = Field(gt=0, decimal_places=2, max_digits=14)
    type: TransactionTypeEnum
    category: str = Field(min_length=1, max_length=128)
    occurred_at: datetime
    notes: str | None = Field(default=None, max_length=2000)

    @field_validator("category")
    @classmethod
    def category_strip(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("category cannot be empty")
        return s


class FinancialRecordCreate(FinancialRecordBase):
    pass


class FinancialRecordUpdate(BaseModel):
    amount: Decimal | None = Field(default=None, gt=0, decimal_places=2, max_digits=14)
    type: TransactionTypeEnum | None = None
    category: str | None = Field(default=None, min_length=1, max_length=128)
    occurred_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)


class FinancialRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: Decimal
    type: TransactionTypeEnum
    category: str
    occurred_at: datetime
    notes: str | None
    created_by_user_id: int | None
    created_at: datetime


# --- Dashboard ---
class CategoryTotal(BaseModel):
    category: str
    type: TransactionTypeEnum
    total: Decimal


class RecentActivityItem(BaseModel):
    id: int
    amount: Decimal
    type: TransactionTypeEnum
    category: str
    occurred_at: datetime
    notes: str | None


class TrendPoint(BaseModel):
    period: str
    income: Decimal
    expense: Decimal
    net: Decimal


class DashboardSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_balance: Decimal
    record_count: int


class DashboardFull(BaseModel):
    summary: DashboardSummary
    category_totals: list[CategoryTotal]
    recent_activity: list[RecentActivityItem]
    monthly_trends: list[TrendPoint]
