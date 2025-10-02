from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Currency(str, Enum):
    RUB = "rub"
    UAH = "uah"
    KZT = "kzt"
    BYN = "byn"
    USD = "usd"
    EUR = "eur"
    GBP = "gbp"
    CNY = "cny"
    TRY = "try"
    JPY = "jpy"
    BRL = "brl"


class TransferRequest(BaseModel):
    user_id: int
    amount: float = Field(gt=0)
    comment: str
    currency: str = "rub"


class TransferResponse(BaseModel):
    transaction_id: int
    status: str
    amount: float
    user_id: int
    comment: str


class PaymentHistoryItem(BaseModel):
    id: int
    type: str
    amount: float
    user_id: Optional[int] = None
    username: Optional[str] = None
    comment: Optional[str] = None
    timestamp: datetime


class PaymentHistory(BaseModel):
    payments: List[PaymentHistoryItem]
    total: int


class Balance(BaseModel):
    amount: float
    currency: str


class PaymentStatus(BaseModel):
    found: bool
    amount: Optional[float] = None
    payment_id: Optional[UUID] = None
    user_id: Optional[int] = None


class InvoiceCreate(BaseModel):
    currency: Currency = Currency.RUB
    amount: float = Field(gt=0)
    payment_id: str
    comment: str
    url_success: str
    url_callback: Optional[str] = None
    merchant_id: int
    lifetime: int = Field(default=3600, ge=300, le=43200)
    additional_data: Optional[str] = None
    is_test: bool = False


class Invoice(BaseModel):
    invoice_id: int
    payment_id: str
    merchant_id: int
    user_id: int
    amount: float
    comment: str
    status: str
    url: str
    url_success: str
    url_callback: Optional[str] = None
    additional_data: Optional[str] = None
    invoice_date: int
    expires_at: int
    paid_date: Optional[int] = None
    payer_user_id: Optional[int] = None
    is_test: bool
    resend_attempts: int = 0


class InvoiceResponse(BaseModel):
    invoice: Invoice
