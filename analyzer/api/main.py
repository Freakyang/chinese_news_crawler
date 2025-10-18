from flask import Flask, render_template_string, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# 全域變數儲存新聞資料
news_data = []

# 簡化的爬蟲功能
def crawl_news(keyword):
    """簡化的新聞爬蟲功能"""
    print(f"[開始] 爬取關鍵詞: {keyword}")
    
    # 模擬新聞數據
    mock_news = [
        {
            'title': f'{keyword}相關新聞：重要發展動態',
            'content': f'關於{keyword}的最新報導，涉及重要發展動態。這則新聞提供了詳細的分析和背景資訊，幫助讀者了解相關議題的最新動態。',
            'source': '中央社',
            'url': f'https://example.com/news/{keyword}/1',
            'publish_date': datetime.now().strftime('%Y-%m-%d'),
            'topic': '政治'
        },
        {
            'title': f'{keyword}最新消息：市場表現亮眼',
            'content': f'關於{keyword}的最新消息，市場表現亮眼。相關產業發展趨勢良好，為投資者帶來新的機會。',
            'source': '經濟日報',
            'url': f'https://example.com/news/{keyword}/2',
            'publish_date': datetime.now().strftime('%Y-%m-%d'),
            'topic': '經濟'
        },
        {
            'title': f'{keyword}技術突破：創新發展',
            'content': f'關於{keyword}的技術突破，展現創新發展潛力。相關技術應用前景廣闊，為行業帶來新的變革。',
            'source': '科技新報',
            'url': f'https://example.com/news/{keyword}/3',
            'publish_date': datetime.now().strftime('%Y-%m-%d'),
            'topic': '科技'
        },
        {
            'title': f'{keyword}社會議題：民眾關注焦點',
            'content': f'關於{keyword}的社會議題持續受到民眾關注。相關討論在社會各界引起廣泛迴響，值得深入探討。',
            'source': '聯合報',
            'url': f'https://example.com/news/{keyword}/4',
            'publish_date': datetime.now().strftime('%Y-%m-%d'),
            'topic': '社會'
        },
        {
            'title': f'{keyword}國際視角：全球影響力',
            'content': f'從國際視角來看，{keyword}在全球範圍內具有重要影響力。相關發展趨勢值得持續關注。',
            'source': 'BBC中文',
            'url': f'https://example.com/news/{keyword}/5',
            'publish_date': datetime.now().strftime('%Y-%m-%d'),
            'topic': '國際'
        }
    ]
    
    # 更新全域變數
    global news_data
    news_data = mock_news
    
    print(f"[成功] 儲存 {len(mock_news)} 篇新聞")
    return len(mock_news)

