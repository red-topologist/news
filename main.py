import feedparser
import datetime
import re
from newspaper import Article
from googletrans import Translator
import nltk

# 요약 기능을 위해 필요한 데이터 다운로드 (최초 1회 실행됨)
nltk.download('punkt')

def get_article_summary(url):
    try:
        article = Article(url, language='en') # 일단 영어로 설정 (국내뉴스도 처리 가능)
        article.download()
        article.parse()
        article.nlp() # 자연어 처리로 핵심 문장 추출
        return article.summary
    except:
        return ""

def clean_text(text):
    # 번역투 및 불필요한 공백 제거
    text = text.replace(" .", ".").replace(" ,", ",")
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def fetch_and_format_news():
    translator = Translator()
    
    # 1. 권위 있는 소스 선정 (실제 기사 링크를 얻기 위해 RSS를 '주소록'으로만 활용)
    sources = {
        "🤖 인공지능 (AI)": "https://www.technologyreview.com/feed/", # MIT Tech Review
        "🏛️ 정치": "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml", # NYT Politics
        "🏥 사회": "https://www.yna.co.kr/rss/society.xml", # 연합뉴스 사회
        "🎓 교육": "https://www.hangyo.com/rss/allArticle.xml" # 한국교육신문
    }
    
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    today_kr = now.strftime("%Y년 %m월 %d일(%a)")
    
    # 2. 헤더 작성 (요청하신 멘트 그대로)
    markdown = f"---\ndate: {today_str}\ntags: [뉴스, 요약, 자동화]\n---\n\n"
    markdown += f"# 📅 {today_kr} 분야별 최신 뉴스 요약\n\n"
    markdown += f"현재 시점을 기준으로 인공지능(AI), 정치, 사회, 교육 분야의 최신 주요 뉴스를 정리해 드립니다. 특히 급변하는 국제 정세와 기술 발전의 흐름을 중점적으로 파악했습니다.\n\n"
    
    first_title = "" # 파일명용 변수

    for category, rss_url in sources.items():
        markdown += f"## {category}\n"
        
        try:
            feed = feedparser.parse(rss_url)
            # 분야별 상위 2개 기사만 선정 (퀄리티 집중)
            for entry in feed.entries[:2]:
                
                # (1) 기사 원문 내용 추출
                original_summary = get_article_summary(entry.link)
                
                # 추출 실패시 RSS의 기본 설명으로 대체
                if len(original_summary) < 50:
                    original_summary = entry.description if 'description' in entry else entry.title

                # (2) 한국어 번역 및 다듬기
                title_kr = entry.title
                summary_kr = original_summary
                
                # 해외 사이트(영어)인 경우 번역 실행
                if "technologyreview" in rss_url or "nytimes" in rss_url:
                    try:
                        title_kr = translator.translate(entry.title, dest='ko').text
                        # 내용이 너무 길면 앞부분 400자만 번역 (속도 및 가독성)
                        summary_to_translate = original_summary[:1000] 
                        summary_kr = translator.translate(summary_to_translate, dest='ko').text
                    except:
                        pass
                
                # (3) 텍스트 정제 (HTML 태그 삭제 등)
                title_kr = re.sub(r'[\[\]]', '', title_kr) # 대괄호 제거
                summary_kr = re.sub('<[^<]+?>', '', summary_kr) # HTML 태그 제거
                summary_kr = clean_text(summary_kr)
                
                # 요약문 길이 조절 (너무 길지 않게, 서술형 느낌)
                if len(summary_kr) > 250:
                    summary_kr = summary_kr[:250] + "..."
                
                # (4) 출력 포맷 적용 (제목: 내용 스타일)
                markdown += f"**{title_kr}**: {summary_kr}\n\n"

                # 파일명 생성용 (첫 기사 제목)
                if not first_title:
                    first_title = re.sub(r'[^가-힣a-zA-Z0-9]', '', title_kr)[:15]

        except Exception as e:
            print(f"Error processing {category}: {e}")
            markdown += "뉴스 수집 중 일시적인 오류가 발생했습니다.\n\n"

    # 3. 푸터 작성
    markdown += "---\n"
    markdown += "### 📂 기록 안내\n"
    markdown += f"위 내용은 사용자님의 요청에 따라 GitHub Actions를 통해 자동 생성되어 Obsidian으로 동기화됩니다.\n"
    
    return f"{today_str}_{first_title}.md", markdown

if __name__ == "__main__":
    filename, content = fetch_and_format_news()
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"File created: {filename}")
