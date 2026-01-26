import datetime
import re
import requests
from bs4 import BeautifulSoup
import trafilatura

def get_clean_summary(url):
    try:
        # User-Agent 설정으로 차단 방지
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None: return ""

        text = trafilatura.extract(downloaded, include_comments=False)
        if not text or len(text) < 100: return ""

        # 본문 정제
        text = text.replace('\n', ' ').strip()
        text = re.sub(r'\s+', ' ', text)

        sentences = text.split('. ')
        summary_sentences = []
        char_count = 0
        
        for sent in sentences:
            clean_sent = sent.strip()
            if len(clean_sent) < 20: continue
            if not clean_sent.endswith('.'): clean_sent += '.'
            
            summary_sentences.append(clean_sent)
            char_count += len(clean_sent)
            if char_count > 350: break
        
        return ' '.join(summary_sentences)
    except:
        return ""

def get_naver_section_links(sid1, sid2=None):
    """
    네이버 뉴스 섹션 페이지에서 기사 링크를 직접 추출합니다.
    sid1: 105(IT/과학), 101(경제), 102(사회)
    """
    links = []
    url = f"https://news.naver.com/main/main.naver?mode=LSD&mid=shm&sid1={sid1}"
    if sid2:
        url += f"&sid2={sid2}"
        
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 네이버 뉴스 메인 페이지의 기사 링크 패턴 추출
        for a in soup.select('a[href*="article"]'):
            href = a['href']
            if href.startswith('https://n.news.naver.com/mnews/article/'):
                full_url = href.split('?')[0] # 파라미터 제거
                if full_url not in links:
                    links.append(full_url)
            if len(links) >= 5: break # 넉넉하게 후보군 5개 수집
    except Exception as e:
        print(f"Naver Scraping Error: {e}")
    
    return links

def fetch_news():
    # 네이버 뉴스 섹션 코드: 105(IT/AI), 101(경제), 102(사회/교육)
    sections = {
        "🤖 인공지능 (AI)": {"sid1": "105"},
        "💰 경제": {"sid1": "101"},
        "🎓 교육": {"sid1": "102", "sid2": "250"} # 250은 교육 섹션
    }
    
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    
    markdown = f"""---
date: {today_str}
last_update: {now.strftime("%Y-%m-%d %H:%M:%S")}
type: insight
topic: [인공지능, 경제, 교육]
tags: [뉴스, 요약, {today_str}]
---

# 📅 {now.strftime('%Y년 %m월 %d일(%a)')} 핵심 뉴스 브리핑

"""
    
    for category, ids in sections.items():
        markdown += f"## {category}\n"
        print(f"Processing: {category}")
        
        links = get_naver_section_links(ids['sid1'], ids.get('sid2'))
        success_count = 0
        
        for link in links:
            if success_count >= 2: break
            
            summary = get_clean_summary(link)
            if not summary: continue
            
            # 네이버 뉴스는 trafilatura가 제목도 잘 가져옵니다.
            markdown += f"### 🔗 [뉴스 기사 확인하기]({link})\n"
            markdown += f"> {summary}\n\n"
            success_count += 1
            
        if success_count == 0:
            markdown += "> 최신 기사를 불러오는 데 실패했습니다.\n\n"

    markdown += "---\n### 📂 자동화 기록 안내\n"
    filename = f"{today_str}_Daily_News_Briefing.md"
    return filename, markdown

if __name__ == "__main__":
    filename, content = fetch_news()
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
