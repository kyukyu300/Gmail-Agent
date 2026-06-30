import asyncio
import os
from telegram import Bot
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def send_telegram_message(message: str) -> str:
    """
    텔레그램으로 메시지를 보냅니다.
    
    Args:
        message: 보낼 메시지
    
    Returns:
        성공/실패 메시지
    """
    async def _send():
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
            parse_mode='Markdown'
        )
    
    try:
        asyncio.run(_send())
        return "✅ 텔레그램 메시지 전송 완료"
    except Exception as e:
        return f"❌ 텔레그램 전송 실패: {str(e)}"
