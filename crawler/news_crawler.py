import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import random
import jieba
import re
from fake_useragent import UserAgent
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsCrawler:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # 中文新聞網站配置
        self.news_sites = {
            'udn': {
                'name': '聯合新聞網',
                'url': 'https://udn.com/news/breaknews/1',
                'selectors': {
                    'article': '.story-list__text',
                    'title': 'h2 a, h3 a',
                    'link': 'h2 a, h3 a',
                    'date': '.story-list__time'
                }
            },
            'chinatimes': {
                'name': '中時新聞網',
                'url': 'https://www.chinatimes.com/realtimenews',
                'selectors': {
                    'article': '.news-list-item',
                    'title': '.title a',
                    'link': '.title a',
                    'date': '.time'
                }
            },
            'ltn': {
                'name': '自由時報',
                'url': 'https://news.ltn.com.tw/breakingnews',
                'selectors': {
                    'article': '.list li',
                    'title': 'a',
                    'link': 'a',
                    'date': '.time'
                }
            },
            'cna': {
                'name': '中央社',
                'url': 'https://www.cna.com.tw/list/aall.aspx',
                'selectors': {
                    'article': '.mainList li',
                    'title': 'h2 a, h3 a',
                    'link': 'h2 a, h3 a',
                    'date': '.date'
                }
            },
            'bbc_chinese': {
                'name': 'BBC中文網',
                'url': 'https://www.bbc.com/zhongwen/trad',
                'selectors': {
                    'article': '.media-list__item',
                    'title': '.media__title a',
                    'link': '.media__title a',
                    'date': '.date'
                }
            },
            'rfi_chinese': {
                'name': 'RFI中文網',
                'url': 'https://www.rfi.fr/cn/',
                'selectors': {
                    'article': '.article__content',
                    'title': 'h2 a, h3 a',
                    'link': 'h2 a, h3 a',
                    'date': '.date'
                }
            }
        }
        
        # 簡體中文網站
        self.simplified_sites = {
            'sina': {
                'name': '新浪新聞',
                'url': 'https://news.sina.com.cn/',
                'selectors': {
                    'article': '.news-item',
                    'title': 'h3 a, h4 a',
                    'link': 'h3 a, h4 a',
                    'date': '.time'
                }
            },
            'sohu': {
                'name': '搜狐新聞',
                'url': 'https://news.sohu.com/',
                'selectors': {
                    'article': '.news-item',
                    'title': 'h3 a, h4 a',
                    'link': 'h3 a, h4 a',
                    'date': '.time'
                }
            },
            'people': {
                'name': '人民網',
                'url': 'http://www.people.com.cn/',
                'selectors': {
                    'article': '.news-item',
                    'title': 'h3 a, h4 a',
                    'link': 'h3 a, h4 a',
                    'date': '.time'
                }
            }
        }
        
        # 合併所有網站
        self.all_sites = {**self.news_sites, **self.simplified_sites}

    def crawl_news(self, start_date, end_date, topics=None):
        """爬取新聞"""
        articles = []
        
        for site_key, site_config in self.all_sites.items():
            try:
                logger.info(f"正在爬取 {site_config['name']}...")
                site_articles = self._crawl_site(site_config, start_date, end_date, topics)
                articles.extend(site_articles)
                
                # 隨機延遲避免被封鎖
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"爬取 {site_config['name']} 時發生錯誤: {e}")
                continue
        
        return articles

    def _crawl_site(self, site_config, start_date, end_date, topics=None):
        """爬取單一網站"""
        articles = []
        
        try:
            response = self.session.get(site_config['url'], timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 根據選擇器找到文章
            article_elements = soup.select(site_config['selectors']['article'])
            
            for element in article_elements[:20]:  # 限制每站最多20篇文章
                try:
                    article = self._extract_article(element, site_config, start_date, end_date)
                    if article and self._is_relevant(article, topics):
                        articles.append(article)
                except Exception as e:
                    logger.warning(f"提取文章時發生錯誤: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"爬取網站時發生錯誤: {e}")
            
        return articles

    def _extract_article(self, element, site_config, start_date, end_date):
        """提取文章資訊"""
        try:
            # 提取標題和連結
            title_element = element.select_one(site_config['selectors']['title'])
            if not title_element:
                return None
                
            title = title_element.get_text(strip=True)
            link = title_element.get('href')
            
            if not link:
                return None
                
            # 處理相對連結
            if link.startswith('/'):
                from urllib.parse import urljoin
                link = urljoin(site_config['url'], link)
            
            # 提取日期
            date_element = element.select_one(site_config['selectors']['date'])
            publish_date = self._parse_date(date_element.get_text(strip=True) if date_element else '')
            
            if not publish_date:
                publish_date = datetime.now()
            
            # 檢查日期範圍
            if publish_date < start_date or publish_date > end_date:
                return None
            
            # 提取文章內容
            content = self._extract_content(link)
            
            # 提取關鍵詞
            keywords = self._extract_keywords(title + ' ' + (content or ''))
            
            return {
                'title': title,
                'content': content,
                'source': site_config['name'],
                'url': link,
                'publish_date': publish_date,
                'keywords': keywords,
                'topic': self._classify_topic(title, content, keywords)
            }
            
        except Exception as e:
            logger.warning(f"提取文章資訊時發生錯誤: {e}")
            return None

    def _extract_content(self, url):
        """提取文章內容"""
        try:
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 常見的內容選擇器
            content_selectors = [
                '.article-content',
                '.story-content',
                '.news-content',
                '.content',
                '.article-body',
                '.post-content',
                'article',
                '.main-content'
            ]
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    # 移除腳本和樣式標籤
                    for script in content_element(["script", "style"]):
                        script.decompose()
                    
                    content = content_element.get_text(strip=True)
                    if len(content) > 100:  # 確保內容足夠長
                        return content[:2000]  # 限制內容長度
            
            return None
            
        except Exception as e:
            logger.warning(f"提取內容時發生錯誤: {e}")
            return None

    def _parse_date(self, date_str):
        """解析日期字串"""
        if not date_str:
            return None
            
        # 常見的日期格式
        date_formats = [
            '%Y-%m-%d %H:%M',
            '%Y/%m/%d %H:%M',
            '%m-%d %H:%M',
            '%m/%d %H:%M',
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%m-%d',
            '%m/%d'
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str, fmt)
                # 如果是沒有年份的格式，使用當前年份
                if parsed_date.year == 1900:
                    parsed_date = parsed_date.replace(year=datetime.now().year)
                return parsed_date
            except ValueError:
                continue
        
        return None

    def _extract_keywords(self, text):
        """提取關鍵詞"""
        if not text:
            return []
        
        # 使用jieba分詞
        words = jieba.lcut(text)
        
        # 過濾停用詞和短詞
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一個', '上', '也', '很', '到', '說', '要', '去', '你', '會', '著', '沒有', '看', '好', '自己', '這', '那', '什麼', '可以', '因為', '所以', '但是', '如果', '或者', '而且', '然後', '因為', '所以', '但是', '如果', '或者', '而且', '然後'}
        
        keywords = []
        for word in words:
            if len(word) > 1 and word not in stop_words and re.match(r'[\u4e00-\u9fff]', word):
                keywords.append(word)
        
        # 返回頻率最高的前10個關鍵詞
        from collections import Counter
        return [word for word, count in Counter(keywords).most_common(10)]

    def _classify_topic(self, title, content, keywords):
        """分類主題"""
        # 簡單的主題分類邏輯
        topic_keywords = {
            '政治': ['政治', '選舉', '政府', '總統', '立法院', '政黨', '政策', '官員'],
            '經濟': ['經濟', '股市', '金融', '投資', '企業', '商業', '貿易', '就業'],
            '社會': ['社會', '犯罪', '事故', '災害', '教育', '醫療', '環保', '交通'],
            '國際': ['國際', '外交', '戰爭', '和平', '聯合國', '美國', '中國', '日本'],
            '科技': ['科技', 'AI', '人工智慧', '網路', '手機', '電腦', '創新', '數位'],
            '體育': ['體育', '運動', '足球', '籃球', '奧運', '比賽', '選手', '冠軍'],
            '娛樂': ['娛樂', '電影', '音樂', '明星', '電視', '節目', '藝人', '演出']
        }
        
        text = (title + ' ' + (content or '')).lower()
        
        topic_scores = {}
        for topic, keywords_list in topic_keywords.items():
            score = sum(1 for keyword in keywords_list if keyword in text)
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        
        return '其他'

    def _is_relevant(self, article, topics):
        """檢查文章是否相關"""
        if not topics:
            return True
        
        article_text = (article['title'] + ' ' + (article['content'] or '')).lower()
        
        for topic in topics:
            if topic.lower() in article_text:
                return True
        
        return False
