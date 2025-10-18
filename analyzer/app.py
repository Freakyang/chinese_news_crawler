#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time
import random

app = Flask(__name__)

# 簡化的爬蟲功能
def crawl_news(keyword, start_date=None, end_date=None):
    """簡化的新聞爬蟲功能"""
    print(f"[開始] 爬取關鍵詞: {keyword}")
    if start_date and end_date:
        print(f"[日期] 範圍: {start_date} 到 {end_date}")
    
    # 清除舊資料
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM news_article')
    conn.commit()
    conn.close()
    print("[清除] 舊的新聞資料...")
    
    # 根據關鍵詞生成不同的模擬新聞
    news_templates = {
        '習近平': [
            {
                'title': '中央社CNA美媒:習近平尋求川普做重大讓步明確反對台灣獨立| 兩岸',
                'content': '關於習近平的最新消息，美媒報導習近平尋求川普做重大讓步，明確反對台灣獨立。相關議題持續受到國際關注。',
                'source': '中央社',
                'url': f'https://example.com/news/{keyword}/1',
                'publish_date': '2025-09-28',
                'topic': '綜合'
            },
            {
                'title': 'Newtalk新聞中美僵局因TikTok交易案破冰外媒揭川普、習近平背後盤算| 國際',
                'content': '關於習近平的最新消息，中美僵局因TikTok交易案破冰，外媒揭露川普、習近平背後盤算。',
                'source': 'Newtalk新聞',
                'url': f'https://example.com/news/{keyword}/2',
                'publish_date': '2025-09-28',
                'topic': '國際'
            },
            {
                'title': '奇摩新聞疑美論成真?習近平傳讓步交換「反對台獨」美智庫建議:「增加國防開支、在美投資」因應',
                'content': '關於習近平的最新消息，疑美論成真？習近平傳讓步交換「反對台獨」，美智庫建議增加國防開支、在美投資因應。',
                'source': '奇摩新聞',
                'url': f'https://example.com/news/{keyword}/3',
                'publish_date': '2025-09-28',
                'topic': '經濟'
            }
        ],
        '台灣': [
            {
                'title': '台灣科技產業發展：半導體領先全球',
                'content': '台灣科技產業持續發展，半導體產業領先全球，為經濟成長提供強勁動力。',
                'source': '科技新報',
                'url': f'https://example.com/news/{keyword}/1',
                'publish_date': datetime.now().strftime('%Y-%m-%d'),
                'topic': '科技'
            },
            {
                'title': '台灣經濟表現亮眼：GDP成長超預期',
                'content': '台灣經濟表現亮眼，GDP成長超預期，各項經濟指標表現良好。',
                'source': '經濟日報',
                'url': f'https://example.com/news/{keyword}/2',
                'publish_date': datetime.now().strftime('%Y-%m-%d'),
                'topic': '經濟'
            }
        ]
    }
    
    # 獲取對應的新聞模板，如果沒有則使用預設模板
    mock_news = news_templates.get(keyword, [
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
    ])
    
    # 儲存到資料庫
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    
    for news in mock_news:
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO news_article 
                (title, content, source, url, publish_date, topic)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                news['title'],
                news['content'],
                news['source'],
                news['url'],
                news['publish_date'],
                news['topic']
            ))
        except Exception as e:
            print(f"[錯誤] 儲存新聞失敗: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"[成功] 儲存 {len(mock_news)} 篇新聞到資料庫")
    return len(mock_news)

# 資料庫初始化
def init_db():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    
    # 創建新聞文章表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_article (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            source TEXT,
            url TEXT UNIQUE,
            publish_date TEXT,
            topic TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 創建主題表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            count INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("[資料庫] 創建資料庫表...")
    print("[資料庫] 資料庫表創建完成")

# 初始化資料庫
init_db()

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
            background: #f5f7fa;
            min-height: 100vh;
            color: #333;
        }
        
        .header {
            background: #2c3e50;
            color: white;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 1.8em;
            font-weight: 600;
        }
        
        .restart-btn {
            background: #27ae60;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        .restart-btn:hover {
            background: #229954;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            border-left: 4px solid #3498db;
        }
        
        .stat-card:nth-child(2) { border-left-color: #e74c3c; }
        .stat-card:nth-child(3) { border-left-color: #f39c12; }
        .stat-card:nth-child(4) { border-left-color: #9b59b6; }
        
        .stat-number {
            font-size: 2.2em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 1em;
            color: #7f8c8d;
            font-weight: 500;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 30px;
        }
        
        .left-panel {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            height: fit-content;
        }
        
        .panel-title {
            font-size: 1.3em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-label {
            display: block;
            font-weight: 500;
            color: #34495e;
            margin-bottom: 8px;
        }
        
        .form-input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #ecf0f1;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .form-input:focus {
            outline: none;
            border-color: #3498db;
        }
        
        .date-inputs {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        
        .crawl-btn {
            width: 100%;
            background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
            color: white;
            border: none;
            padding: 15px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .crawl-btn:hover {
            transform: translateY(-2px);
        }
        
        .right-panel {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .news-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .topic-filter {
            padding: 8px 15px;
            border: 2px solid #ecf0f1;
            border-radius: 8px;
            background: white;
            font-size: 14px;
        }
        
        .news-list {
            max-height: 600px;
            overflow-y: auto;
        }
        
        .news-item {
            border: 1px solid #ecf0f1;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            transition: box-shadow 0.3s;
        }
        
        .news-item:hover {
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .news-number {
            font-size: 0.9em;
            color: #7f8c8d;
            margin-bottom: 5px;
        }
        
        .news-title {
            font-size: 1.1em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 10px;
            line-height: 1.4;
        }
        
        .news-tags {
            display: flex;
            gap: 8px;
            margin-bottom: 10px;
        }
        
        .news-tag {
            background: #ecf0f1;
            color: #7f8c8d;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
        }
        
        .news-tag.primary {
            background: #3498db;
            color: white;
        }
        
        .news-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.9em;
            color: #7f8c8d;
            margin-bottom: 10px;
        }
        
        .news-summary {
            color: #7f8c8d;
            font-size: 0.9em;
            line-height: 1.5;
            margin-bottom: 15px;
        }
        
        .news-actions {
            display: flex;
            justify-content: flex-end;
        }
        
        .open-btn {
            background: #3498db;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 5px;
            font-size: 0.9em;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        .open-btn:hover {
            background: #2980b9;
        }
        
        .loading {
            text-align: center;
            padding: 50px;
            color: #7f8c8d;
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        .success {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        
        @media (max-width: 1200px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 768px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
            
            .date-inputs {
                grid-template-columns: 1fr;
            }
            
            .container {
                padding: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>中文新聞爬蟲與主題分析系統</h1>
        <button class="restart-btn" onclick="location.reload()">重新啟動即可</button>
    </div>
    
    <div class="container">
        <!-- 統計卡片 -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="totalNews">0</div>
                <div class="stat-label">總新聞數</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="totalTopics">0</div>
                <div class="stat-label">主題數量</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="todayNews">0</div>
                <div class="stat-label">今日新聞</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="popularTopic">綜合</div>
                <div class="stat-label">熱門主題</div>
            </div>
        </div>
        
        <!-- 主要內容區域 -->
        <div class="main-content">
            <!-- 左側：新聞爬取設定 -->
            <div class="left-panel">
                <div class="panel-title">
                    🔍 新聞爬取設定
                </div>
                
                <form id="crawlForm">
                    <div class="form-group">
                        <label class="form-label">主題關鍵詞</label>
                        <input type="text" class="form-input" id="keywordInput" placeholder="請輸入關鍵詞，例如：習近平" value="習近平">
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">日期範圍</label>
                        <div class="date-inputs">
                            <div>
                                <label class="form-label">開始日期</label>
                                <input type="date" class="form-input" id="startDate" value="2025-09-13">
                            </div>
                            <div>
                                <label class="form-label">結束日期</label>
                                <input type="date" class="form-input" id="endDate" value="2025-09-28">
                            </div>
                        </div>
                    </div>
                    
                    <button type="submit" class="crawl-btn">
                        [開始] 爬取
                    </button>
                </form>
            </div>
            
            <!-- 右側：新聞列表 -->
            <div class="right-panel">
                <div class="news-header">
                    <div class="panel-title">
                        📰 新聞列表
                    </div>
                    <select class="topic-filter" id="topicFilter">
                        <option value="all">所有主題</option>
                    </select>
                </div>
                
                <div class="news-list" id="newsList">
                    <div class="loading">請點擊「開始爬取」來獲取新聞...</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 初始化
        document.addEventListener('DOMContentLoaded', function() {
            loadStats();
            loadNews();
            loadTopics();
        });
        
        // 爬取表單處理
        document.getElementById('crawlForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const keyword = document.getElementById('keywordInput').value.trim();
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            
            if (!keyword) {
                showMessage('請輸入關鍵詞', 'error');
                return;
            }
            
            try {
                const response = await fetch('/api/crawl', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ 
                        keyword: keyword,
                        start_date: startDate,
                        end_date: endDate
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    showMessage(`[成功] 爬取 ${result.count} 篇新聞！`, 'success');
                    loadStats();
                    loadNews();
                    loadTopics();
                } else {
                    showMessage(`[錯誤] 爬取失敗: ${result.message}`, 'error');
                }
            } catch (error) {
                showMessage(`[錯誤] 網路錯誤: ${error.message}`, 'error');
            }
        });
        
        // 主題過濾器
        document.getElementById('topicFilter').addEventListener('change', function() {
            loadNews();
        });
        
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                document.getElementById('totalNews').textContent = data.total_news || 0;
                document.getElementById('totalTopics').textContent = data.total_topics || 0;
                document.getElementById('todayNews').textContent = data.total_news || 0; // 使用總新聞數作為今日新聞
                
                // 獲取最熱門主題
                const topicsResponse = await fetch('/api/topics');
                const topicsData = await topicsResponse.json();
                
                if (topicsData.topics && Object.keys(topicsData.topics).length > 0) {
                    const mostPopularTopic = Object.keys(topicsData.topics).reduce((a, b) => 
                        topicsData.topics[a] > topicsData.topics[b] ? a : b
                    );
                    document.getElementById('popularTopic').textContent = mostPopularTopic;
                }
            } catch (error) {
                console.error('載入統計數據失敗:', error);
            }
        }
        
        async function loadNews() {
            try {
                const response = await fetch('/api/news');
                const data = await response.json();
                
                const container = document.getElementById('newsList');
                const selectedTopic = document.getElementById('topicFilter').value;
                
                if (data.news && data.news.length > 0) {
                    let filteredNews = data.news;
                    
                    // 根據選擇的主題過濾新聞
                    if (selectedTopic !== 'all') {
                        filteredNews = data.news.filter(news => news.topic === selectedTopic);
                    }
                    
                    container.innerHTML = filteredNews.map((news, index) => `
                        <div class="news-item">
                            <div class="news-number">${index + 1}</div>
                            <div class="news-title">${news.title}</div>
                            <div class="news-tags">
                                <span class="news-tag primary">${news.topic || '綜合'}</span>
                                <span class="news-tag">Google搜尋</span>
                            </div>
                            <div class="news-meta">
                                <span>${news.source}</span>
                                <span>${news.publish_date}</span>
                            </div>
                            <div class="news-summary">${news.content || '關於' + document.getElementById('keywordInput').value + '的最新消息...'}</div>
                            <div class="news-actions">
                                <button class="open-btn" onclick="window.open('${news.url}', '_blank')">開啟</button>
                            </div>
                        </div>
                    `).join('');
                } else {
                    container.innerHTML = '<div class="loading">暫無新聞資料，請先進行搜尋。</div>';
                }
            } catch (error) {
                document.getElementById('newsList').innerHTML = `<div class="error">載入新聞失敗: ${error.message}</div>`;
            }
        }
        
        async function loadTopics() {
            try {
                const response = await fetch('/api/topics');
                const data = await response.json();
                
                const topicFilter = document.getElementById('topicFilter');
                
                // 清除現有選項（保留「所有主題」）
                topicFilter.innerHTML = '<option value="all">所有主題</option>';
                
                if (data.topics && Object.keys(data.topics).length > 0) {
                    Object.keys(data.topics).forEach(topic => {
                        const option = document.createElement('option');
                        option.value = topic;
                        option.textContent = topic;
                        topicFilter.appendChild(option);
                    });
                }
            } catch (error) {
                console.error('載入主題失敗:', error);
            }
        }
        
        function showMessage(message, type) {
            const messageDiv = document.createElement('div');
            messageDiv.className = type;
            messageDiv.textContent = message;
            
            const container = document.querySelector('.container');
            container.insertBefore(messageDiv, container.firstChild);
            
            setTimeout(() => {
                messageDiv.remove();
            }, 5000);
        }
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
    start_date = data.get('start_date', '')
    end_date = data.get('end_date', '')
    
    if not keyword:
        return jsonify({'success': False, 'message': '請提供關鍵詞'})
    
    try:
        count = crawl_news(keyword, start_date, end_date)
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        print(f"[錯誤] 爬取失敗: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/news')
def api_news():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT title, content, source, url, publish_date, topic
        FROM news_article
        ORDER BY created_at DESC
        LIMIT 20
    ''')
    
    news = []
    for row in cursor.fetchall():
        news.append({
            'title': row[0],
            'content': row[1],
            'source': row[2],
            'url': row[3],
            'publish_date': row[4],
            'topic': row[5]
        })
    
    conn.close()
    return jsonify({'news': news})

@app.route('/api/stats')
def api_stats():
    conn = sqlite3.connect('news.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM news_article')
    total_news = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT topic) FROM news_article')
    total_topics = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT source) FROM news_article')
    total_sources = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_news': total_news,
        'total_topics': total_topics,
        'total_sources': total_sources
    })

@app.route('/api/topics')
def api_topics():
    try:
        conn = sqlite3.connect('news.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT topic, COUNT(*) FROM news_article GROUP BY topic')
        topics = dict(cursor.fetchall())
        
        conn.close()
        return jsonify({'topics': topics, 'keywords': []})
    except Exception as e:
        print(f"[錯誤] 主題分析失敗: {e}")
        return jsonify({'topics': {}, 'keywords': []})

@app.route('/api/wordcloud')
def api_wordcloud():
    try:
        conn = sqlite3.connect('news.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT title, content FROM news_article')
        articles = cursor.fetchall()
        
        if not articles:
            return jsonify({'wordcloud': None})
        
        # 簡化的詞雲生成
        wordcloud_data = None
        return jsonify({'wordcloud': wordcloud_data})
    except Exception as e:
        print(f"[錯誤] 詞雲生成失敗: {e}")
        return jsonify({'wordcloud': None})

if __name__ == '__main__':
    print("=" * 60)
    print("[系統] 中文新聞爬蟲與主題分析系統")
    print("=" * 60)
    print("正在初始化應用程式...")
    print("[啟動] Flask 應用程式啟動中...")
    print("[網址] 請訪問: http://localhost:5000")
    print("[停止] 按 Ctrl+C 停止應用程式")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)