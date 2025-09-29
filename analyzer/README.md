# 中文新聞爬蟲與主題分析系統

一個功能完整的中文新聞爬蟲系統，具備動態新聞搜尋、主題分析、詞雲生成等功能。

## 🌟 功能特色

- **動態新聞爬取**: 從 Google、Yahoo、ETtoday 等來源即時爬取新聞
- **智能日期篩選**: 支援日期範圍搜尋，允許 ±3 天誤差
- **主題自動分類**: 自動將新聞分類為政治、經濟、科技、國際、社會、體育、娛樂等主題
- **詞雲視覺化**: 生成關鍵詞詞雲圖
- **現代化 Web 介面**: 響應式設計，支援即時搜尋與篩選
- **資料庫儲存**: 使用 SQLite 儲存新聞資料

## 🚀 快速開始

### 環境需求

- Python 3.7+
- pip

### 安裝步驟

1. **克隆專案**
   ```bash
   git clone https://github.com/Freakyang/chinese_news_crawler.git
   cd chinese_news_crawler
   ```

2. **安裝依賴套件**
   ```bash
   pip install -r requirements.txt
   ```

3. **啟動應用程式**
   ```bash
   python analyzer/real_news_crawler.py
   ```

4. **開啟瀏覽器**
   訪問 `http://localhost:5000`

## 📖 使用說明

### 基本操作

1. **搜尋新聞**: 在「主題關鍵詞」欄位輸入關鍵詞
2. **設定日期範圍**: 選擇搜尋的日期範圍（可選）
3. **開始爬取**: 點擊「開始爬取」按鈕
4. **查看結果**: 在右側新聞列表中查看爬取結果
5. **開啟新聞**: 點擊「開啟」按鈕直接開啟原始新聞頁面

### 進階功能

- **主題篩選**: 使用左側主題標籤篩選特定主題的新聞
- **詞雲查看**: 點擊主題標籤查看相關詞雲圖
- **即時更新**: 系統會自動更新統計資料

## 🛠️ 技術架構

### 後端技術
- **Flask**: Web 框架
- **SQLAlchemy**: ORM 資料庫操作
- **BeautifulSoup4**: HTML 解析
- **jieba**: 中文分詞
- **wordcloud**: 詞雲生成

### 前端技術
- **Bootstrap 5**: UI 框架
- **Font Awesome**: 圖示庫
- **JavaScript**: 互動功能

### 資料庫
- **SQLite**: 輕量級資料庫

## 📁 專案結構

```
chinese_news_crawler/
├── analyzer/
│   ├── __init__.py
│   ├── topic_analyzer.py      # 主題分析模組
│   ├── wordcloud_generator.py # 詞雲生成模組
│   └── real_news_crawler.py  # 主應用程式
├── static/
│   └── wordclouds/           # 詞雲圖片儲存
├── news.db                   # SQLite 資料庫
├── requirements.txt          # 依賴套件清單
└── README.md                 # 專案說明
```

## 🔧 配置說明

### 新聞來源
系統支援以下新聞來源：
- Google News 搜尋
- Yahoo 新聞
- ETtoday 新聞雲
- 中國時報

### 主題分類
自動分類為以下主題：
- 政治
- 經濟  
- 科技
- 國際
- 社會
- 體育
- 娛樂

## 📊 API 端點

- `GET /` - 主頁面
- `GET /api/news` - 獲取新聞列表
- `GET /api/stats` - 獲取統計資料
- `GET /api/topics` - 獲取主題列表
- `POST /api/crawl` - 開始爬取新聞

## 🤝 貢獻指南

歡迎提交 Issue 和 Pull Request！

1. Fork 本專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

## 📄 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 👨‍💻 作者

**Freakyang** - [@Freakyang](https://github.com/Freakyang)

## 🙏 致謝

- 感謝所有開源社群的貢獻
- 感謝新聞媒體提供的新聞內容

## 📞 聯絡方式

如有問題或建議，請透過以下方式聯絡：

- GitHub Issues: [專案 Issues 頁面](https://github.com/Freakyang/chinese_news_crawler/issues)
- Email: 透過 GitHub 個人資料頁面

---

⭐ 如果這個專案對您有幫助，請給個 Star！