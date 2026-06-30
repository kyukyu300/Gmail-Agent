import urllib.request
import xml.etree.ElementTree as ET
import json

def fetch_rss_titles(url: str, limit: int = 4) -> list:
    """RSS 피드에서 기사 제목과 링크를 가져옵니다."""
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        items = []
        for item in root.findall('.//item')[:limit]:
            title = item.find('title').text if item.find('title') is not None else '제목 없음'
            link = item.find('link').text if item.find('link') is not None else ''
            # 구글 뉴스 제목 포맷: "제목 - 언론사"에서 언론사 부분 분리하거나 그냥 둠
            items.append({
                'title': title,
                'link': link
            })
        return items
    except Exception as e:
        print(f"❌ RSS 가져오기 실패 ({url}): {e}")
        return []

def get_top_news() -> list:
    """
    종합 뉴스(4개), IT/테크 뉴스(3개), 경제 뉴스(3개)를 골고루 가져옵니다.
    
    Returns:
        기사 목록 (category, title, link)
    """
    general_url = "https://news.google.com/rss?hl=ko&gl=KR&ceid=KR:ko"
    it_url = "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=ko&gl=KR&ceid=KR:ko"
    business_url = "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko"
    
    combined_news = []
    
    # 1. 종합 뉴스 4개
    for item in fetch_rss_titles(general_url, 4):
        combined_news.append({
            'category': '종합 뉴스',
            'title': item['title'],
            'link': item['link']
        })
        
    # 2. IT/과학 뉴스 3개
    for item in fetch_rss_titles(it_url, 3):
        combined_news.append({
            'category': 'IT/테크 뉴스',
            'title': item['title'],
            'link': item['link']
        })
        
    # 3. 경제/비즈니스 뉴스 3개
    for item in fetch_rss_titles(business_url, 3):
        combined_news.append({
            'category': '경제 뉴스',
            'title': item['title'],
            'link': item['link']
        })
        
    return combined_news


if __name__ == "__main__":
    # 단독 실행 시 테스트 출력
    print("📰 뉴스 가져오기 테스트...")
    news = get_top_news()
    print(f"가져온 뉴스 개수: {len(news)}")
    for i, n in enumerate(news, 1):
        print(f"{i}. [{n['category']}] {n['title']} ({n['link'][:40]}...)")
