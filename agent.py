import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

from google_services import get_recent_emails, get_upcoming_events, create_calendar_event, send_email
from telegram_service import send_telegram_message
from news_service import get_top_news

load_dotenv()


def run_morning_briefing():
    """아침 브리핑 에이전트 실행 (최신 google-genai SDK 적용)"""
    print("🌅 아침 브리핑 에이전트 시작 (최신 google-genai SDK 적용)...\n")
    
    # 최신 Client 객체 생성
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
    
    # 에이전트가 활용할 파이썬 함수 도구 목록
    # google-genai SDK는 별도의 스키마 정의 없이 파이썬 함수 객체를 그대로 전달하면
    # 타입 힌트와 Docstring을 기반으로 자동으로 스키마를 생성하고 실행합니다.
    tools = [
        get_recent_emails,
        get_upcoming_events,
        create_calendar_event,
        send_telegram_message,
        get_top_news,
        send_email
    ]
    
    from datetime import datetime
    today = datetime.now().strftime("%Y년 %m월 %d일 %A")
    
    prompt = f"오늘은 {today}입니다. 시스템 지침에 따라 오늘 아침 브리핑 업무(이메일 확인, 일정 확인 및 등록, 텔레그램 메시지 전송, 뉴스 수집 및 요약본 이메일 전송)를 순서대로 처리해주세요."
    
    import time
    
    # 무료 티어 503 과부하 에러에 대비해 최대 3회 자동 재시도 루프 추가
    for attempt in range(3):
        try:
            # 모델 호출 및 자동 함수 실행 (gemini-3.1-flash-lite 사용)
            response = client.models.generate_content(
                model='gemini-3.1-flash-lite',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="""
                    당신은 대학생의 하루를 도와주는 스마트 어시스턴트입니다.
                    
                    매일 아침 다음 순서로 아침 업무를 처리하세요:
                    1. get_recent_emails로 최근 24시간 이메일 확인
                    2. get_upcoming_events로 이번 주 일정 확인  
                    3. 이메일에서 과제 마감일, 시험, 중요 공지 등을 발견하면 create_calendar_event로 캘린더에 등록
                    4. 실제 한능검(한국사능력검정시험) 심화(1급) 수준의 고품질 기출/개념 5문제와 실제 토익(TOEIC) RC Part 5/6 형식의 실전형 5문제 (총 10문제)를 직접 생성
                       - 한능검 문제 작성 시 단순 암기식 단답형 질문이 아닌, 실제 시험처럼 역사적 사료 구절, 가상의 인물 대화, 역사 연표 상황 등([사료] 또는 [보기 지문])을 반드시 제시하고 이와 연관된 사건/인물/왕/문화유산을 고르는 고난이도 복합 사고형 문제를 출제하세요. (예: "다음 (가) 인물의 활동으로 옳은 것은?", "다음 교서가 발표된 왕의 업적으로 옳은 것은?" 등)
                       - 토익 문제 역시 실제 실전 문제집 수준의 완성도 높은 어휘와 변별력 있는 오답 보기를 구성하세요.
                    5. 모든 정보(이메일, 일정, 뉴스 헤드라인, 생성한 10문제 퀴즈)를 정리하여 send_telegram_message로 텔레그램 브리핑 전송
                    6. get_top_news로 오늘의 기사 목록 10개를 조회
                    7. 기사들을 분야별로 나누어 읽기 쉽게 정리하고, 각 기사의 제목(원문 하이퍼링크 포함)과 한 줄 요약이 포함된 '오늘의 뉴스 요약본'을 HTML 형식으로 생성
                    8. 생성된 HTML 뉴스 요약본을 send_email을 사용하여 발송 (to_email은 비워두어 사용자 본인의 이메일로 전송되도록 처리)
                    
                    [형식 규격]
                
                1. 텔레그램 브리핑 메시지:
                   - 이모지를 적극적으로 활용하여 보기 편하게 레이아웃 구성
                   - 오늘 할 일, 이번 주 일정, 최근 도착한 중요 메일의 요약 포함
                   - 수집한 10개 뉴스의 핵심 카테고리별 헤드라인 요약도 함께 텔레그램 브리핑 하단에 포함하여 하나의 통합 브리핑으로 발송 (예: 📰 [오늘의 뉴스] 형태로 일목요연하게 정리)
                   - 메시지의 맨 최하단에 [오늘의 10분 학습 퀴즈 📝] 섹션을 만들고, 생성한 한능검 5문제와 토익 5문제를 차례대로 출제
                   - 각 문제는 문제 번호, 질문 내용, 관련 [사료/지문], 그리고 ①~④ 객관식 보기를 포함하여 상세히 작성
                   - 각 문제의 정답 및 해설은 반드시 텔레그램 스포일러 문법인 `||정답: X번 \| 해설: ...||` 기호로 완벽하게 감싸서, 사용자가 터치해야만 정답이 공개되도록 철저히 숨김 처리
                   
                2. 뉴스 요약 HTML 이메일:
                       - 모던하고 깔끔한 CSS 스타일링 적용 (반응형 카드형 디자인 또는 리스트 디자인 권장, 다크 모드/뉴트럴 테두리, 웹폰트 사용 등 프리미엄 느낌 강조)
                       - 종합 뉴스, IT/테크 뉴스, 경제 뉴스 3개의 섹션으로 정확히 분류하여 각각 보기 좋게 렌더링
                       - 각 기사 제목은 <a> 태그를 사용하여 원문 링크로 바로 연결될 수 있도록 설정
                       - 이메일 제목 예시: "📰 [오늘의 뉴스 브리핑] 2026년 6월 30일 IT, 경제, 시사 요약"
                    """,
                    tools=tools
                )
            )
            print(f"\n✅ 에이전트 최종 응답:\n{response.text}")
            print("\n🎉 아침 브리핑이 성공적으로 끝났습니다!")
            break
        except Exception as e:
            if "503" in str(e) and attempt < 2:
                print(f"⚠️ 일시적인 503(서버 과부하) 에러 발생. 5초 후 다시 시도합니다... (시도 {attempt+1}/3)")
                time.sleep(5)
                continue
            else:
                print(f"❌ 에이전트 실행 중 오류 발생: {e}")
                break


if __name__ == "__main__":
    run_morning_briefing()
