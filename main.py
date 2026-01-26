import feedparser
import datetime
import re
import nltk
from newspaper import Article, Config

# 자연어 처리를 위한 데이터 다운로드 (최초 1회)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def get_clean_summary(url):
    """
    기사 본문을 긁어와서 '완벽한 문장'으로 구성된 요약본을 반환합니다.
    말 줄임표(...)로 끝나는 것을 방지합니다.
    """
    # 봇 차단 방지를 위한 브라우저 위장 설정
    config = Config()
    config.browser_user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    config.request_timeout = 10

    try:
        article = Article(url, config=config, language='ko')
        article.download()
        article.parse()
        
        # 본문이 너무 짧으면(스크랩 실패 등) 빈 값 반환 -> 목록에서 제외됨
        if len(article.text) < 50:
            return ""

        # 문장 단위로 분리
        text = article.text.strip()
        # 불필요한 공백/줄바꿈 제거
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\s+', ' ', text)

        # 마침표 기준으로 문장 나누기 (간이 문장 분리)
        sentences = text.split('. ')
        
        # 핵심 3~4문장만 추출
        summary_sentences = []
        char_count = 0
        
        for sent in sentences:
            clean_sent = sent.strip()
            if not clean_sent: continue
            
            # 너무 짧은 문장(기자 이름 등) 제외
            if len(clean_sent) < 10: continue
            
            # 문장 끝에 마침표 복구
            if not clean_sent.endswith('.'):
                clean_sent += '.'
            
            summary_sentences.append(clean_sent)
            char_count += len(clean_sent)
            
            # 약 300~400자 정도 채워지면 중단
            if char_count > 350:
                break
        
        # 문장들을 다시 합침
        final_summary = ' '.join(summary_sentences)
        return final_summary

    except Exception as e:
        # 에러 발생 시 해당 기사는 건너뜀
        return ""

def fetch_news():
    # 1. 스크랩이 확실하게 잘 되는 '직접 RSS' 소스 선정
    sources = {
        "🤖 인공지능 (AI)": "http://www.aitimes.com/rss/allArticle.xml", # AI타임스 (전문지)
        "💰 경제": "https://www.mk.co.kr/rss/30000001/", # 매일경제 (경제)
        "🎓 교육": "https://rss.donga.com/education.php" # 동아일보 교육섹션 (스크랩 안정성 높음)
    }
    
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    update_time = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # YAML Frontmatter
    markdown = f"""---
date: {today_str}
last_update: {update_time}
type: insight
topic: [인공지능, 경제, 교육]
tags: [뉴스, 요약, {today_str}]
source: [AI타임스, 매일경제, 동아일보]
---

# 📅 {now.strftime('%Y년 %m월 %d일(%a)')} 핵심 뉴스 브리핑

"""
    
    first_title = "" 

    for category, rss_url in sources.items():
        markdown += f"## {category}\n"
        try:
            feed = feedparser.parse(rss_url)
            
            # 분야별 성공한 기사 2개만 수집
            success_count = 0
            
            for entry in feed.entries:
                if success_count >= 2: break
                
                # 본문 스크랩 시도
                summary = get_clean_summary(entry.link)
                
                # 스크랩 실패했거나 내용이 없으면 과감히 건너뜀 (말줄임표 방지)
                if not summary:
                    continue
                
                markdown += f"### 🔗 [{entry.title}]({entry.link})\n"
                markdown += f"> {summary}\n\n"
                
                # 파일명용 제목 추출
                if not first_title:
                    clean_title = re.sub(r'[^가-힣a-zA-Z0-9\s]', '', entry.title).strip()
                    first_title = clean_title.replace(" ", "_")[:15]
                
                success_count += 1
                
        except Exception as e:
            print(f"Error in {category}: {e}")

    markdown += "---\n"
    markdown += f"### 📂 자동화 기록 안내\n"
    markdown += f"최종 업데이트 시각: **{update_time}**\n"
    
    filename = f"{today_str}_{first_title}.md"
    return filename, markdown

if __name__ == "__main__":
    filename, content = fetch_news()
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created: {filename}")
