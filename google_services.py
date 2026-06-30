import os
import base64
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from email.mime.text import MIMEText

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar',
]

def get_google_credentials():
    """Google OAuth2 인증 처리"""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception:
                # If refresh fails, clear token and request again
                if os.path.exists('token.json'):
                    os.remove('token.json')
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return creds



def get_recent_emails(hours: int = 24) -> list[dict]:
    """
    최근 N시간 이내의 이메일을 가져옵니다.
    
    Args:
        hours: 몇 시간 이내 이메일을 가져올지
    
    Returns:
        이메일 목록 (sender, subject, body, date)
    """
    creds = get_google_credentials()
    service = build('gmail', 'v1', credentials=creds)
    
    after_time = int((datetime.now() - timedelta(hours=hours)).timestamp())
    query = f'after:{after_time}'
    
    result = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=20
    ).execute()
    
    messages = result.get('messages', [])
    emails = []
    
    for msg in messages:
        msg_data = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()
        
        headers = msg_data['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '제목 없음')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '발신자 없음')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
        
        # 본문 추출
        body = ''
        payload = msg_data['payload']
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
        elif 'body' in payload:
            data = payload['body'].get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        
        emails.append({
            'subject': subject,
            'sender': sender,
            'date': date,
            'body': body[:1000]  # 너무 길면 앞 1000자만
        })
    
    return emails


def get_upcoming_events(days: int = 7) -> list[dict]:
    """
    앞으로 N일간의 Google Calendar 일정을 가져옵니다.
    
    Args:
        days: 몇 일 앞 일정을 가져올지
    
    Returns:
        일정 목록 (title, start, end, description)
    """
    creds = get_google_credentials()
    service = build('calendar', 'v3', credentials=creds)
    
    now = datetime.utcnow().isoformat() + 'Z'
    end = (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
    
    result = service.events().list(
        calendarId='primary',
        timeMin=now,
        timeMax=end,
        maxResults=20,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = result.get('items', [])
    event_list = []
    
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date', ''))
        end_time = event['end'].get('dateTime', event['end'].get('date', ''))
        
        event_list.append({
            'title': event.get('summary', '제목 없음'),
            'start': start,
            'end': end_time,
            'description': event.get('description', '')
        })
    
    return event_list


def create_calendar_event(title: str, date: str, time: str = '', description: str = '') -> str:
    """
    Google Calendar에 새 일정을 추가합니다.
    
    Args:
        title: 일정 제목
        date: 날짜 (YYYY-MM-DD 형식)
        time: 시간 (HH:MM 형식, 없으면 종일 일정)
        description: 일정 설명
    
    Returns:
        성공/실패 메시지
    """
    creds = get_google_credentials()
    service = build('calendar', 'v3', credentials=creds)
    
    try:
        if time:
            # 시간 있는 일정
            start_datetime = f"{date}T{time}:00+09:00"
            end_datetime = f"{date}T{time}:00+09:00"
            event = {
                'summary': title,
                'description': description,
                'start': {'dateTime': start_datetime, 'timeZone': 'Asia/Seoul'},
                'end': {'dateTime': end_datetime, 'timeZone': 'Asia/Seoul'},
            }
        else:
            # 종일 일정
            event = {
                'summary': title,
                'description': description,
                'start': {'date': date},
                'end': {'date': date},
            }
        
        created = service.events().insert(calendarId='primary', body=event).execute()
        return f"✅ 일정 추가 완료: {title} ({date})"
    except Exception as e:
        return f"❌ 일정 추가 실패: {str(e)}"


def get_user_email() -> str:
    """인증된 사용자의 이메일 주소를 가져옵니다."""
    try:
        creds = get_google_credentials()
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        return profile.get('emailAddress', '이메일 주소 없음')
    except Exception as e:
        return f"❌ 사용자 이메일 조회 실패: {str(e)}"


def send_email(subject: str, html_content: str, to_email: str = None) -> str:
    """
    Gmail API를 통해 이메일을 보냅니다.
    
    Args:
        subject: 이메일 제목
        html_content: 이메일 본문 (HTML 형식 가능)
        to_email: 수신자 이메일 주소 (None인 경우 본인 주소로 자동 발송)
    
    Returns:
        성공/실패 결과 메시지
    """
    try:
        creds = get_google_credentials()
        service = build('gmail', 'v1', credentials=creds)
        
        # 수신자가 없거나 예시용 이메일(example.com 등)인 경우 본인 계정으로 설정
        if not to_email or "example" in to_email or "user@" in to_email:
            to_email = get_user_email()
            if to_email.startswith("❌"):
                return to_email
        
        message = MIMEText(html_content, 'html', 'utf-8')
        message['to'] = to_email
        message['from'] = 'me'
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return f"✅ 이메일 발송 성공 (수신: {to_email})"
    except Exception as e:
        return f"❌ 이메일 발송 실패: {str(e)}"

