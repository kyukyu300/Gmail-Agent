# 대학생 AI 스마트 어시스턴트 🎓

구글 Gmail 요약, Google Calendar 일정 등록/알림, **전북대학교(JBNU) 학사 및 장학 공지사항 수집**, **망각 곡선 반영 라이트너(Leitner) 퀴즈 투표**, 그리고 **분야별 시사 뉴스 메일 발송**을 매일 아침 자동으로 처리하는 최첨단 AI 에이전트 서비스입니다.

GitHub Actions 스케줄러를 통해 클라우드 환경에서 매일 아침 지연 없이 실행되도록 구성할 수 있으며, 퀴즈 정답 결과 및 학습 현황 데이터베이스는 자동으로 레포지토리에 저장(State Persistence)됩니다.

---

## 🌟 주요 기능

| 기능 | 요약 | 상세 설명 |
| :--- | :--- | :--- |
| **📧 Gmail 중요 메일 요약** | 최근 24시간 메일 브리핑 | 긴 안내 메일을 핵심만 3줄 이내로 깔끔하게 요약하여 전달합니다. |
| **📅 구글 캘린더 일정 관리** | 일정 확인 및 자동 등록 | 이번 주 일정을 브리핑하며, 이메일/공지사항에서 발견된 **시험, 과제 마감일, 근로 장학생 모집 마감일** 등을 구글 캘린더에 자동 등록합니다. |
| **📢 전북대 공지사항 알리미** | 교내 및 장학 공지 크롤링 | 전북대학교 홈페이지의 교내공지(`sub01.do`) 및 장학공지(`sub03.do`)를 크롤링하여 **장학금, 국가근로(근로장학생), 학생 지원 혜택 및 복지**에 부합하는 소식을 우선하여 링크와 함께 요약 제공합니다. |
| **📝 라이트너(Leitner) 퀴즈** | 텔레그램 네이티브 퀴즈 투표 | 매일 아침 한국사능력검정시험(한능검) 심화 5문제 + 토익 RC 5문제를 텔레그램 Quiz Poll 형태로 발송합니다. 사용자는 앱 내에서 즉시 풀고 해설을 터치해 볼 수 있습니다. |
| **🧠 오답 복습 및 스케줄러** | 망각 곡선 기반 스케줄링 | 전날 출제된 퀴즈의 투표 결과를 수집하여 **오답은 당일 즉시 복습 지정, 정답은 다음 주기(1일 ➡️ 3일 ➡️ 7일 뒤)로 승급**시켜 효율적인 암기 학습을 제공합니다. |
| **📰 시사 뉴스 HTML 이메일** | 뉴스 요약본 자동 메일링 | 오늘의 10대 주요 뉴스 헤드라인을 종합, IT/테크, 경제 분야로 나누어 반응형 웹 디자인 스타일링이 적용된 HTML 형식으로 본인의 이메일로 전송합니다. |
| **🔄 깃허브 상태 동기화** | 자동 Git 커밋 & 푸시 | 퀴즈 출제 이력과 라이트너 학습 박스가 담긴 데이터베이스(`quiz_db.json`)의 업데이트 사항을 매일 실행 종료 직후 GitHub에 자동 커밋하여 상태를 영구 보존합니다. |

---

## 📂 프로젝트 구조

```text
college-agent/
├── .github/
│   └── workflows/
│       └── daily_briefing.yml   # 매일 오전 8:48(KST) 자동 실행 및 DB 자동 저장 깃허브 액션
├── agent.py                     # Gemini 3.1 Flash-Lite 기반 의사결정 브레인 에이전트
├── google_services.py           # Gmail (읽기/보내기) + Google Calendar API 연동 모듈
├── telegram_service.py          # 텔레그램 메시지 발송 및 네이티브 Quiz Poll 발송/투표 조회 모듈
├── notice_service.py            # 전북대학교 공지사항 (교내공지, 장학공지) 멀티 크롤러 모듈
├── news_service.py              # 최신 뉴스 헤드라인 수집 API 연동 모듈
├── main.py                      # 전체 에이전트 실행 진입점 (EntryPoint)
├── quiz_db.json                 # 라이트너 오답 복습 상태를 저장하는 로컬/원격 데이터베이스
├── requirements.txt             # 프로젝트 의존성 라이브러리 목록
└── credentials.json             # Google Cloud Console용 OAuth2 클라이언트 키 (배포 시 필수)
```

---

## 🛠 설치 및 초기 설정

### 1. 패키지 설치
로컬 실행을 위해 아래의 명령어로 필요 패키지를 설치합니다.
```bash
pip install -r requirements.txt
```

### 2. 구글 OAuth2 인증 파일 준비
* Google Cloud Console에서 `Gmail API`, `Google Calendar API`를 활성화합니다.
* 데스크톱 앱 형식의 `OAuth 2.0 클라이언트 ID`를 생성하여 `credentials.json` 파일명으로 프로젝트 루트 디렉토리에 저장합니다.

### 3. 로컬 첫 실행 및 토큰 생성
```bash
python main.py
```
* 최초 실행 시 웹 브라우저 창이 열리며 구글 로그인창으로 리다이렉트됩니다.
* 권한 수락을 완료하면 프로젝트 디렉토리에 `token.json`이 자동으로 생성됩니다. 이후부터는 추가 인증 없이 무중단 자동 실행됩니다.

### 4. 환경 변수 구성 (`.env`)
프로젝트 루트 폴더에 `.env` 파일을 생성하고 아래의 설정값을 기입합니다.
```env
GEMINI_API_KEY=your_gemini_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# (선택 사항) 크롤링할 대학교 공지사항 URL 변경 시 기입 (기본값: 전북대학교)
# UNIVERSITY_NOTICE_URL=https://www.snu.ac.kr/academics/resources/announcements
```

---

## ☁️ GitHub Actions를 통한 무중단 클라우드 배포

이 프로젝트는 서버를 24시간 켜둘 필요 없이, **GitHub Actions** 무료 컨테이너를 스케줄러로 활용해 매일 아침 정해진 시간에 구동됩니다.

### 1. GitHub Secrets 등록
보안이 요구되는 환경 변수와 인증 데이터들을 GitHub Repository의 **Settings -> Secrets and variables -> Actions**에 등록합니다.

* `DOT_ENV`: 로컬 `.env` 파일의 전체 텍스트 내용 복사 붙여넣기
* `CREDENTIALS_JSON`: 로컬 `credentials.json` 파일의 전체 JSON 내용 복사 붙여넣기
* `TOKEN_JSON`: 로컬 `token.json` 파일의 전체 JSON 내용 복사 붙여넣기

### 2. 저장소 쓰기 권한 활성화 (필수)
`quiz_db.json` 학습 데이터베이스 상태를 매일 자동으로 깃허브에 커밋 & 백업하기 위해 Actions의 쓰기 권한이 필요합니다.
* GitHub 레포지토리의 **Settings -> Actions -> General -> Workflow permissions**로 이동합니다.
* **Read and write permissions** 옵션을 활성화하고 저장합니다.

### 3. 구동 일정
깃허브 액션 대기열 혼잡에 따른 지연을 방지하기 위해 매일 한국 시간 **오전 8시 48분**에 구동이 예약되어 있으며, 실행 소요 시간과 미세 지연을 합쳐 **매일 오전 9시 전후 정각**에 최상의 품질로 비서 브리핑과 10개의 퀴즈 투표를 받아볼 수 있습니다.
