from enum import Enum
from typing import Optional

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


class Balance(BaseModel):
    amount: float
    currency: str


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
