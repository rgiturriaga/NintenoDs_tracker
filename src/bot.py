"""Telegram bot entry point.

Commands available in chat:
    /start          - Start the price monitor in the background.
    /stop           - Stop the monitor (finishes the current scan first).
    /status         - Show current state and active configuration.
    /setprice <n>   - Change the maximum price threshold on the fly.

Security: all commands are restricted to the TELEGRAM_CHAT_ID set in the environment.
Any other chat ID is silently ignored.
"""

import os
import logging
import threading
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from main import run_monitor_loop

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class MonitorController:
    """Manages the lifecycle of the price monitor background thread."""

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self.config: dict = {
            "target_url": os.getenv(
                "TARGET_URL",
                "https://listado.mercadolibre.com.mx/nintendo-ds-lite",
            ),
            "max_price": self._parse_float("MAX_PRICE", 1000.0),
            "check_interval": self._parse_int("CHECK_INTERVAL", 3600),
        }

    @staticmethod
    def _parse_float(key: str, default: float) -> float:
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid {key} in environment, using default {default}")
            return default

    @staticmethod
    def _parse_int(key: str, default: int) -> int:
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid {key} in environment, using default {default}")
            return default

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> bool:
        """Spawns the monitor thread. Returns False if already running."""
        if self.is_running:
            return False
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=run_monitor_loop,
            args=(self._stop_event, self.config),
            daemon=True,
            name="monitor-thread",
        )
        self._thread.start()
        logger.info("Monitor thread started.")
        return True

    def stop(self) -> bool:
        """Signals the monitor to stop after the current scan. Returns False if not running."""
        if not self.is_running:
            return False
        self._stop_event.set()
        logger.info("Stop signal sent to monitor thread.")
        return True

    def set_max_price(self, price: float) -> None:
        """Updates the price threshold. Takes effect on the next scan cycle."""
        self.config["max_price"] = price


# Single shared controller instance for all bot handlers
_controller = MonitorController()


def _is_authorized(update: Update) -> bool:
    """Ensures the command comes from the configured chat only."""
    allowed_id = os.getenv("TELEGRAM_CHAT_ID")
    return allowed_id is not None and str(update.effective_chat.id) == allowed_id


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Starts the price monitor."""
    if not _is_authorized(update):
        return

    if _controller.start():
        cfg = _controller.config
        await update.message.reply_text(
            f"Monitor started.\n"
            f"Max price: ${cfg['max_price']:,.2f}\n"
            f"Check interval: {cfg['check_interval']}s\n"
            f"URL: {cfg['target_url']}"
        )
    else:
        await update.message.reply_text("The monitor is already running.")


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stops the price monitor."""
    if not _is_authorized(update):
        return

    if _controller.stop():
        await update.message.reply_text(
            "Stop signal sent. The monitor will finish its current scan and then halt."
        )
    else:
        await update.message.reply_text("The monitor is not running.")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reports the current state and configuration."""
    if not _is_authorized(update):
        return

    state = "Running" if _controller.is_running else "Stopped"
    cfg = _controller.config
    await update.message.reply_text(
        f"<b>Monitor Status</b>\n\n"
        f"State: {state}\n"
        f"Max price: ${cfg['max_price']:,.2f}\n"
        f"Check interval: {cfg['check_interval']}s\n"
        f"URL: {cfg['target_url']}",
        parse_mode="HTML",
    )


async def cmd_setprice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Changes the maximum price threshold. Usage: /setprice 800"""
    if not _is_authorized(update):
        return

    if not context.args:
        await update.message.reply_text("Usage: /setprice <value>  e.g. /setprice 800")
        return

    try:
        new_price = float(context.args[0])
        if new_price <= 0:
            raise ValueError("Price must be positive.")
        _controller.set_max_price(new_price)
        await update.message.reply_text(
            f"Max price updated to ${new_price:,.2f}. Takes effect on the next scan."
        )
    except ValueError as e:
        await update.message.reply_text(f"Invalid value: {e}\nExample: /setprice 800")


def main() -> None:
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN not found in environment variables.")

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("setprice", cmd_setprice))

    logger.info("Telegram bot started with polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