# HTML 模板
HTML_TEMPLATE = '''
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
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .search-section {
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }
        
        .search-form {
            display: flex;
            gap: 15px;
            max-width: 600px;
            margin: 0 auto;
        }
        
        .search-input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e9ecef;
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
        
        .tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }
        
        .tab {
            flex: 1;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
            font-size: 18px;
            font-weight: 500;
        }
        
        .tab.active {
            background: white;
            border-bottom-color: #667eea;
            color: #667eea;
        }
        
        .tab:hover {
            background: #e9ecef;
        }
        
        .content {
            padding: 30px;
            min-height: 400px;
        }
        
        .news-item {
            background: white;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }
        
        .news-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        }
        
        .news-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
            line-height: 1.4;
        }
        
        .news-content {
            color: #666;
            line-height: 1.6;
            margin-bottom: 15px;
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
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 0.8em;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .stat-label {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .loading {
            text-align: center;
            padding: 50px;
            color: #666;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .success {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        @media (max-width: 768px) {
            .search-form {
                flex-direction: column;
            }
            
            .tabs {
                flex-direction: column;
            }
            
            .tab {
                border-bottom: 1px solid #e9ecef;
                border-right: none;
            }
            
            .tab.active {
                border-bottom-color: #667eea;
                border-right: none;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>[新聞] 中文新聞爬蟲與主題分析系統</h1>
            <p>即時搜尋、分析與視覺化中文新聞內容</p>
        </div>
        
        <div class="search-section">
            <form class="search-form" id="searchForm">
                <input type="text" class="search-input" id="keywordInput" placeholder="請輸入搜尋關鍵詞，例如：台灣、科技、政治..." required>
                <button type="submit" class="search-btn">[搜尋] 開始搜尋</button>
            </form>
        </div>
        
        <div class="tabs">
            <div class="tab active" data-tab="news">[新聞] 新聞列表</div>
            <div class="tab" data-tab="topics">[分析] 主題分析</div>
            <div class="tab" data-tab="wordcloud">[詞雲] 詞雲圖</div>
            <div class="tab" data-tab="stats">[統計] 統計數據</div>
        </div>
        
        <div class="content">
            <div id="newsTab" class="tab-content">
                <div class="loading">請輸入關鍵詞開始搜尋新聞...</div>
            </div>
            
            <div id="topicsTab" class="tab-content" style="display: none;">
                <div class="loading">載入主題分析中...</div>
            </div>
            
            <div id="wordcloudTab" class="tab-content" style="display: none;">
                <div class="loading">載入詞雲圖中...</div>
            </div>
            
            <div id="statsTab" class="tab-content" style="display: none;">
                <div class="loading">載入統計數據中...</div>
            </div>
        </div>
    </div>

    <script>
        let currentTab = 'news';
        
        // 標籤切換
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const tabName = tab.dataset.tab;
                switchTab(tabName);
            });
        });
        
        function switchTab(tabName) {
            // 更新標籤狀態
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
            
            // 更新內容顯示
            document.querySelectorAll('.tab-content').forEach(content => {
                content.style.display = 'none';
            });
            document.getElementById(tabName + 'Tab').style.display = 'block';
            
            currentTab = tabName;
            
            // 載入對應數據
            loadTabData(tabName);
        }
        
        function loadTabData(tabName) {
            switch(tabName) {
                case 'news':
                    loadNews();
                    break;
                case 'topics':
                    loadTopics();
                    break;
                case 'wordcloud':
                    loadWordCloud();
                    break;
                case 'stats':
                    loadStats();
                    break;
            }
        }
        
        // 搜尋表單處理
        document.getElementById('searchForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const keyword = document.getElementById('keywordInput').value.trim();
            
            if (!keyword) return;
            
            try {
                const response = await fetch('/api/crawl', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ keyword })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showMessage(`[成功] 爬取 ${result.count} 篇新聞！`, 'success');
                    loadNews();
                } else {
                    showMessage(`[錯誤] 爬取失敗: ${result.message}`, 'error');
                }
            } catch (error) {
                showMessage(`[錯誤] 網路錯誤: ${error.message}`, 'error');
            }
        });
        
        async function loadNews() {
            try {
                const response = await fetch('/api/news');
                const data = await response.json();
                
                const container = document.getElementById('newsTab');
                
                if (data.news && data.news.length > 0) {
                    container.innerHTML = data.news.map(news => `
                        <div class="news-item">
                            <div class="news-title">${news.title}</div>
                            <div class="news-content">${news.content || '無內容'}</div>
                            <div class="news-meta">
                                <span class="news-source">${news.source}</span>
                                <span>${news.publish_date}</span>
                            </div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<div class="loading">暫無新聞資料，請先進行搜尋。</div>';
                }
            } catch (error) {
                document.getElementById('newsTab').innerHTML = `<div class="error">載入新聞失敗: ${error.message}</div>`;
            }
        }
        
        async function loadTopics() {
            try {
                const response = await fetch('/api/topics');
                const data = await response.json();
                
                const container = document.getElementById('topicsTab');
                
                if (data.topics && Object.keys(data.topics).length > 0) {
                    container.innerHTML = Object.entries(data.topics).map(([topic, count]) => `
                        <div class="news-item">
                            <div class="news-title">${topic}</div>
                            <div class="news-content">相關新聞數量: ${count}</div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<div class="loading">暫無主題分析資料。</div>';
                }
            } catch (error) {
                document.getElementById('topicsTab').innerHTML = `<div class="error">載入主題分析失敗: ${error.message}</div>`;
            }
        }
        
        async function loadWordCloud() {
            try {
                const response = await fetch('/api/wordcloud');
                const data = await response.json();
                
                const container = document.getElementById('wordcloudTab');
                
                if (data.wordcloud) {
                    container.innerHTML = `
                        <div style="text-align: center;">
                            <img src="data:image/png;base64,${data.wordcloud}" style="max-width: 100%; height: auto;" alt="詞雲圖">
                        </div>
                    `;
                } else {
                    container.innerHTML = '<div class="loading">暫無詞雲圖資料。</div>';
                }
            } catch (error) {
                document.getElementById('wordcloudTab').innerHTML = `<div class="error">載入詞雲圖失敗: ${error.message}</div>`;
            }
        }
        
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                const container = document.getElementById('statsTab');
                
                container.innerHTML = `
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number">${data.total_news || 0}</div>
                            <div class="stat-label">總新聞數</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${data.total_topics || 0}</div>
                            <div class="stat-label">主題數量</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">${data.total_sources || 0}</div>
                            <div class="stat-label">新聞來源</div>
                        </div>
                    </div>
                `;
            } catch (error) {
                document.getElementById('statsTab').innerHTML = `<div class="error">載入統計數據失敗: ${error.message}</div>`;
            }
        }
        
        function showMessage(message, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = type;
            messageDiv.textContent = message;
            
            const content = document.querySelector('.content');
            content.insertBefore(messageDiv, content.firstChild);
            
            setTimeout(() => {
                messageDiv.remove();
            }, 5000);
        }
        
        // 初始載入
        loadTabData(currentTab);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/crawl', methods=['POST'])
def api_crawl():
    data = request.get_json()
    keyword = data.get('keyword', '')
    
    if not keyword:
        return jsonify({'success': False, 'message': '請提供關鍵詞'})
    
    try:
        count = crawl_news(keyword)
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        print(f"[錯誤] 爬取失敗: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/news')
def api_news():
    try:
        return jsonify({'news': news_data})
    except Exception as e:
        print(f"[錯誤] 載入新聞失敗: {e}")
        return jsonify({'news': []})

@app.route('/api/stats')
def api_stats():
    try:
        total_news = len(news_data)
        topics = set(news['topic'] for news in news_data)
        sources = set(news['source'] for news in news_data)
        
        return jsonify({
            'total_news': total_news,
            'total_topics': len(topics),
            'total_sources': len(sources)
        })
    except Exception as e:
        print(f"[錯誤] 載入統計失敗: {e}")
        return jsonify({
            'total_news': 0,
            'total_topics': 0,
            'total_sources': 0
        })

@app.route('/api/topics')
def api_topics():
    try:
        topics = {}
        for news in news_data:
            topic = news.get('topic', '未分類')
            topics[topic] = topics.get(topic, 0) + 1
        
        return jsonify({'topics': topics, 'keywords': []})
    except Exception as e:
        print(f"[錯誤] 主題分析失敗: {e}")
        return jsonify({'topics': {}, 'keywords': []})

@app.route('/api/wordcloud')
def api_wordcloud():
    try:
        # 簡化的詞雲生成
        wordcloud_data = None
        return jsonify({'wordcloud': wordcloud_data})
    except Exception as e:
        print(f"[錯誤] 詞雲生成失敗: {e}")
        return jsonify({'wordcloud': None})

# Vercel 無伺服器函數處理器
def handler(request):
    return app(request.environ, lambda *args: None)

# 導出處理器供 Vercel 使用
if __name__ == '__main__':
    app.run(debug=True)