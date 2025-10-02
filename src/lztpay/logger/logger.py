import inspect
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

from colorama import Fore, Style, init

init(autoreset=True)


class ColorizedFormatter(logging.Formatter):
    COLORS = {
        "DEBUG": Fore.CYAN,
        "INFO": Fore.GREEN,
        "WARNING": Fore.YELLOW,
        "ERROR": Fore.RED,
        "CRITICAL": Fore.RED + Style.BRIGHT,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        reset = Style.RESET_ALL

        log_data = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "msg": record.getMessage(),
        }

        if hasattr(record, "module_name") and record.module_name:
            log_data["module"] = record.module_name

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        if record.exc_info:
            log_data["exc"] = self.formatException(record.exc_info)

        json_str = json.dumps(log_data, ensure_ascii=False)
        return f"{color}{json_str}{reset}"


class Logger:
    _instances: Dict[str, "Logger"] = {}

    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(ColorizedFormatter())
            self.logger.addHandler(handler)

        self.logger.propagate = False

    def _log_with_data(self, level: int, msg: str, **kwargs: Any) -> None:
        extra_data = {k: v for k, v in kwargs.items() if v is not None}

        frame = inspect.currentframe()
        if frame and frame.f_back and frame.f_back.f_back:
            caller_frame = frame.f_back.f_back
            module_name = caller_frame.f_globals.get("__name__", "")
            if module_name.startswith("lztpay."):
                module_name = module_name.replace("lztpay.", "")
        else:
            module_name = ""

        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "",
            0,
            msg,
            (),
            None,
        )
        record.module_name = module_name
        if extra_data:
            record.extra_data = extra_data
        self.logger.handle(record)

    def debug(self, msg: str, **kwargs: Any) -> None:
        self._log_with_data(logging.DEBUG, msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        self._log_with_data(logging.INFO, msg, **kwargs)

    def warn(self, msg: str, **kwargs: Any) -> None:
        self._log_with_data(logging.WARNING, msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        self._log_with_data(logging.ERROR, msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any) -> None:
        self._log_with_data(logging.CRITICAL, msg, **kwargs)

    @classmethod
    def get_instance(cls, name: str = "lztpay", level: int = logging.INFO) -> "Logger":
        if name not in cls._instances:
            cls._instances[name] = cls(name, level)
        return cls._instances[name]


def get_logger(name: str = "lztpay", level: int = logging.INFO) -> Logger:
    return Logger.get_instance(name, level)
