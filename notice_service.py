import os
import urllib.request
import urllib.parse
import ssl
import re
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive'
}

def get_university_notices() -> list[dict]:
    """
    학교 홈페이지 공지사항을 스크레이핑하여 최근 공지글 목록을 가져옵니다.
    .env에 UNIVERSITY_NOTICE_URL이 지정되어 있으면 해당 페이지를 긁어오며,
    미지정시 기본값으로 전북대학교 교내공지(sub01.do) 및 장학공지(sub03.do) 게시판을 모두 스크랩하여 통합합니다.
    """
    url = os.getenv("UNIVERSITY_NOTICE_URL")
    
    urls_to_scrape = []
    if not url:
        urls_to_scrape = [
            ("https://www.jbnu.ac.kr/web/news/notice/sub01.do", "교내공지"),
            ("https://www.jbnu.ac.kr/web/news/notice/sub03.do", "장학공지")
        ]
    else:
        urls_to_scrape = [(url, "공지사항")]
        
    all_notices = []
    context = ssl._create_unverified_context()
    
    for target_url, board_name in urls_to_scrape:
        print(f"[Notice] Fetching notices from: {target_url} ({board_name})")
        try:
            req = urllib.request.Request(target_url, headers=HEADERS)
            with urllib.request.urlopen(req, context=context, timeout=10) as response:
                raw_bytes = response.read()
                
            soup = BeautifulSoup(raw_bytes.decode("utf-8", errors="ignore"), 'html.parser')
            
            # 1. 전북대학교 공지사항 게시판 구조
            if "jbnu.ac.kr" in target_url:
                rows = soup.select("table tbody tr")
                print(f"[Notice] Found {len(rows)} rows in {board_name}.")
                for row in rows[:10]:  # 최근 10개씩 수집
                    title_el = row.select_one("a.title")
                    if not title_el:
                        title_el = row.select_one("td.td-title a, td a")
                        
                    if title_el:
                        title = title_el.get_text(strip=True)
                        # 게시판 이름을 머릿말로 붙여 구분
                        if not title.startswith(f"[{board_name}]"):
                            title = f"[{board_name}] {title}"
                            
                        # javascript pf_DetailMove 파싱 처리
                        link = ""
                        onclick_str = title_el.get("onclick", "")
                        match = re.search(r"pf_DetailMove\('(\d+)'\)", onclick_str)
                        if match:
                            post_id = match.group(1)
                            link = f"https://www.jbnu.ac.kr/web/Board/{post_id}/detailView.do"
                        else:
                            href = title_el.get("href", "")
                            if href and not href.startswith("javascript:"):
                                link = urllib.parse.urljoin(target_url, href)
                                
                        # 날짜 파싱 (etc-list 첫 번째 li 요소를 날짜로 사용)
                        date_el = row.select_one("ul.etc-list li")
                        if date_el:
                            date_str = date_el.get_text(strip=True)
                        else:
                            date_str = datetime.now().strftime("%Y-%m-%d")
                            for td in row.find_all("td"):
                                txt = td.get_text(strip=True)
                                if len(txt) >= 8 and (txt.count('-') >= 2 or txt.count('.') >= 2):
                                    date_str = txt
                                    break
                                    
                        if title and link:
                            all_notices.append({
                                "title": title,
                                "link": link,
                                "date": date_str
                            })
                            
            # 2. 범용 테이블 게시판 구조 (기타 사이트 대비)
            else:
                rows = soup.select("table tbody tr")
                if not rows:
                    rows = soup.select("tr")
                    
                for row in rows[:10]:
                    a_tags = row.find_all("a")
                    if not a_tags:
                        continue
                        
                    title_el = max(a_tags, key=lambda el: len(el.get_text(strip=True)))
                    title = title_el.get_text(strip=True)
                    if len(title) < 5:
                        continue
                        
                    link = title_el.get("href", "")
                    if link and not link.startswith("http"):
                        link = urllib.parse.urljoin(target_url, link)
                        
                    date_str = datetime.now().strftime("%Y-%m-%d")
                    tds = row.find_all("td")
                    for td in tds:
                        text = td.get_text(strip=True)
                        if len(text) >= 8 and (text.count('.') >= 2 or text.count('-') >= 2):
                            date_str = text
                            break
                            
                    all_notices.append({
                        "title": title,
                        "link": link,
                        "date": date_str
                    })
        except Exception as e:
            print(f"[Notice] Failed to fetch notices from {target_url}: {e}")
            
    # 중복 제거 (링크 기준)
    unique_notices = []
    seen_links = set()
    for n in all_notices:
        if n["link"] not in seen_links:
            seen_links.add(n["link"])
            unique_notices.append(n)
            
    # 날짜 최신순 정렬
    unique_notices.sort(key=lambda x: x["date"], reverse=True)
    
    print(f"[Notice] Total combined unique notices: {len(unique_notices)}")
    return unique_notices[:15]  # 최근 15개 요약 후보 반환

if __name__ == "__main__":
    print(get_university_notices())
