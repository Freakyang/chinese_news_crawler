from flask import Flask, render_template, request, jsonify, send_file
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
    return render_template('index.html')

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
        }
    ]
    
    # 在背景執行爬取任務
    thread = threading.Thread(target=run_crawling, args=(sample_articles,))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started', 'message': '爬取任務已開始'})

def run_crawling(articles):
    """執行爬取任務"""
    try:
        # 儲存到資料庫
        for article_data in articles:
            existing = NewsArticle.query.filter_by(url=article_data['url']).first()
            if not existing:
                news_article = NewsArticle(
                    title=article_data['title'],
                    content=article_data['content'],
                    source=article_data['source'],
                    url=article_data['url'],
                    publish_date=article_data['publish_date'],
                    topic=article_data['topic'],
                    keywords=article_data['keywords']
                )
                db.session.add(news_article)
        
        db.session.commit()
        print("示例新聞已添加到資料庫")
        
    except Exception as e:
        print(f"爬取過程中發生錯誤: {e}")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("Flask 應用程式啟動中...")
    print("請訪問: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)