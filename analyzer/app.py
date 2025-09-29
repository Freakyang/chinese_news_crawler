from flask import Flask, render_template, render_template_string, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import json
import threading
import time

# 導入自定義模組
from real_news_crawler import RealNewsCrawler
from topic_analyzer import TopicAnalyzer
from wordcloud_generator import WordCloudGenerator

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
    count = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 初始化爬蟲和分析器
crawler = RealNewsCrawler()
analyzer = TopicAnalyzer()
wordcloud_gen = WordCloudGenerator()

# 資料庫初始化
def init_db():
    with app.app_context():
        db.create_all()
        print("📊 創建資料庫表...")
        print("✅ 資料庫表創建完成")

# 初始化資料庫
init_db()

# 主頁面
@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>中文新聞爬蟲與主題分析系統</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft JhengHei', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .search-section {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }
        
        .search-form {
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .search-input {
            flex: 1;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        .search-input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .search-btn {
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .search-btn:hover {
            transform: translateY(-2px);
        }
        
        .search-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .tabs {
            display: flex;
            background: #f8f9fa;
            border-radius: 10px;
            padding: 5px;
            margin-bottom: 20px;
        }
        
        .tab {
            flex: 1;
            padding: 15px;
            text-align: center;
            background: transparent;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 16px;
            font-weight: 500;
        }
        
        .tab.active {
            background: white;
            color: #667eea;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .news-item {
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        
        .news-item:hover {
            transform: translateY(-2px);
        }
        
        .news-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
            line-height: 1.4;
        }
        
        .news-content {
            color: #666;
            line-height: 1.6;
            margin-bottom: 10px;
        }
        
        .news-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.9em;
            color: #888;
        }
        
        .news-source {
            background: #667eea;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        
        .topic-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .topic-name {
            font-weight: 500;
            color: #333;
        }
        
        .topic-count {
            background: #667eea;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
        }
        
        .wordcloud-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .wordcloud-image {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .loading::after {
            content: '';
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid #667eea;
            border-radius: 50%;
            border-top-color: transparent;
            animation: spin 1s linear infinite;
            margin-left: 10px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .error {
            background: #ffebee;
            color: #c62828;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #c62828;
        }
        
        .success {
            background: #e8f5e8;
            color: #2e7d32;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border-left: 4px solid #2e7d32;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .search-form {
                flex-direction: column;
            }
            
            .tabs {
                flex-direction: column;
            }
            
            .stats-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 中文新聞爬蟲與主題分析系統</h1>
            <p>即時爬取中文新聞，進行主題分析和詞雲生成</p>
        </div>
        
        <div class="search-section">
            <form class="search-form" id="searchForm">
                <input type="text" class="search-input" id="keywordInput" placeholder="請輸入搜尋關鍵詞，例如：台灣、科技、政治..." required>
                <button type="submit" class="search-btn" id="searchBtn">🔍 開始爬取</button>
            </form>
            
            <div class="tabs">
                <button class="tab active" data-tab="news">📰 新聞列表</button>
                <button class="tab" data-tab="topics">📊 主題分析</button>
                <button class="tab" data-tab="wordcloud">☁️ 詞雲圖</button>
                <button class="tab" data-tab="stats">📈 統計數據</button>
            </div>
            
            <div id="message"></div>
            
            <div class="tab-content active" id="news-tab">
                <div id="newsList" class="loading">正在載入新聞...</div>
            </div>
            
            <div class="tab-content" id="topics-tab">
                <div id="topicsList" class="loading">正在載入主題分析...</div>
            </div>
            
            <div class="tab-content" id="wordcloud-tab">
                <div id="wordcloudContainer" class="loading">正在生成詞雲圖...</div>
            </div>
            
            <div class="tab-content" id="stats-tab">
                <div id="statsContainer" class="loading">正在載入統計數據...</div>
            </div>
        </div>
    </div>

    <script>
        // 標籤切換功能
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                // 移除所有活動狀態
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                
                // 添加活動狀態
                tab.classList.add('active');
                document.getElementById(tab.dataset.tab + '-tab').classList.add('active');
                
                // 載入對應內容
                loadTabContent(tab.dataset.tab);
            });
        });
        
        // 搜尋功能
        document.getElementById('searchForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const keyword = document.getElementById('keywordInput').value.trim();
            if (!keyword) return;
            
            const searchBtn = document.getElementById('searchBtn');
            const messageDiv = document.getElementById('message');
            
            searchBtn.disabled = true;
            searchBtn.textContent = '🔄 爬取中...';
            messageDiv.innerHTML = '<div class="loading">正在爬取新聞，請稍候...</div>';
            
            try {
                const response = await fetch('/api/crawl', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ keyword: keyword })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    messageDiv.innerHTML = `<div class="success">✅ 成功爬取 ${result.count} 篇新聞！</div>`;
                    // 重新載入所有標籤內容
                    loadAllContent();
                } else {
                    messageDiv.innerHTML = `<div class="error">❌ 爬取失敗：${result.message}</div>`;
                }
            } catch (error) {
                messageDiv.innerHTML = `<div class="error">❌ 網路錯誤：${error.message}</div>`;
            } finally {
                searchBtn.disabled = false;
                searchBtn.textContent = '🔍 開始爬取';
            }
        });
        
        // 載入標籤內容
        async function loadTabContent(tabName) {
            const container = document.getElementById(tabName + (tabName === 'stats' ? 'Container' : tabName === 'wordcloud' ? 'Container' : 'List'));
            
            try {
                let response, data;
                
                switch(tabName) {
                    case 'news':
                        response = await fetch('/api/news');
                        data = await response.json();
                        displayNews(data.news);
                        break;
                    case 'topics':
                        response = await fetch('/api/topics');
                        data = await response.json();
                        displayTopics(data);
                        break;
                    case 'wordcloud':
                        response = await fetch('/api/wordcloud');
                        data = await response.json();
                        displayWordcloud(data.wordcloud);
                        break;
                    case 'stats':
                        response = await fetch('/api/stats');
                        data = await response.json();
                        displayStats(data);
                        break;
                }
            } catch (error) {
                container.innerHTML = `<div class="error">❌ 載入失敗：${error.message}</div>`;
            }
        }
        
        // 載入所有內容
        function loadAllContent() {
            loadTabContent('news');
            loadTabContent('topics');
            loadTabContent('wordcloud');
            loadTabContent('stats');
        }
        
        // 顯示新聞列表
        function displayNews(news) {
            const container = document.getElementById('newsList');
            
            if (!news || news.length === 0) {
                container.innerHTML = '<div class="loading">暫無新聞資料</div>';
                return;
            }
            
            container.innerHTML = news.map(item => `
                <div class="news-item">
                    <div class="news-title">${item.title}</div>
                    <div class="news-content">${item.content}</div>
                    <div class="news-meta">
                        <span class="news-source">${item.source}</span>
                        <span>${item.publish_date}</span>
                    </div>
                </div>
            `).join('');
        }
        
        // 顯示主題分析
        function displayTopics(data) {
            const container = document.getElementById('topicsList');
            
            if (!data.topics || Object.keys(data.topics).length === 0) {
                container.innerHTML = '<div class="loading">暫無主題資料</div>';
                return;
            }
            
            const topics = Object.entries(data.topics)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10);
            
            container.innerHTML = topics.map(([topic, count]) => `
                <div class="topic-item">
                    <span class="topic-name">${topic}</span>
                    <span class="topic-count">${count}</span>
                </div>
            `).join('');
        }
        
        // 顯示詞雲圖
        function displayWordcloud(wordcloudData) {
            const container = document.getElementById('wordcloudContainer');
            
            if (!wordcloudData) {
                container.innerHTML = '<div class="loading">暫無詞雲資料</div>';
                return;
            }
            
            container.innerHTML = `
                <div class="wordcloud-container">
                    <img src="data:image/png;base64,${wordcloudData}" alt="詞雲圖" class="wordcloud-image">
                </div>
            `;
        }
        
        // 顯示統計數據
        function displayStats(stats) {
            const container = document.getElementById('statsContainer');
            
            container.innerHTML = `
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">${stats.total_news || 0}</div>
                        <div class="stat-label">總新聞數</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${stats.total_topics || 0}</div>
                        <div class="stat-label">主題數量</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${stats.total_sources || 0}</div>
                        <div class="stat-label">新聞來源</div>
                    </div>
                </div>
            `;
        }
        
        // 頁面載入時載入所有內容
        document.addEventListener('DOMContentLoaded', loadAllContent);
    </script>
