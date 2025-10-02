import asyncio
from typing import Optional, Union

from lztpay.core import LZTClient
from lztpay.core.models import Currency, InvoiceCreate
from lztpay.exceptions import PaymentNotFoundError
from lztpay.logger import get_logger
from lztpay.storage import MemoryStore

logger = get_logger()


class PaymentManager:
    def __init__(
        self,
        client: LZTClient,
        merchant_id: int,
        url_success: str,
        url_callback: Optional[str] = None,
        ttl_seconds: int = 3600,
    ):
        self.client = client
        self.merchant_id = merchant_id
        self.url_success = url_success
        self.url_callback = url_callback
        self.store = MemoryStore(ttl_seconds=ttl_seconds)
        self._cleanup_task: Optional[asyncio.Task] = None

    async def start_cleanup(self, interval: int = 300) -> None:
        async def cleanup_loop():
            while True:
                await asyncio.sleep(interval)
                await self.store.cleanup_expired()

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info("cleanup task started", interval=interval)

    async def stop_cleanup(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("cleanup task stopped")

    async def create_invoice(
        self,
        payment_id: str,
        amount: float,
        comment: str = "",
        lifetime: int = 3600,
        currency: Union[Currency, str] = Currency.RUB,
        is_test: bool = False,
        additional_data: Optional[str] = None,
    ) -> dict:

        invoice_data = InvoiceCreate(
            currency=currency,
            amount=amount,
            payment_id=payment_id,
            comment=comment or f"Payment {payment_id[:8]}",
            url_success=self.url_success,
            url_callback=self.url_callback,
            merchant_id=self.merchant_id,
            lifetime=lifetime,
            additional_data=additional_data,
            is_test=is_test,
        )

        invoice = await self.client.create_invoice(invoice_data)

        await self.store.put(
            payment_id,
            amount,
            0,
            invoice_id=invoice.invoice_id,
            is_test=is_test,
            additional_data=additional_data,
        )

        logger.info(
            "invoice created",
            payment_id=payment_id,
            invoice_id=invoice.invoice_id,
            amount=amount,
            is_test=is_test,
            url=invoice.url,
        )

        return {
            "payment_id": payment_id,
            "invoice_id": invoice.invoice_id,
            "amount": amount,
            "payment_url": invoice.url,
            "status": invoice.status,
            "expires_at": invoice.expires_at,
            "is_test": is_test,
        }

    async def check_payment(self, payment_id: str) -> Optional[dict]:
        stored = await self.store.get(payment_id)

        if not stored:
            raise PaymentNotFoundError(
                f"payment not found or expired: {payment_id}",
                details={"payment_id": payment_id},
            )

        invoice = await self.client.get_invoice(payment_id=payment_id)

        if invoice.status == "paid":
            await self.store.delete(payment_id)
            logger.info(
                "payment confirmed",
                payment_id=payment_id,
                invoice_id=invoice.invoice_id,
                amount=invoice.amount,
                payer_user_id=invoice.payer_user_id,
            )
            return {
                "payment_id": payment_id,
                "invoice_id": invoice.invoice_id,
                "amount": invoice.amount,
                "payer_user_id": invoice.payer_user_id,
                "paid_date": invoice.paid_date,
                "confirmed": True,
            }

        logger.debug(
            "payment not confirmed yet",
            payment_id=payment_id,
            status=invoice.status,
        )

        return None

    async def get_payment_info(self, payment_id: str) -> Optional[dict]:
        return await self.store.get(payment_id)

    def get_stats(self) -> dict:
        return self.store.get_stats()
