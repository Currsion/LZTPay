import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from lztpay.logger import get_logger

logger = get_logger()


class MemoryStore:
    def __init__(self, ttl_seconds: int = 3600):
        self._data: Dict[str, Dict[str, Any]] = {}
        self._ttl = ttl_seconds
        self._lock = asyncio.Lock()

    async def put(self, payment_id: str, amount: float, user_id: int, **extra: Any) -> None:
        async with self._lock:
            key = payment_id
            self._data[key] = {
                "payment_id": payment_id,
                "amount": amount,
                "user_id": user_id,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(seconds=self._ttl),
                **extra,
            }
            logger.debug(
                "payment stored",
                payment_id=key,
                amount=amount,
                user_id=user_id,
            )

    async def get(self, payment_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            key = payment_id
            data = self._data.get(key)

            if not data:
                return None

            if datetime.utcnow() > data["expires_at"]:
                del self._data[key]
                logger.debug("payment expired", payment_id=key)
                return None

            return data

    async def delete(self, payment_id: str) -> bool:
        async with self._lock:
            key = payment_id
            if key in self._data:
                del self._data[key]
                logger.debug("payment deleted", payment_id=key)
                return True
            return False

    async def find_by_user(self, user_id: int) -> list[Dict[str, Any]]:
        async with self._lock:
            now = datetime.utcnow()
            results = []

            for key, data in list(self._data.items()):
                if now > data["expires_at"]:
                    del self._data[key]
                    continue

                if data["user_id"] == user_id:
                    results.append(data)

            return results

    async def cleanup_expired(self) -> int:
        async with self._lock:
            now = datetime.utcnow()
            expired_keys = [
                key for key, data in self._data.items() if now > data["expires_at"]
            ]

            for key in expired_keys:
                del self._data[key]

            if expired_keys:
                logger.debug("expired payments cleaned", count=len(expired_keys))

            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_payments": len(self._data),
            "ttl_seconds": self._ttl,
        }
