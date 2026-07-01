import os
import json
import time
import subprocess
from datetime import datetime, timedelta
from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

from google_services import get_recent_emails, get_upcoming_events, create_calendar_event, send_email
from telegram_service import send_telegram_message, send_telegram_poll, get_poll_votes
from news_service import get_top_news
from notice_service import get_university_notices

load_dotenv()

# ──────────────────────────────────────────────
# Pydantic 스키마 정의 (퀴즈용)
# ──────────────────────────────────────────────

class QuizItem(BaseModel):
    question: str
    options: List[str]
    correct_option_id: int
    explanation: str
    category: str  # 'history' 또는 'toeic'


class QuizList(BaseModel):
    quizzes: List[QuizItem]


# ──────────────────────────────────────────────
# Git 자동 커밋 및 푸시 유틸리티
# ──────────────────────────────────────────────

def commit_and_push_db():
    """quiz_db.json 변경사항을 깃허브 레포지토리에 커밋 & 푸시합니다."""
    if not os.path.exists('.git'):
        print("[Git] .git 폴더를 찾을 수 없어 push를 생략합니다.")
        return
        
    try:
        # 깃허브 액션 환경일 경우 사용자 정보 기본 설정
        if os.getenv("GITHUB_ACTIONS"):
            subprocess.run(["git", "--help"], capture_output=True) # Check if git command exists
            subprocess.run(["git", "config", "--local", "user.email", "action@github.com"], check=True)
            subprocess.run(["git", "config", "--local", "user.name", "GitHub Action"], check=True)
            
        subprocess.run(["git", "add", "quiz_db.json"], check=True)
        status = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
        
        if "quiz_db.json" in status.stdout:
            subprocess.run(["git", "commit", "-m", "chore: Update Leitner quiz database [skip ci]"], check=True)
            subprocess.run(["git", "push"], check=True)
            print("[Git] quiz_db.json 변경사항을 성공적으로 GitHub에 푸시하였습니다.")
        else:
            print("[Git] quiz_db.json에 변경된 내용이 없어 커밋을 건너뜁니다.")
    except Exception as e:
        print(f"[Git] 깃허브 푸시 오류 발생: {e}")


# ──────────────────────────────────────────────
# 메인 실행 함수
# ──────────────────────────────────────────────

