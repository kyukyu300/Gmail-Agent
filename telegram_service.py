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
    print(f"[Telegram] Preparing to send message (length: {len(message)})")
    
    # Reload env to ensure latest values are used
    load_dotenv()
    token = os.getenv('TELEGRAM_BOT_TOKEN') or TELEGRAM_BOT_TOKEN
    chat_id = os.getenv('TELEGRAM_CHAT_ID') or TELEGRAM_CHAT_ID
    
    token_display = f"{token[:10]}...{token[-5:]}" if token else "None"
    print(f"[Telegram] Bot Token: {token_display}")
    print(f"[Telegram] Chat ID: {chat_id}")
    
    async def _send():
        bot = Bot(token=token)
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown'
        )
    
    try:
        asyncio.run(_send())
        print("[Telegram] Message sent successfully!")
        return "✅ 텔레그램 메시지 전송 완료"
    except Exception as e:
        print(f"[Telegram] Error sending message: {str(e)}")
        return f"❌ 텔레그램 전송 실패: {str(e)}"
