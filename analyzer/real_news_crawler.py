from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import json
import threading
import time
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///news.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 資料庫模型
class NewsArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    content = db.Column(db.Text)
    source = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    publish_date = db.Column(db.DateTime, nullable=False)
    topic = db.Column(db.String(100))
    keywords = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    keyword = db.Column(db.String(100), nullable=False)
    priority = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 真實新聞爬蟲類
class RealNewsCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def crawl_news(self, keyword, max_articles=20, start_date=None, end_date=None):
        """爬取真實新聞 - 純動態搜尋"""
        articles = []
        
        print(f"🚀 開始動態搜尋關鍵詞: {keyword}")
        if start_date and end_date:
            print(f"📅 搜尋日期範圍: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}")
        
        # 首先嘗試Google搜尋
        try:
            print(f"🔍 正在Google搜尋關於 '{keyword}' 的真實新聞...")
            google_articles = self._crawl_google_news(keyword, max_articles, start_date, end_date)
            articles.extend(google_articles)
            print(f"✅ 從Google搜尋獲得 {len(google_articles)} 篇真實新聞")
        except Exception as e:
            print(f"❌ Google搜尋失敗: {e}")
        
        # 如果Google搜尋結果不足，嘗試不帶日期限制的搜尋
        if len(articles) < 5:
            print(f"🔄 Google搜尋結果不足，嘗試不帶日期限制的搜尋...")
            try:
                google_articles_no_date = self._crawl_google_news(keyword, max_articles - len(articles))
                articles.extend(google_articles_no_date)
                print(f"✅ 從無日期限制搜尋獲得 {len(google_articles_no_date)} 篇真實新聞")
            except Exception as e:
                print(f"❌ 無日期限制搜尋失敗: {e}")
        
        # 如果Google搜尋結果不足，嘗試其他新聞來源
        if len(articles) < max_articles:
            remaining = max_articles - len(articles)
            print(f"🔄 補充其他新聞來源，還需要 {remaining} 篇...")
            
            # 新聞來源列表
            news_sources = [
                {
                    'name': 'Yahoo新聞',
                    'search_url': f'https://tw.news.yahoo.com/search?p={keyword}',
                    'base_url': 'https://tw.news.yahoo.com'
                },
                {
                    'name': 'ETtoday新聞雲',
                    'search_url': f'https://www.ettoday.net/news_search/doSearch.php?keywords={keyword}',
                    'base_url': 'https://www.ettoday.net'
                }
            ]
            
            for source in news_sources:
                if len(articles) >= max_articles:
                    break
                    
                try:
                    print(f"🔍 正在爬取 {source['name']} 關於 '{keyword}' 的新聞...")
                    
                    # 發送請求
                    response = self.session.get(source['search_url'], timeout=10)
                    response.encoding = 'utf-8'
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # 根據不同網站解析新聞
                        if 'yahoo' in source['name'].lower():
                            source_articles = self._parse_yahoo_news(soup, source, keyword)
                        elif 'ettoday' in source['name'].lower():
                            source_articles = self._parse_ettoday_news(soup, source, keyword)
                        else:
                            continue
                        
                        # 避免重複文章
                        for article in source_articles:
                            if not any(existing['title'] == article['title'] for existing in articles):
                                articles.append(article)
                                if len(articles) >= max_articles:
                                    break
                    
                except Exception as e:
                    print(f"❌ 爬取 {source['name']} 時發生錯誤: {e}")
                    continue
        
        # 如果仍然沒有足夠的新聞，嘗試更多搜尋策略
        if len(articles) < 3:
            print("🔄 嘗試更多搜尋策略...")
            try:
                # 嘗試不同的搜尋詞組合
                search_variations = [
                    f"{keyword} 最新",
                    f"{keyword} 今日",
                    f"{keyword} 即時"
                ]
                
                for variation in search_variations:
                    if len(articles) >= max_articles:
                        break
                        
                    print(f"🔍 嘗試搜尋: {variation}")
                    variation_articles = self._crawl_google_news(variation, 5, start_date, end_date)
                    
                    for article in variation_articles:
                        if not any(existing['title'] == article['title'] for existing in articles):
                            articles.append(article)
                            if len(articles) >= max_articles:
                                break
                                
            except Exception as e:
                print(f"❌ 額外搜尋策略失敗: {e}")
        
        print(f"🎉 動態搜尋完成！總共獲得 {len(articles)} 篇真實新聞")
        return articles[:max_articles]
    
    def _extract_date_from_article(self, url, title, content):
        """從URL、標題或內容中提取發布日期"""
        import re
        from datetime import datetime, timedelta

        # 方法1: 從URL中提取日期 (例如: /news/20250929/...)
        url_date_match = re.search(r'/(\d{8})/', url)
        if url_date_match:
            date_str = url_date_match.group(1)
            try:
                return datetime.strptime(date_str, '%Y%m%d').date()
            except:
                pass

        # 方法2: 從URL中提取日期 (例如: /2025/09/29/...)
        url_date_match2 = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
        if url_date_match2:
            year, month, day = url_date_match2.groups()
            try:
                return datetime.strptime(f"{year}{month}{day}", '%Y%m%d').date()
            except:
                pass

        # 方法3: 從標題或內容中提取日期
        date_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',  # 2025年9月29日
            r'(\d{4})/(\d{1,2})/(\d{1,2})',      # 2025/9/29
            r'(\d{4})-(\d{1,2})-(\d{1,2})',      # 2025-9-29
        ]

        text = title + ' ' + content
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                year, month, day = match.groups()
                try:
                    return datetime.strptime(f"{year}{month.zfill(2)}{day.zfill(2)}", '%Y%m%d').date()
                except:
                    continue

        # 方法4: 從"X天前"、"X小時前"等相對時間提取
        relative_patterns = [
            r'(\d+)\s*天前',  # X天前
            r'(\d+)\s*小時前',  # X小時前
            r'(\d+)\s*分鐘前',  # X分鐘前
        ]
        
        for pattern in relative_patterns:
            match = re.search(pattern, text)
            if match:
                value = int(match.group(1))
                if '天前' in match.group(0):
                    return (datetime.now() - timedelta(days=value)).date()
                elif '小時前' in match.group(0):
                    return (datetime.now() - timedelta(hours=value)).date()
                elif '分鐘前' in match.group(0):
                    return (datetime.now() - timedelta(minutes=value)).date()

        # 如果無法提取日期，返回3天前的日期（更合理的預設值）
        fallback_date = (datetime.now() - timedelta(days=3)).date()
        print(f"⚠️ 無法從URL或內容中提取日期，使用預設日期: {fallback_date}")
        return fallback_date
    
    def _crawl_google_news(self, keyword, max_articles=20, start_date=None, end_date=None):
        """從Google搜尋結果爬取真實新聞"""
        articles = []
        try:
            # 使用多種搜尋策略來獲取更多新聞
            search_queries = [
                f"{keyword} 新聞",
                f"{keyword} 最新消息",
                f"{keyword} 報導"
            ]
            
            for query in search_queries:
                if len(articles) >= max_articles:
                    break
                    
                search_url = f"https://www.google.com/search?q={query}&tbm=nws&num=20"
                print(f"🔍 搜尋: {query}")
                
                # 發送請求
                response = self.session.get(search_url, timeout=15)
                response.encoding = 'utf-8'
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # 更精確的Google搜尋結果解析
                    news_results = []
                    
                    # 方法1: 尋找所有包含標題和連結的結果容器
                    results = soup.find_all('div', class_='g')
                    
                    # 方法2: 如果沒有找到，嘗試其他可能的容器
                    if not results:
                        results = soup.find_all('div', {'data-ved': True})
                    
                    # 方法3: 尋找所有h3標題的父容器
                    if not results:
                        h3_elements = soup.find_all('h3')
                        for h3 in h3_elements:
                            parent = h3.find_parent('div')
                            if parent and parent not in results:
                                results.append(parent)
                    
                    news_results = results
                    
                    print(f"🔍 找到 {len(news_results)} 個搜尋結果")
                    
                    for i, result in enumerate(news_results):
                        if len(articles) >= max_articles:
                            break
                            
                        try:
                            # 提取標題 - 使用多種方法
                            title = None
                            title_elem = result.find('h3')
                            if title_elem:
                                title = title_elem.get_text(strip=True)
                            
                            # 如果沒有找到h3，嘗試其他標題元素
                            if not title:
                                title_elem = result.find('a')
                                if title_elem:
                                    title = title_elem.get_text(strip=True)
                            
                            if not title or len(title) < 5:
                                continue
                            
                            # 提取連結 - 使用多種方法
                            url = None
                            link_elem = result.find('a')
                            if link_elem and link_elem.get('href'):
                                url = link_elem.get('href')
                            
                            if not url:
                                continue
                            
                            # 處理Google重定向URL
                            if url.startswith('/url?q='):
                                url = url.split('/url?q=')[1].split('&')[0]
                                url = url.replace('%3A', ':').replace('%2F', '/')
                            elif url.startswith('/search?') or url.startswith('/'):
                                continue
                            
                            # 驗證URL是否有效
                            if not url or not url.startswith('http'):
                                continue
                            
                            # 提取來源
                            source = "Google搜尋"
                            source_elem = result.find('cite')
                            if source_elem:
                                source = source_elem.get_text(strip=True)
                            
                            # 提取摘要
                            snippet = f"關於 {keyword} 的最新消息"
                            snippet_elem = result.find('span', class_='VwiC3b')
                            if not snippet_elem:
                                snippet_elem = result.find('div', class_='VwiC3b')
                            if snippet_elem:
                                snippet = snippet_elem.get_text(strip=True)
                            
                            # 檢查是否已存在相同標題的文章
                            if any(existing['title'] == title for existing in articles):
                                continue
                            
                            # 嘗試從URL或內容中提取實際發布日期
                            article_date = self._extract_date_from_article(url, title, snippet)
                            
                            # 檢查日期篩選（放寬條件，允許3天內的誤差）
                            if start_date and end_date:
                                # 計算日期範圍，允許前後3天的誤差
                                from datetime import timedelta
                                extended_start = start_date.date() - timedelta(days=3)
                                extended_end = end_date.date() + timedelta(days=3)
                                
                                if not (extended_start <= article_date <= extended_end):
                                    print(f"❌ 新聞日期 {article_date} 不在搜尋範圍內（允許±3天誤差），跳過")
                                    continue
                                else:
                                    print(f"✅ 新聞日期 {article_date} 符合搜尋範圍（允許±3天誤差）")
                            
                            # 創建文章物件
                            article = {
                                'title': title,
                                'content': snippet,
                                'source': source,
                                'url': url,
                                'publish_date': article_date,
                                'topic': self._classify_topic(title + ' ' + snippet),
                                'keywords': keyword
                            }
                            
                            articles.append(article)
                            print(f"📰 找到真實新聞: {title[:50]}...")
                            print(f"🔗 連結: {url}")
                            
                        except Exception as e:
                            print(f"❌ 解析第 {i+1} 個搜尋結果時發生錯誤: {e}")
                            continue
                
                print(f"✅ 從 '{query}' 搜尋獲得 {len(articles)} 篇新聞")
            
            print(f"🎉 總共獲得 {len(articles)} 篇真實新聞")
            return articles
            
        except Exception as e:
            print(f"❌ Google搜尋爬取失敗: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_yahoo_news(self, soup, source, keyword):
        """解析Yahoo新聞"""
        articles = []
        try:
            # 尋找新聞連結
            news_links = soup.find_all('a', href=True)
            for link in news_links[:10]:  # 限制數量
                href = link.get('href')
                if href and ('news' in href or 'story' in href):
                    title = link.get_text(strip=True)
                    if title and len(title) > 10:
                        full_url = urljoin(source['base_url'], href)
                        articles.append({
                            'title': title,
                            'content': f"關於 {keyword} 的最新消息",
                            'source': source['name'],
                            'url': full_url,
                            'publish_date': datetime.now(),
                            'topic': self._classify_topic(keyword),
                            'keywords': keyword
                        })
        except Exception as e:
            print(f"解析Yahoo新聞時發生錯誤: {e}")
        return articles
    
    def _parse_ettoday_news(self, soup, source, keyword):
        """解析ETtoday新聞"""
        articles = []
        try:
            # 尋找新聞標題和連結
            news_items = soup.find_all(['h3', 'h2', 'h1'], class_=re.compile(r'title|headline'))
            for item in news_items[:10]:
                link = item.find('a')
                if link:
                    title = link.get_text(strip=True)
                    href = link.get('href')
                    if title and href and len(title) > 10:
                        full_url = urljoin(source['base_url'], href)
                        articles.append({
                            'title': title,
                            'content': f"關於 {keyword} 的最新報導",
                            'source': source['name'],
                            'url': full_url,
                            'publish_date': datetime.now(),
                            'topic': self._classify_topic(keyword),
                            'keywords': keyword
                        })
        except Exception as e:
            print(f"解析ETtoday新聞時發生錯誤: {e}")
        return articles
    
    def _parse_chinatimes_news(self, soup, source, keyword):
        """解析中時新聞網"""
        articles = []
        try:
            # 尋找新聞標題
            news_items = soup.find_all(['h3', 'h2'], class_=re.compile(r'title|headline'))
            for item in news_items[:10]:
                link = item.find('a')
                if link:
                    title = link.get_text(strip=True)
                    href = link.get('href')
                    if title and href and len(title) > 10:
                        full_url = urljoin(source['base_url'], href)
                        articles.append({
                            'title': title,
                            'content': f"關於 {keyword} 的重要新聞",
                            'source': source['name'],
                            'url': full_url,
                            'publish_date': datetime.now(),
                            'topic': self._classify_topic(keyword),
                            'keywords': keyword
                        })
        except Exception as e:
            print(f"解析中時新聞網時發生錯誤: {e}")
        return articles
    
    def _classify_topic(self, keyword):
        """根據關鍵詞分類主題"""
        topic_keywords = {
            '政治': ['政治', '選舉', '政府', '總統', '立委', '政黨'],
            '經濟': ['經濟', '股市', '金融', '投資', 'GDP', '通膨'],
            '科技': ['科技', 'AI', '人工智慧', '5G', '半導體', '晶片'],
            '國際': ['國際', '美國', '中國', '日本', '韓國', '歐洲'],
            '社會': ['社會', '民生', '教育', '醫療', '交通', '環保'],
            '體育': ['體育', '運動', '奧運', '足球', '籃球', '棒球'],
            '娛樂': ['娛樂', '電影', '音樂', '明星', '藝人', '綜藝']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(kw in keyword for kw in keywords):
                return topic
        return '綜合'
    
    # 移除所有備用新聞資料函數，改為純動態搜尋

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>中文新聞爬蟲與主題分析系統</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <style>
            body { background-color: #f8f9fa; font-family: 'Microsoft JhengHei', sans-serif; }
            .navbar-brand { font-weight: bold; color: #2c3e50 !important; }
            .card { border: none; box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075); border-radius: 0.5rem; }
            .stats-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .stats-number { font-size: 2rem; font-weight: bold; }
            .news-item { 
                border-left: 4px solid #007bff; 
                padding: 15px; 
                margin-bottom: 15px; 
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                transition: transform 0.2s ease;
            }
            .news-item:hover { 
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }
            .news-title { 
                color: #2c3e50; 
                font-weight: bold; 
                text-decoration: none; 
                font-size: 1.1rem;
                line-height: 1.4;
                display: block;
                margin-bottom: 8px;
            }
            .news-title:hover { 
                color: #007bff; 
                text-decoration: underline; 
            }
            .news-meta { 
                color: #6c757d; 
                font-size: 0.9rem; 
                margin-bottom: 8px;
            }
            .news-content { 
                color: #495057; 
                font-size: 0.95rem; 
                line-height: 1.5;
                margin-top: 8px;
            }
            .btn-crawl { background: linear-gradient(45deg, #28a745, #20c997); border: none; }
            .btn-crawl:hover { background: linear-gradient(45deg, #218838, #1ea085); }
            .loading { display: none; }
            .topic-badge { margin: 2px; }
            .news-list-container { 
                max-height: 600px; 
                overflow-y: auto; 
                padding-right: 10px;
            }
            .search-keyword { 
                background: linear-gradient(45deg, #ff6b6b, #ee5a24); 
                color: white; 
                padding: 4px 8px; 
                border-radius: 4px; 
                font-size: 0.8rem;
                margin-right: 8px;
            }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
            <div class="container">
                <a class="navbar-brand" href="#">🌐 中文新聞爬蟲與主題分析系統</a>
            </div>
        </nav>

        <div class="container mt-4">
            <!-- 統計卡片 -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card stats-card">
                        <div class="card-body text-center">
                            <h5 class="card-title">總新聞數</h5>
                            <div class="stats-number" id="totalNews">0</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stats-card">
                        <div class="card-body text-center">
                            <h5 class="card-title">主題數量</h5>
                            <div class="stats-number" id="totalTopics">0</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stats-card">
                        <div class="card-body text-center">
                            <h5 class="card-title">今日新聞</h5>
                            <div class="stats-number" id="todayNews">0</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stats-card">
                        <div class="card-body text-center">
                            <h5 class="card-title">熱門主題</h5>
                            <div class="stats-number" id="hotTopic">-</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 控制面板 -->
            <div class="row">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5>🔍 新聞爬取設定</h5>
                        </div>
                        <div class="card-body">
                            <div class="mb-3">
                                <label class="form-label">主題關鍵詞</label>
                                <input type="text" class="form-control" id="keyword" placeholder="輸入關鍵詞，如：川普、經濟、科技">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">開始日期</label>
                                <input type="date" class="form-control" id="startDate">
                            </div>
                            <div class="mb-3">
                                <label class="form-label">結束日期</label>
                                <input type="date" class="form-control" id="endDate">
                            </div>
                            <button class="btn btn-crawl btn-lg w-100" onclick="startCrawling()">
                                <span class="loading">⏳ 爬取中...</span>
                                <span class="normal">🚀 開始爬取</span>
                            </button>
                        </div>
                    </div>
                </div>

                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h5>📰 新聞列表</h5>
                            <div>
                                <select class="form-select" id="topicFilter" onchange="filterByTopic()">
                                    <option value="">所有主題</option>
                                </select>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="news-list-container" id="newsList">
                                <p class="text-muted text-center">請輸入關鍵詞並點擊「開始爬取」來獲取新聞</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 主題分析 -->
            <div class="row mt-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5>📊 主題分析</h5>
                        </div>
                        <div class="card-body">
                            <div id="topicAnalysis">
                                <p class="text-muted text-center">爬取新聞後將顯示主題分析</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // 設置默認日期
            document.getElementById('startDate').value = new Date().toISOString().split('T')[0];
            document.getElementById('endDate').value = new Date().toISOString().split('T')[0];

            // 載入統計數據
            loadStats();
            loadTopics();

            function startCrawling() {
                const keyword = document.getElementById('keyword').value.trim();
                if (!keyword) {
                    alert('請輸入關鍵詞！');
                    return;
                }

                const startDate = document.getElementById('startDate').value;
                const endDate = document.getElementById('endDate').value;

                // 顯示載入狀態
                document.querySelector('.loading').style.display = 'inline';
                document.querySelector('.normal').style.display = 'none';

                // 發送爬取請求
                fetch('/api/crawl', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        keyword: keyword,
                        start_date: startDate,
                        end_date: endDate
                    })
                })
                .then(response => response.json())
                .then(data => {
                    console.log('爬取開始:', data);
                    // 等待3秒後重新載入數據
                    setTimeout(() => {
                        loadStats();
                        loadNews();
                        loadTopics();
                        loadTopicAnalysis();
                        
                        // 恢復按鈕狀態
                        document.querySelector('.loading').style.display = 'none';
                        document.querySelector('.normal').style.display = 'inline';
                    }, 3000);
                })
                .catch(error => {
                    console.error('錯誤:', error);
                    alert('爬取過程中發生錯誤，請稍後再試');
                    
                    // 恢復按鈕狀態
                    document.querySelector('.loading').style.display = 'none';
                    document.querySelector('.normal').style.display = 'inline';
                });
            }

            function loadStats() {
                fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('totalNews').textContent = data.total_news || 0;
                    document.getElementById('totalTopics').textContent = data.total_topics || 0;
                    document.getElementById('todayNews').textContent = data.today_news || 0;
                    document.getElementById('hotTopic').textContent = data.hot_topic || '-';
                });
            }

            function loadNews() {
                console.log('🔄 開始載入新聞...');
                fetch('/api/news?per_page=20')
                .then(response => {
                    console.log('📡 API回應狀態:', response.status);
                    return response.json();
                })
                .then(data => {
                    console.log('📰 收到新聞資料:', data);
                    console.log('📊 新聞數量:', data.length);
                    const newsList = document.getElementById('newsList');
                    if (data.length === 0) {
                        console.log('❌ 沒有新聞資料，顯示空狀態');
                        newsList.innerHTML = '<p class="text-muted text-center">暫無新聞資料</p>';
                        return;
                    }
                    console.log('✅ 開始渲染新聞列表');

                    newsList.innerHTML = data.map((article, index) => `
                        <div class="news-item">
                            <div class="d-flex justify-content-between align-items-start">
                                <div class="flex-grow-1">
                                    <a href="${article.url}" target="_blank" class="news-title">
                                        ${index + 1}. ${article.source} → ${article.title}
                                    </a>
                                    <div class="news-meta">
                                        <span class="badge bg-primary topic-badge">${article.topic || '未分類'}</span>
                                        <span class="badge bg-secondary">${article.source}</span>
                                        <span class="text-muted">${new Date(article.publish_date).toLocaleDateString()}</span>
                                    </div>
                                    <div class="news-content">
                                        <strong>內容摘要：</strong><br>
                                        ${article.content ? article.content.substring(0, 150) + '...' : '點擊標題查看完整內容'}
                                    </div>
                                </div>
                                <div class="ms-3">
                                    <a href="${article.url}" target="_blank" class="btn btn-sm btn-outline-primary">
                                        <i class="fas fa-external-link-alt"></i> 開啟
                                    </a>
                                </div>
                            </div>
                        </div>
                    `).join('');
                    console.log('🎉 新聞列表渲染完成');
                })
                .catch(error => {
                    console.error('❌ 載入新聞時發生錯誤:', error);
                    const newsList = document.getElementById('newsList');
                    newsList.innerHTML = '<p class="text-danger text-center">載入新聞時發生錯誤</p>';
                });
            }

            function loadTopics() {
                fetch('/api/topics')
                .then(response => response.json())
                .then(data => {
                    const topicFilter = document.getElementById('topicFilter');
                    topicFilter.innerHTML = '<option value="">所有主題</option>' +
                        data.map(topic => `<option value="${topic.name}">${topic.name} (${topic.count})</option>`).join('');
                });
            }

            function loadTopicAnalysis() {
                fetch('/api/topics')
                .then(response => response.json())
                .then(data => {
                    const topicAnalysis = document.getElementById('topicAnalysis');
                    if (data.length === 0) {
                        topicAnalysis.innerHTML = '<p class="text-muted text-center">暫無主題資料</p>';
                        return;
                    }

                    topicAnalysis.innerHTML = data.map(topic => `
                        <div class="d-inline-block me-3 mb-2">
                            <span class="badge bg-info fs-6">${topic.name}</span>
                            <span class="text-muted">(${topic.count}篇)</span>
                        </div>
                    `).join('');
                });
            }

            function filterByTopic() {
                const topic = document.getElementById('topicFilter').value;
                const url = topic ? `/api/news?per_page=20&topic=${encodeURIComponent(topic)}` : '/api/news?per_page=20';
                
                fetch(url)
                .then(response => response.json())
                .then(data => {
                    const newsList = document.getElementById('newsList');
                    if (data.length === 0) {
                        newsList.innerHTML = '<p class="text-muted text-center">該主題暫無新聞</p>';
                        return;
                    }

                    newsList.innerHTML = data.map((article, index) => `
                        <div class="news-item">
                            <div class="d-flex justify-content-between align-items-start">
                                <div class="flex-grow-1">
                                    <a href="${article.url}" target="_blank" class="news-title">
                                        ${index + 1}. ${article.source} → ${article.title}
                                    </a>
                                    <div class="news-meta">
                                        <span class="badge bg-primary topic-badge">${article.topic || '未分類'}</span>
                                        <span class="badge bg-secondary">${article.source}</span>
                                        <span class="text-muted">${new Date(article.publish_date).toLocaleDateString()}</span>
                                    </div>
                                    <div class="news-content">
                                        <strong>內容摘要：</strong><br>
                                        ${article.content ? article.content.substring(0, 150) + '...' : '點擊標題查看完整內容'}
                                    </div>
                                </div>
                                <div class="ms-3">
                                    <a href="${article.url}" target="_blank" class="btn btn-sm btn-outline-primary">
                                        <i class="fas fa-external-link-alt"></i> 開啟
                                    </a>
                                </div>
                            </div>
                        </div>
                    `).join('');
                });
            }

            // 初始載入新聞
            loadNews();
        </script>
    </body>
    </html>
    '''

@app.route('/api/stats')
def get_stats():
    """獲取統計數據"""
    total_news = NewsArticle.query.count()
    total_topics = db.session.query(NewsArticle.topic).filter(NewsArticle.topic.isnot(None)).distinct().count()
    today = datetime.now().date()
    today_news = NewsArticle.query.filter(db.func.date(NewsArticle.publish_date) == today).count()
    
    # 最熱門主題
    hot_topic = db.session.query(
        NewsArticle.topic,
        db.func.count(NewsArticle.id).label('count')
    ).filter(NewsArticle.topic.isnot(None)).group_by(NewsArticle.topic).order_by(db.desc('count')).first()
    
    return jsonify({
        'total_news': total_news,
        'total_topics': total_topics,
        'today_news': today_news,
        'hot_topic': hot_topic[0] if hot_topic else None
    })

@app.route('/api/news')
def get_news():
    """獲取新聞列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    topic = request.args.get('topic')
    
    query = NewsArticle.query
    if topic:
        query = query.filter(NewsArticle.topic == topic)
    
    articles = query.order_by(NewsArticle.publish_date.desc()).limit(per_page).all()
    
    return jsonify([{
        'id': article.id,
        'title': article.title,
        'content': article.content,
        'source': article.source,
        'url': article.url,
        'publish_date': article.publish_date.isoformat(),
        'topic': article.topic,
        'keywords': article.keywords
    } for article in articles])

@app.route('/api/topics')
def get_topics():
    """獲取主題列表"""
    topics = db.session.query(
        NewsArticle.topic,
        db.func.count(NewsArticle.id).label('count')
    ).filter(NewsArticle.topic.isnot(None)).group_by(NewsArticle.topic).all()
    
    return jsonify([{'name': topic[0], 'count': topic[1]} for topic in topics])

@app.route('/api/crawl', methods=['POST'])
def start_crawl():
    """開始爬取新聞"""
    data = request.get_json()
    keyword = data.get('keyword', '')
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
    
    # 在背景執行爬取任務
    thread = threading.Thread(target=run_crawling, args=(keyword, start_date, end_date))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started', 'message': f'正在爬取關於「{keyword}」的新聞...'})

def run_crawling(keyword, start_date, end_date):
    """執行真實的爬取任務"""
    with app.app_context():
        try:
            print(f"🚀 開始爬取關鍵詞: {keyword}")
            
            # 先清除舊的新聞資料
            print("🗑️ 清除舊的新聞資料...")
            NewsArticle.query.delete()
            db.session.commit()
            print("✅ 舊資料已清除")
            
            # 創建爬蟲實例
            crawler = RealNewsCrawler()
            
            # 爬取新聞
            articles = crawler.crawl_news(keyword, max_articles=20, start_date=start_date, end_date=end_date)
            
            print(f"📰 成功爬取到 {len(articles)} 篇新聞")
            
            # 儲存到資料庫
            for article in articles:
                news_article = NewsArticle(
                    title=article['title'],
                    content=article['content'],
                    source=article['source'],
                    url=article['url'],
                    publish_date=article['publish_date'],
                    topic=article['topic'],
                    keywords=article['keywords']
                )
                db.session.add(news_article)
            
            db.session.commit()
            print(f"✅ 成功儲存 {len(articles)} 篇新聞到資料庫")
            
        except Exception as e:
            print(f"❌ 爬取過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("=" * 60)
    print("🎉 中文新聞爬蟲與主題分析系統")
    print("=" * 60)
    print("正在初始化應用程式...")
    
    # 創建資料庫表
    print("📊 創建資料庫表...")
    with app.app_context():
        try:
            db.create_all()
            print("✅ 資料庫表創建完成")
            
            # 驗證表格是否創建成功
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 已創建的表格: {tables}")
        except Exception as e:
            print(f"❌ 資料庫表創建失敗: {e}")
            import traceback
            traceback.print_exc()
    
    print("🚀 Flask 應用程式啟動中...")
    print("🌐 請訪問: http://localhost:5000")
    print("⏹️  按 Ctrl+C 停止應用程式")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
