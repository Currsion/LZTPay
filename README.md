# LZTPay

Библиотека для приема платежей через Lolz.live

## Установка

```bash
pip install -e .
```

## Быстрый старт

### Настройка

1. Создайте мерчанта на https://lzt.market/merchants/
2. Получите `merchant_id` и API `token` от маркета

### Пример использования

```python
import asyncio
from lztpay import LZTClient, PaymentManager, Currency

async def main():
    async with LZTClient(token="your_token") as client:
        manager = PaymentManager(
            client,
            merchant_id=123456,
            url_success="https://yoursite.com/success"
        )

        payment = await manager.create_payment(
            amount=100.0,
            comment="Подписка Premium",
            currency=Currency.RUB,
            lifetime=3600,
            is_test=True
        )

        print(f"Ссылка на оплату: {payment['payment_url']}")

        result = await manager.check_payment(payment["payment_id"])
        if result:
            print(f"Оплачено: {result['amount']} RUB")
            print(f"Плательщик: {result['payer_user_id']}")

asyncio.run(main())
```

## Основные методы

### Создание платежа

```python
payment = await manager.create_payment(
    amount=100.0,          # сумма
    comment="Описание",    # описание
    currency=Currency.USD, # валюта
    lifetime=1800,         # время жизни (сек)
    is_test=False          # тестовый режим
)
```

Возвращает:
```python
{
    "payment_id": UUID,       # ID для проверки
    "invoice_id": int,        # ID в LZT
    "payment_url": str,       # ссылка для оплаты
    "amount": float,
    "status": "not_paid",
    "expires_at": int,
    "is_test": bool
}
```

### Проверка оплаты

```python
result = await manager.check_payment(payment_id)
```

Если оплачено:
```python
{
    "payment_id": UUID,
    "invoice_id": int,
    "amount": float,
    "payer_user_id": int,     # кто оплатил
    "paid_date": int,
    "confirmed": True
}
```

## Валюты

```python
Currency.RUB  # рубль
Currency.USD  # доллар
Currency.EUR  # евро
Currency.UAH  # гривна
Currency.KZT  # тенге
Currency.BYN  # белорусский рубль
Currency.GBP  # фунт
Currency.CNY  # юань
Currency.TRY  # лира
Currency.JPY  # иена
Currency.BRL  # реал
```

## Дополнительно

### Автоочистка

```python
await manager.start_cleanup(interval=300)
await manager.stop_cleanup()
```

### Webhook

```python
manager = PaymentManager(
    client,
    merchant_id=123456,
    url_success="https://example.com/success",
    url_callback="https://example.com/webhook"
)
```

### Логи

```python
from lztpay import get_logger

logger = get_logger()
logger.info("payment created", payment_id="123", amount=100.0)
```

## Примеры

```bash
python examples/basic_usage.py
```

## Структура

```
lztpay/
├── core/              # API клиент
├── decorators/        # retry, timing, validation
├── exceptions/        # ошибки
├── logger/            # логирование
├── storage/           # хранилище
└── payment_manager.py # менеджер платежей
```

## Лицензия

MIT
