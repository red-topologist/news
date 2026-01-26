import feedparser
import datetime
import re
import os
from newspaper import Article

def get_article_content(url):
    try:
        # 구글 뉴스 등 리다이렉트가 있는 경우를 위해 newspaper3k가 자동으로 처리
        article = Article(url, language='ko')
        article.download()
        article.parse()
        
        # 줄바꿈 정제
        text = re.sub(r'\n+', ' ', article.text.strip())
        
        # 300~350자 내외로 요약 (문장 중간 끊김 방지)
        summary = text[:350]
        if "." in summary[300:]:
            summary = summary[:300] + summary[300:].split('.')[0] + "."
        else:
            summary += "..."
            
        return summary
    except:
        return ""

def fetch_korean_news():
    # 1. 뉴스 소스 정의 (교육은 구글 뉴스로 변경하여 해결)
    sources = {
        "🤖 인공지능 (AI)": "http://www.aitimes.com/rss/allArticle.xml", 
        "🏛️ 정치": "https://www.yna.co.kr/rss/politics.xml", 
        "🏥 사회": "https://www.yna.co.kr/rss/society.xml",
        "🎓 교육": "https://news.google.com/rss/search?q=교육&hl=ko&gl=KR&ceid=KR:ko"
    }
    
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    today_display = now.strftime("%Y년 %m월 %d일(%a)")
    update_time = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # 2. YAML Frontmatter 작성 (요청하신 형식 적용)
    # topic과 source는 현재 수집하는 대상에 맞춰서 기입
    markdown = f"""---
date: {today_str}
last_update: {update_time}
type: insight
topic: [인공지능, 정치, 사회, 교육]
tags: [뉴스, 요약, 자동화, {today_str}]
source: [AI타임스, 연합뉴스, 구글뉴스]
---

# 📅 {today_display} 핵심 뉴스 브리핑

"""
    
    first_title = "" 

    for category, rss_url in sources.items():
        markdown += f"## {category}\n"
        try:
            feed = feedparser.parse(rss_url)
            # 분야별 기사 2개씩 가져오기
            for entry in feed.entries[:2]:
                
                # 본문 추출 시도
                content_summary = get_article_content(entry.link)
                
                # 본문 추출 실패 시 RSS 기본 설명 사용 (구글 뉴스는 이쪽으로 빠질 확률이 있음)
                if not content_summary or len(content_summary) < 20:
                    if 'description' in entry:
                        clean_desc = re.sub('<[^<]+?>', '', entry.description)
                        content_summary = clean_desc[:200] + "..."
                    else:
                        content_summary = "내용을 불러올 수 없습니다. 원문 링크를 확인하세요."
                
                markdown += f"### 🔗 [{entry.title}]({entry.link})\n"
                markdown += f"> {content_summary}\n\n"

                # 파일명 생성용 (첫 기사 제목)
                if not first_title:
                    clean_title = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', entry.title).strip()
                    safe_title = clean_title.replace(" ", "_")[:15]
                    first_title = safe_title
        except Exception as e:
            print(f"Error in {category}: {e}")
            markdown += f"> 뉴스 수집 중 오류가 발생했습니다.\n\n"

    markdown += "---\n"
    markdown += f"### 📂 자동화 기록 안내\n"
    markdown += f"최종 업데이트 시각: **{update_time}**\n"
    
    filename = f"{today_str}_{first_title}.md"
    return filename, markdown

if __name__ == "__main__":
    filename, content = fetch_korean_news()
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"File created: {filename}")
