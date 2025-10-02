from typing import Any, Dict, Optional

import httpx

from lztpay.decorators import measure_time, retry_on_error
from lztpay.exceptions import AuthError, NetworkError
from lztpay.logger import get_logger
from lztpay.core.models import Balance, Invoice, InvoiceCreate, InvoiceResponse

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

            return response.json()

        except httpx.RequestError as e:
            logger.error("network request failed", error=str(e), endpoint=endpoint)
            raise NetworkError(f"network error: {str(e)}")

    async def get_merchant_balance(self, merchant_id: int) -> Balance:
        data = await self._request("GET", f"/balance/exchange?merchant_id={merchant_id}")
        balance_data = data.get("to", {}).get("balance", {})
        return Balance(amount=float(balance_data.get("balance", "0")), currency="rub")

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
