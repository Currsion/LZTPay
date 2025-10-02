import asyncio

from lztpay import Currency, LZTClient, PaymentManager, get_logger

logger = get_logger()


async def main():
    TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzUxMiJ9.eyJzdWIiOjk1NDY2MzgsImlzcyI6Imx6dCIsImlhdCI6MTc1OTQxNjMzMywianRpIjoiODU5MDQ5Iiwic2NvcGUiOiJiYXNpYyByZWFkIHBvc3QgY29udmVyc2F0ZSBwYXltZW50IGludm9pY2UgY2hhdGJveCBtYXJrZXQiLCJleHAiOjE3NzQ5NjgzMzN9.Igh3Puhj9-KwKoqIqMvuozIn6B-18qR_xk-q7s95ESGgBZWvptdeHVMOthzJAajWdUudyC02PAMA03p3QRDJyFZvXcbb5XeJqr9rl5lABvXDrmNktES9IbG97sxt2-RK6I9eIOHw8MeJO77WLXVXb61Acv1NAlGwaq36YFcJ5v0" #токен от маркета
    MERCHANT_ID = 1433 #merchantid 

    async with LZTClient(token=TOKEN) as client:
        balance = await client.get_merchant_balance(MERCHANT_ID)
        logger.info("merchant balance", amount=balance.amount, currency=balance.currency)

        manager = PaymentManager(
            client,
            merchant_id=MERCHANT_ID,
            url_success="https://lolz.live/currison/",
            # url_callback="https://example.com/webhook",  # webhook для уведомлений об оплате
            ttl_seconds=1800,  # время хранения платежа в памяти (секунды)
        )

        # запуск автоматической очистки устаревших платежей
        await manager.start_cleanup(interval=300)

        payment = await manager.create_invoice(
            # ОБЯЗАТЕЛЬНЫЕ ПАРАМЕТРЫ
            amount=1.0,  # сумма платежа

            # ОПЦИОНАЛЬНЫЕ ПАРАМЕТРЫ
            comment="Premium subscription",  # коментарий к платежу
            lifetime=3600,  # время жизни invoice в секундах (300-43200, default: 3600)
            currency=Currency.RUB,  # валюта (RUB, USD, EUR, UAH, KZT, BYN, GBP, CNY, TRY, JPY, BRL)
            is_test=True,  # тестовый платеж (не списывает реальные деньги)
        )

        logger.info(
            "invoice created",
            payment_id=str(payment["payment_id"]),
            invoice_id=payment["invoice_id"],
            payment_url=payment["payment_url"],
            expires_at=payment["expires_at"],
        )

        print(f"\nПерейди по ссылке для оплаты:\n{payment['payment_url']}\n")

        for attempt in range(30):
            await asyncio.sleep(5)

            result = await manager.check_payment(payment["payment_id"])

            if result:
                logger.info(
                    "payment confirmed, crediting balance",
                    amount=result["amount"],
                    payer_user_id=result["payer_user_id"],
                )
                break
        else:
            logger.warn("payment timeout", payment_id=str(payment["payment_id"]))

        stats = manager.get_stats()
        logger.info("payment stats", **stats)

        await manager.stop_cleanup()


if __name__ == "__main__":
    asyncio.run(main())