</body>
</html>
    ''')

# API 路由
@app.route('/api/crawl', methods=['POST'])
def api_crawl():
    data = request.get_json()
    keyword = data.get('keyword', '')
    
    if not keyword:
        return jsonify({'success': False, 'message': '請提供關鍵詞'})
    
    try:
        print(f"🚀 開始爬取關鍵詞: {keyword}")
        count = crawler.crawl_news(keyword)
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        print(f"❌ 爬取失敗: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/news')
def api_news():
    try:
        with app.app_context():
            news = NewsArticle.query.order_by(NewsArticle.created_at.desc()).limit(20).all()
            return jsonify({
                'news': [{
                    'title': item.title,
                    'content': item.content,
                    'source': item.source,
                    'url': item.url,
                    'publish_date': item.publish_date.strftime('%Y-%m-%d') if item.publish_date else '',
                    'topic': item.topic
                } for item in news]
            })
    except Exception as e:
        print(f"❌ 載入新聞失敗: {e}")
        return jsonify({'news': []})

@app.route('/api/stats')
def api_stats():
    try:
        with app.app_context():
            total_news = NewsArticle.query.count()
            total_topics = db.session.query(NewsArticle.topic).distinct().count()
            total_sources = db.session.query(NewsArticle.source).distinct().count()
            
            return jsonify({
                'total_news': total_news,
                'total_topics': total_topics,
                'total_sources': total_sources
            })
    except Exception as e:
        print(f"❌ 載入統計失敗: {e}")
        return jsonify({
            'total_news': 0,
            'total_topics': 0,
            'total_sources': 0
        })

@app.route('/api/topics')
def api_topics():
    try:
        with app.app_context():
            articles = NewsArticle.query.all()
            analysis = analyzer.analyze_topics(articles)
            
            # 轉換為前端需要的格式
            topics = {}
            for topic, stats in analysis['topic_stats'].items():
                topics[topic] = stats['count']
            
            return jsonify({'topics': topics, 'keywords': []})
    except Exception as e:
        print(f"❌ 主題分析失敗: {e}")
        return jsonify({'topics': {}, 'keywords': []})

@app.route('/api/wordcloud')
def api_wordcloud():
    try:
        with app.app_context():
            articles = NewsArticle.query.all()
            if not articles:
                return jsonify({'wordcloud': None})
            
            # 提取所有文章的文字
            texts = []
            for article in articles:
                text = article.title + ' ' + (article.content or '')
                texts.append(text)
            
            # 生成詞雲
            wordcloud_path = wordcloud_gen.generate_wordcloud(texts)
            
            if wordcloud_path and os.path.exists(wordcloud_path):
                # 讀取圖片並轉換為base64
                with open(wordcloud_path, 'rb') as f:
                    import base64
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                    return jsonify({'wordcloud': image_data})
            else:
                return jsonify({'wordcloud': None})
                
    except Exception as e:
        print(f"❌ 詞雲生成失敗: {e}")
        return jsonify({'wordcloud': None})

if __name__ == '__main__':
    print("=" * 60)
    print("🎉 中文新聞爬蟲與主題分析系統")
    print("=" * 60)
    print("正在初始化應用程式...")
    print("🚀 Flask 應用程式啟動中...")
    print("🌐 請訪問: http://localhost:5000")
    print("⏹️  按 Ctrl+C 停止應用程式")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)