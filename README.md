# 대학생 AI 어시스턴트 🎓

Gmail 요약 + Google Calendar 일정 알림을 매일 아침 텔레그램으로 전송하는 AI 에이전트

## 프로젝트 구조

```
college-agent/
├── .env                 # API 키 (절대 공유 금지!)
├── credentials.json     # Google OAuth2 키 (직접 넣어야 함)
├── requirements.txt     # 의존성 패키지
├── main.py              # 실행 진입점
├── agent.py             # Gemini AI 에이전트 (두뇌)
├── google_services.py   # Gmail + Calendar API
└── telegram_service.py  # 텔레그램 알림
```

## 설치 및 실행

### 1. 패키지 설치
```bash
pip install -r requirements.txt
```

### 2. credentials.json 넣기
Google Cloud Console에서 다운로드한 `credentials.json`을 이 폴더에 넣으세요.

### 3. 첫 실행 (Google 로그인)
```bash
python main.py
```
처음 실행 시 브라우저가 열리며 Google 로그인을 요청합니다.
로그인 후 `token.json`이 자동 생성되고 이후엔 자동 실행됩니다.

### 4. 매일 아침 자동 실행 설정 (Mac cron)
```bash
# crontab 편집
crontab -e

# 매일 오전 8시에 실행 (아래 줄 추가)
0 8 * * * cd /Users/gyujin/.gemini/antigravity/scratch/college-agent && python main.py >> logs/agent.log 2>&1
```

## 기능

| 기능 | 설명 |
|------|------|
| 📧 이메일 요약 | 최근 24시간 Gmail 요약 |
| 📅 일정 알림 | 이번 주 Google Calendar 일정 |
| 🗓️ 자동 일정 등록 | 이메일에서 마감일 감지 → 캘린더 자동 등록 |
| 📱 텔레그램 알림 | 매일 아침 브리핑 전송 |

## 주의사항
- `.env`와 `credentials.json`, `token.json`은 절대 GitHub에 올리지 마세요!
- `.gitignore`에 반드시 추가하세요.
