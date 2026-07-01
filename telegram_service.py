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
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'
            )
        except Exception as e:
            if "parse entities" in str(e).lower():
                print("[Telegram] Markdown parsing failed, retrying in plain text...")
                await bot.send_message(
                    chat_id=chat_id,
                    text=message
                )
            else:
                raise e
    
    try:
        asyncio.run(_send())
        print("[Telegram] Message sent successfully!")
        return "✅ 텔레그램 메시지 전송 완료"
    except Exception as e:
        print(f"[Telegram] Error sending message: {str(e)}")
        return f"❌ 텔레그램 전송 실패: {str(e)}"


def send_telegram_poll(question: str, options: list, correct_option_id: int, explanation: str) -> str:
    """
    텔레그램 퀴즈 투표(Quiz Poll)를 발송합니다.
    (질문: 300자 제한, 보기: 100자 제한, 해설: 200자 제한 자동 Truncate 처리)
    """
    # Safe limits truncation
    q_safe = question if len(question) <= 300 else question[:297] + "..."
    opts_safe = [opt if len(opt) <= 100 else opt[:97] + "..." for opt in options]
    exp_safe = explanation if not explanation or len(explanation) <= 200 else explanation[:197] + "..."

    async def _send():
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        msg = await bot.send_poll(
            chat_id=TELEGRAM_CHAT_ID,
            question=q_safe,
            options=opts_safe,
            type='quiz',
            correct_option_id=correct_option_id,
            explanation=exp_safe,
            is_anonymous=False
        )
        return msg.poll.id

    try:
        poll_id = asyncio.run(_send())
        print(f"[Telegram] Quiz poll sent successfully. Poll ID: {poll_id}")
        return poll_id
    except Exception as e:
        print(f"[Telegram] Error sending quiz poll: {str(e)}")
        return ""


def get_poll_votes() -> dict:
    """
    최근 텔레그램 업데이트를 조회하여 사용자가 투표한 퀴즈 정답 결과를 가져옵니다.
    반환값: { "poll_id": selected_option_id (int) }
    """
    async def _get():
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        updates = await bot.get_updates(limit=100)
        votes = {}
        for u in updates:
            if u.poll_answer:
                pa = u.poll_answer
                if pa.option_ids:
                    votes[pa.poll_id] = pa.option_ids[0]
        return votes

    try:
        votes = asyncio.run(_get())
        print(f"[Telegram] Retrieved {len(votes)} poll votes from updates.")
        return votes
    except Exception as e:
        print(f"[Telegram] Error retrieving poll votes: {str(e)}")
        return {}
