from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx

from ..decorators import measure_time, retry_on_error
from ..exceptions import APIError, AuthError, NetworkError, RateLimitError
from ..logger import get_logger
from .models import Balance, Invoice, InvoiceCreate, InvoiceResponse, PaymentHistory, PaymentHistoryItem

logger = get_logger()


class LZTClient:
    BASE_URL = "https://prod-api.lzt.market"

    def __init__(self, token: str, timeout: int = 300):
        self.token = token
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "LZTClient":
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    @retry_on_error(max_attempts=3)
    @measure_time
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self._client:
            raise RuntimeError("client not initialized, use async with")

        try:
            response = await self._client.request(
                method,
                endpoint,
                params=params,
                json=json,
            )

            if response.status_code == 401:
                raise AuthError("invalid or expired token")

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise RateLimitError(retry_after=retry_after)

            if response.status_code >= 400:
                raise APIError(
                    f"API request failed: {response.status_code}",
                    status_code=response.status_code,
                    response=response.json() if response.content else None,
                )

            return response.json()

        except httpx.RequestError as e:
            logger.error("network request failed", error=str(e), endpoint=endpoint)
            raise NetworkError(f"network error: {str(e)}")

    async def get_balance(self) -> Balance:
        data = await self._request("GET", "/balance")
        return Balance(amount=data["balance"], currency=data.get("currency", "rub"))

    async def transfer_money(
        self,
        user_id: int,
        amount: float,
        comment: str,
        currency: str = "rub",
    ) -> Dict[str, Any]:
        payload = {
            "user_id": user_id,
            "amount": amount,
            "comment": comment,
            "currency": currency,
        }

        logger.info(
            "initiating transfer",
            user_id=user_id,
            amount=amount,
            comment=comment[:50],
        )

        return await self._request("POST", "/balance/transfer", json=payload)

    async def get_payment_history(
        self,
        limit: int = 100,
        offset: int = 0,
        transaction_type: Optional[str] = None,
    ) -> PaymentHistory:
        params: Dict[str, Any] = {"limit": limit, "offset": offset}

        if transaction_type:
            params["type"] = transaction_type

        data = await self._request("GET", "/me/payments", params=params)

        payments = [
            PaymentHistoryItem(
                id=item["id"],
                type=item["type"],
                amount=item["amount"],
                user_id=item.get("user_id"),
                username=item.get("username"),
                comment=item.get("comment"),
                timestamp=item["timestamp"],
            )
            for item in data.get("payments", [])
        ]

        return PaymentHistory(payments=payments, total=data.get("total", len(payments)))

    async def find_payment_by_comment(self, comment: str) -> Optional[PaymentHistoryItem]:
        history = await self.get_payment_history(limit=50)

        for payment in history.payments:
            if payment.comment == comment:
                logger.info(
                    "payment found by comment",
                    payment_id=payment.id,
                    amount=payment.amount,
                    comment=comment[:50],
                )
                return payment

        logger.debug("payment not found", comment=comment[:50])
        return None

    async def create_invoice(self, invoice_data: InvoiceCreate) -> Invoice:
        payload = invoice_data.model_dump(exclude_none=True)

        logger.info(
            "creating invoice",
            payment_id=invoice_data.payment_id,
            amount=invoice_data.amount,
            merchant_id=invoice_data.merchant_id,
        )

        data = await self._request("POST", "/invoice", json=payload)
        response = InvoiceResponse(**data)
        return response.invoice

    async def get_invoice(
        self,
        invoice_id: Optional[int] = None,
        payment_id: Optional[str] = None,
    ) -> Invoice:
        if not invoice_id and not payment_id:
            raise ValueError("either invoice_id or payment_id must be provided")

        params: Dict[str, Any] = {}
        if invoice_id:
            params["invoice_id"] = invoice_id
        if payment_id:
            params["payment_id"] = payment_id

        data = await self._request("GET", "/invoice", params=params)
        response = InvoiceResponse(**data)
        return response.invoice
