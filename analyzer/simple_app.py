from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
import json
import threading
import time

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
        <style>
            body { background-color: #f8f9fa; font-family: 'Microsoft JhengHei', sans-serif; }
            .navbar-brand { font-weight: bold; color: #2c3e50 !important; }
            .card { border: none; box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075); border-radius: 0.5rem; }
            .stats-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
            .stats-number { font-size: 2rem; font-weight: bold; }
        </style>
    </head>
    <body>
        <nav class="navbar navbar-expand-lg navbar-light bg-white shadow-sm">
            <div class="container">
                <a class="navbar-brand" href="#">
                    📰 中文新聞爬蟲與主題分析系統
                </a>
            </div>
        </nav>

        <div class="container mt-4">
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            ⚙️ 爬蟲設定
                        </div>
                        <div class="card-body">
                            <form id="crawl-form">
                                <div class="row">
                                    <div class="col-md-3">
                                        <label for="start-date" class="form-label">開始日期</label>
                                        <input type="date" class="form-control" id="start-date" required>
                                    </div>
                                    <div class="col-md-3">
                                        <label for="end-date" class="form-label">結束日期</label>
                                        <input type="date" class="form-control" id="end-date" required>
                                    </div>
                                    <div class="col-md-4">
                                        <label for="topics" class="form-label">主題關鍵詞</label>
                                        <input type="text" class="form-control" id="topics" placeholder="例如：政治,經濟,科技">
                                    </div>
                                    <div class="col-md-2 d-flex align-items-end">
                                        <button type="submit" class="btn btn-primary w-100">🚀 開始爬取</button>
                                    </div>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card stats-card">
                        <div class="card-body text-center">
                            <div class="stats-number" id="total-articles">0</div>
                            <div>總文章數</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stats-card">
                        <div class="card-body text-center">
                            <div class="stats-number" id="total-topics">0</div>
                            <div>主題數量</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stats-card">
                        <div class="card-body text-center">
                            <div class="stats-number" id="total-sources">0</div>
                            <div>新聞來源</div>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card stats-card">
                        <div class="card-body text-center">
                            <div class="stats-number" id="hot-topic">-</div>
                            <div>最熱門主題</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">📊 主題列表</div>
                        <div class="card-body" style="max-height: 400px; overflow-y: auto;">
                            <div id="topics-list">
                                <div class="text-center text-muted">載入中...</div>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">📰 新聞列表</div>
                        <div class="card-body" style="max-height: 400px; overflow-y: auto;">
                            <div id="news-list">
                                <div class="text-center text-muted">載入中...</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            let currentTopic = null;

            document.addEventListener('DOMContentLoaded', function() {
                const today = new Date();
                const yesterday = new Date(today);
                yesterday.setDate(yesterday.getDate() - 1);
                
                document.getElementById('start-date').value = yesterday.toISOString().split('T')[0];
                document.getElementById('end-date').value = today.toISOString().split('T')[0];
                
                loadStats();
                loadTopics();
                loadNews();
            });

            document.getElementById('crawl-form').addEventListener('submit', function(e) {
                e.preventDefault();
                
                const startDate = document.getElementById('start-date').value;
                const endDate = document.getElementById('end-date').value;
                const topics = document.getElementById('topics').value.split(',').map(t => t.trim()).filter(t => t);
                
                startCrawling(startDate, endDate, topics);
            });

            function startCrawling(startDate, endDate, topics) {
                fetch('/api/crawl', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        start_date: startDate,
                        end_date: endDate,
                        topics: topics
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'started') {
                        alert('爬取任務已開始！');
                        setTimeout(() => {
                            loadStats();
                            loadTopics();
                            loadNews();
                        }, 2000);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('爬取過程中發生錯誤');
                });
            }

            function loadStats() {
                fetch('/api/news?per_page=1')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-articles').textContent = data.total || 0;
                })
                .catch(error => console.error('Error loading stats:', error));
                
                fetch('/api/topics')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('total-topics').textContent = data.length;
                    if (data.length > 0) {
                        const topTopic = data.reduce((max, topic) => topic.count > max.count ? topic : max, data[0]);
                        document.getElementById('hot-topic').textContent = topTopic.name;
                    }
                })
                .catch(error => console.error('Error loading topics:', error));
            }

            function loadTopics() {
                fetch('/api/topics')
                .then(response => response.json())
                .then(data => {
                    const topicsList = document.getElementById('topics-list');
                    if (data.length === 0) {
                        topicsList.innerHTML = '<div class="text-center text-muted">暫無主題資料</div>';
                        return;
                    }
                    
                    topicsList.innerHTML = data.map(topic => `
                        <div class="p-2 border-bottom" onclick="selectTopic('${topic.name}')" style="cursor: pointer;">
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <h6 class="mb-1">${topic.name}</h6>
                                    <small class="text-muted">${topic.count} 篇文章</small>
                                </div>
                                <span class="badge bg-primary">${topic.count}</span>
                            </div>
                        </div>
                    `).join('');
                })
                .catch(error => {
                    console.error('Error loading topics:', error);
                    document.getElementById('topics-list').innerHTML = '<div class="text-center text-danger">載入失敗</div>';
                });
            }

            function selectTopic(topicName) {
                currentTopic = topicName;
                loadNews(topicName);
            }

            function loadNews(topic = null) {
                const newsList = document.getElementById('news-list');
                newsList.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"></div> 載入中...</div>';
                
                let url = '/api/news?per_page=20';
                if (topic) {
                    url += `&topic=${encodeURIComponent(topic)}`;
                }
                
                fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data.articles.length === 0) {
                        newsList.innerHTML = '<div class="text-center text-muted">暫無新聞資料</div>';
                        return;
                    }
                    
                    newsList.innerHTML = data.articles.map(article => `
                        <div class="p-3 border-bottom">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h6 class="mb-1 flex-grow-1">
                                    <a href="${article.url}" target="_blank" class="text-decoration-none">
                                        ${article.title}
                                    </a>
                                </h6>
                                <span class="badge bg-secondary">${article.source}</span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center">
                                <small class="text-muted">
                                    ${new Date(article.publish_date).toLocaleDateString('zh-TW')}
                                </small>
                                ${article.topic ? `<span class="badge bg-info">${article.topic}</span>` : ''}
                            </div>
                        </div>
                    `).join('');
                })
                .catch(error => {
                    console.error('Error loading news:', error);
                    newsList.innerHTML = '<div class="text-center text-danger">載入失敗</div>';
                });
            }
        </script>
    </body>
    </html>
    '''

@app.route('/api/news')
def get_news():
    """獲取新聞列表"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    topic = request.args.get('topic')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    query = NewsArticle.query
    
    if start_date:
        query = query.filter(NewsArticle.publish_date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(NewsArticle.publish_date <= datetime.strptime(end_date, '%Y-%m-%d'))
    if topic:
        query = query.filter(NewsArticle.topic.contains(topic))
    
    articles = query.order_by(NewsArticle.publish_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'articles': [{
            'id': article.id,
            'title': article.title,
            'source': article.source,
            'url': article.url,
            'publish_date': article.publish_date.isoformat(),
            'topic': article.topic,
            'keywords': article.keywords
        } for article in articles.items],
        'total': articles.total,
        'pages': articles.pages,
        'current_page': page
    })

@app.route('/api/topics')
def get_topics():
    """獲取主題統計"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = NewsArticle.query
    if start_date:
        query = query.filter(NewsArticle.publish_date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(NewsArticle.publish_date <= datetime.strptime(end_date, '%Y-%m-%d'))
    
    # 統計主題
    topics = db.session.query(
        NewsArticle.topic,
        db.func.count(NewsArticle.id).label('count')
    ).filter(NewsArticle.topic.isnot(None)).group_by(NewsArticle.topic).all()
    
    return jsonify([{'name': topic[0], 'count': topic[1]} for topic in topics])

@app.route('/api/crawl', methods=['POST'])
def start_crawl():
    """開始爬取新聞"""
    data = request.get_json()
    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
    topics = data.get('topics', [])
    
    # 在背景執行爬取任務
    thread = threading.Thread(target=run_crawling, args=(start_date, end_date, topics))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started', 'message': '爬取任務已開始'})

def run_crawling(start_date, end_date, topics):
    """執行爬取任務"""
    with app.app_context():
        try:
            # 添加一些示例新聞
            sample_articles = [
                {
                    'title': '台灣經濟成長率創新高',
                    'content': '台灣經濟在第三季度表現優異，成長率達到3.2%，創下近年來新高。',
                    'source': '示例新聞網',
                    'url': 'https://example.com/news1',
                    'publish_date': datetime.now(),
                    'topic': '經濟',
                    'keywords': '經濟,成長,台灣'
                },
                {
                    'title': '科技創新推動產業轉型',
                    'content': '人工智慧和物聯網技術的發展，正在推動傳統產業的數位轉型。',
                    'source': '科技日報',
                    'url': 'https://example.com/news2',
                    'publish_date': datetime.now(),
                    'topic': '科技',
                    'keywords': '科技,AI,創新'
                },
                {
                    'title': '環保政策獲得民眾支持',
                    'content': '最新的環保政策調查顯示，超過80%的民眾支持政府推動的綠色能源政策。',
                    'source': '環保時報',
                    'url': 'https://example.com/news3',
                    'publish_date': datetime.now(),
                    'topic': '環境',
                    'keywords': '環保,政策,能源'
                },
                {
                    'title': '體育賽事精彩紛呈',
                    'content': '本週的體育賽事精彩紛呈，多項比賽創下新紀錄。',
                    'source': '體育週報',
                    'url': 'https://example.com/news4',
                    'publish_date': datetime.now(),
                    'topic': '體育',
                    'keywords': '體育,比賽,紀錄'
                },
                {
                    'title': '國際局勢持續關注',
                    'content': '國際局勢持續受到關注，各國領導人進行重要會談。',
                    'source': '國際時報',
                    'url': 'https://example.com/news5',
                    'publish_date': datetime.now(),
                    'topic': '國際',
                    'keywords': '國際,局勢,會談'
                }
            ]
            
            # 儲存到資料庫
            for article in sample_articles:
                existing = NewsArticle.query.filter_by(url=article['url']).first()
                if not existing:
                    news_article = NewsArticle(
                        title=article['title'],
                        content=article['content'],
                        source=article['source'],
                        url=article['url'],
                        publish_date=article['publish_date'],
                        topic=article.get('topic', ''),
                        keywords=article.get('keywords', '')
                    )
                    db.session.add(news_article)
            
            db.session.commit()
            print("✅ 示例新聞已添加到資料庫")
            
        except Exception as e:
            print(f"❌ 爬取過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("=" * 60)
    print("🎉 中文新聞爬蟲與主題分析系統")
    print("=" * 60)
    print("正在初始化應用程式...")
    
    try:
        with app.app_context():
            print("📊 創建資料庫表...")
            db.create_all()
            print("✅ 資料庫表創建完成")
        
        print("🚀 Flask 應用程式啟動中...")
        print("🌐 請訪問: http://localhost:5000")
        print("⏹️  按 Ctrl+C 停止應用程式")
        print("=" * 60)
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        print(f"❌ 啟動應用程式時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