def run_morning_briefing():
    """아침 브리핑 에이전트 실행 (강의계획서 파싱, 공지사항 스크랩, Leitner Spaced Repetition 반영)"""
    print("🌅 아침 브리핑 에이전트 구동 중...\n")
    
    # Client 객체 생성
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    
    # 1. 학교 공지사항 수집
    notices = get_university_notices()
    notices_text = "📢 [학교 공지사항 목록]\n"
    if notices:
        for idx, n in enumerate(notices):
            notices_text += f"{idx+1}. [{n['date']}] {n['title']} (링크: {n['link']})\n"
    else:
        notices_text += "- 새로 등록된 공지사항이 없거나 불러올 수 없습니다.\n"
        
    # 2. Leitner Spaced Repetition 채점 처리 및 복습 관리
    db_file = "quiz_db.json"
    if os.path.exists(db_file):
        try:
            with open(db_file, "r", encoding="utf-8") as f:
                quiz_db = json.load(f)
        except Exception:
            quiz_db = {"sent_polls": [], "spaced_repetition_pool": []}
    else:
        quiz_db = {"sent_polls": [], "spaced_repetition_pool": []}

    if "sent_polls" not in quiz_db:
        quiz_db["sent_polls"] = []
    if "spaced_repetition_pool" not in quiz_db:
        quiz_db["spaced_repetition_pool"] = []

    # 전날 보낸 투표 결과 가져오기
    print("[Leitner] 전날 보낸 투표 결과 채점 조회 중...")
    votes = get_poll_votes()
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    processed_count = 0
    
    for p in quiz_db["sent_polls"]:
        poll_id = p.get("poll_id")
        correct_id = p.get("correct_option_id")
        box = p.get("box", 1)
        
        # 기본값 설정
        p["last_asked"] = today_str
        
        # 투표 정보가 매칭되는 경우 정오답 처리
        if poll_id in votes:
            user_choice = votes[poll_id]
            if user_choice == correct_id:
                # 정답 -> Box 한 단계 승급 (최대 3번)
                p["box"] = min(3, box + 1)
                print(f"[Leitner] 퀴즈 정답! (Poll ID: {poll_id}) Box: {box} -> {p['box']}")
            else:
                # 오답 -> Box 1로 초기화 (재학습)
                p["box"] = 1
                print(f"[Leitner] 퀴즈 오답! (Poll ID: {poll_id}) Box: {box} -> 1")
            
            # 다음 질문일 계산
            interval = 1 if p["box"] == 1 else (3 if p["box"] == 2 else 7)
            p["next_ask"] = (datetime.now() + timedelta(days=interval)).strftime("%Y-%m-%d")
            
        else:
            # 투표하지 않고 넘어간 경우 -> 오답 처리와 동일하게 Box 1로 복습 스케줄 지정
            p["box"] = 1
            p["next_ask"] = today_str  # 오늘 또는 즉시 다시 물어보도록 스케줄링
            print(f"[Leitner] 퀴즈 참여 없음 (Poll ID: {poll_id}) Box 1 복습 지정")
            
        quiz_db["spaced_repetition_pool"].append(p)
        processed_count += 1
        
    print(f"[Leitner] 총 {processed_count}개의 전날 퀴즈 채점 완료.")
    quiz_db["sent_polls"] = []  # 보낸 퀴즈 목록 초기화

    # 오늘 출제해야 할 오답 복습 문제 추출
    due_items = [q for q in quiz_db["spaced_repetition_pool"] if q.get("next_ask", "1970-01-01") <= today_str]
    
    due_history = [q for q in due_items if q.get("category") == "history"]
    due_toeic = [q for q in due_items if q.get("category") == "toeic"]
    
    # 하루 출제 개수 제한 (각각 최대 5개)
    due_history = due_history[:5]
    due_toeic = due_toeic[:5]
    
    H_needed = 5 - len(due_history)
    T_needed = 5 - len(due_toeic)
    
    print(f"[Leitner] 복습 대기 퀴즈: 한국사 {len(due_history)}개, 토익 {len(due_toeic)}개")
    print(f"[Leitner] 신규 출제 필요: 한국사 {H_needed}개, 토익 {T_needed}개")

    # 3. 신규 퀴즈 생성 호출 (Gemini JSON 구조 활용)
    new_items = []
    if H_needed > 0 or T_needed > 0:
        print(f"[Gemini] {H_needed}개의 한능검 문제와 {T_needed}개의 토익 문제 신규 생성 중...")
        prompt_quiz = f"""
        실제 한국사능력검정시험(한능검) 심화(1급) 수준의 고품질 기출/개념 문제 {H_needed}개와
        실제 토익(TOEIC) RC Part 5 형식의 실전형 4지선다 문제 {T_needed}개를 생성해주세요.
        
        작성 규칙:
        1. 한능검 문제 ('history' 카테고리):
           - 단순 암기식이 아니어야 하며, 역사적 사료 구절, 가상의 대화, 인물이나 연표 구절 등([사료] 또는 [보기 지문])을 반드시 질문(question)에 3줄 이상 상세히 포함해야 합니다.
           - options는 반드시 정확히 4개여야 합니다.
           - correct_option_id는 0~3 사이의 정답 인덱스여야 합니다.
           - explanation은 정답의 역사적 근거를 설명하여 200자 이하로 작성해야 합니다.
           
        2. 토익 문제 ('toeic' 카테고리):
           - 실제 토익 실전 모의고사 수준의 문법/어휘 변별력을 갖춰야 합니다.
           - options는 반드시 정확히 4개여야 합니다.
           - correct_option_id는 0~3 사이의 정답 인덱스여야 합니다.
           - explanation은 정답의 근거를 명확하게 설명하여 200자 이하로 작성해야 합니다.
        """
        
        for attempt in range(3):
            try:
                quiz_response = client.models.generate_content(
                    model='gemini-3.1-flash-lite',
                    contents=prompt_quiz,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=QuizList
                    )
                )
                raw_data = json.loads(quiz_response.text)
                raw_new_items = raw_data.get("quizzes", [])
                for item in raw_new_items:
                    new_items.append({
                        "question": item.get("question"),
                        "options": item.get("options"),
                        "correct_option_id": item.get("correct_option_id"),
                        "explanation": item.get("explanation"),
                        "category": item.get("category"),
                        "box": 1,
                        "last_asked": today_str,
                        "next_ask": today_str
                    })
                break
            except Exception as e:
                print(f"[Gemini] 퀴즈 생성 시도 {attempt+1}/3 실패: {e}")
                time.sleep(3)

    # 전체 출제 퀴즈 10개 병합
    all_quizzes = due_history + due_toeic + new_items
    # 10개가 안 맞을 경우 예외 방지를 위해 슬라이싱
    all_quizzes = all_quizzes[:10]

    # 4. 아침 종합 텍스트 브리핑 생성
    tools = [
        get_recent_emails,
        get_upcoming_events,
        create_calendar_event,
        get_top_news,
        send_email
    ]
    
    today_korean = datetime.now().strftime("%Y년 %m월 %d일 %A")
    prompt_briefing = f"""
    오늘은 {today_korean}입니다.
    
    다음 자료를 참고하여 오늘 아침 업무(이메일 확인, 일정 확인 및 등록, 뉴스 메일 발송)를 처리해주세요.
    
    [학교 공지사항 자료]
    {notices_text}
    
    업무 수행 세부 지침:
    1. get_recent_emails를 통해 이메일을 요약하고, 중요 일정 정보(과제 마감일, 시험 등)를 발견하면 create_calendar_event로 Google Calendar에 등록하세요.
    2. 제공된 [학교 공지사항 자료]를 읽고 중요 학사 일정/장학 공지가 있다면 역시 create_calendar_event로 등록하세요.
    3. get_top_news로 뉴스 10건을 조회한 후 분야별(종합, IT/테크, 경제)로 나누어 깔끔한 HTML 형식의 메일을 발송하세요(send_email).
    4. 최종적으로 사용자에게 보낼 텔레그램용 아침 종합 브리핑 텍스트를 정교하게 요약하여 한글로 응답하세요.
       - 오늘 할 일, 이번 주 일정, 최근 도착한 중요 메일의 요약 정보 제공
       - '📢 학교 새 공지사항' 섹션을 단락으로 포함하여 주요 공지의 제목과 하이퍼링크(제공된 링크 적용) 요약 제공
       - 뉴스 10건의 분야별 핵심 헤드라인도 하단에 요약하여 하나의 이쁜 메시지로 포맷팅
       - (주의) 텍스트 브리핑 안에는 퀴즈 섹션을 포함하지 마세요. 퀴즈는 파이썬에서 별도 Poll로 자동 발송됩니다.
    """
    
    briefing_text = ""
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=prompt_briefing,
                config=types.GenerateContentConfig(
                    system_instruction="""
                    당신은 대학생의 하루를 비서처럼 도와주는 최첨단 스마트 어시스턴트입니다.
                    풍부한 이모지 사용, 레이아웃 정돈, 명확한 가독성을 항상 준수하여 텔레그램 메시지를 구성하십시오.
                    """,
                    tools=tools
                )
            )
            briefing_text = response.text
            break
        except Exception as e:
            if "503" in str(e) and attempt < 2:
                print(f"⚠️ 503 과부하 발생. 5초 후 재시도... (시도 {attempt+1}/3)")
                time.sleep(5)
                continue
            else:
                print(f"❌ 아침 브리핑 생성 실패: {e}")
                briefing_text = "🌅 오늘 아침 브리핑 요약본을 생성하는 도중 오류가 발생했습니다. 서비스 연결 상태를 확인해 주세요."
                break

    # 5. 텔레그램 종합 브리핑 텍스트 발송
    send_telegram_message(briefing_text)
    time.sleep(2) # 메세지 순서 꼬임 방지 버퍼
    
    # 6. 10개 퀴즈 투표(Quiz Poll) 발송 및 DB 기록
    active_polls = []
    
    print("[Telegram] 10개 퀴즈 투표 발송 시작...")
    for idx, q in enumerate(all_quizzes):
        cat_tag = "한능검 심화 📝" if q["category"] == "history" else "TOEIC RC Part 5 📝"
        box_tag = f" (복습 ⭐ Box {q.get('box', 1)})" if q.get("next_ask") != today_str else ""
        
        question_title = f"[{idx+1}/10] {cat_tag}{box_tag}\n\n{q['question']}"
        
        poll_id = send_telegram_poll(
            question=question_title,
            options=q["options"],
            correct_option_id=q["correct_option_id"],
            explanation=q["explanation"]
        )
        
        if poll_id:
            active_polls.append({
                "poll_id": poll_id,
                "question": q["question"],
                "options": q["options"],
                "correct_option_id": q["correct_option_id"],
                "explanation": q["explanation"],
                "category": q["category"],
                "box": q.get("box", 1),
                "last_asked": today_str,
                "next_ask": q.get("next_ask")
            })
            time.sleep(1) # Telegram API flood limit 방지
            
    # 7. 사용한 퀴즈를 복습 대기열에서 제거하고 현재 활성화된 Poll 저장
    used_questions = due_history + due_toeic
    used_questions_text = [uq["question"] for uq in used_questions]
    
    # 기존 대기열에서 이번에 출제한 복습 문제 제거
    quiz_db["spaced_repetition_pool"] = [
        q for q in quiz_db["spaced_repetition_pool"] 
        if q["question"] not in used_questions_text
    ]
    
    # 활성화된 Poll DB 등록
    quiz_db["sent_polls"] = active_polls
    
    # DB 파일 저장
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(quiz_db, f, ensure_ascii=False, indent=2)
        
    print("[Leitner] Leitner 데이터베이스 업데이트 및 저장 완료.")
    
    # 8. GitHub에 DB 변경사항 자동 커밋 & 푸시
    commit_and_push_db()
    
    print("\n🎉 아침 브리핑 및 퀴즈 출제가 성공적으로 끝났습니다!")


if __name__ == "__main__":
    run_morning_briefing()
