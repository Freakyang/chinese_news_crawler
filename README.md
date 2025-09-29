# 中文新聞爬蟲與主題分析系統

一個功能完整的中文新聞爬蟲與主題分析系統，支援多個新聞網站的新聞抓取、智能主題分類、文字雲生成和 Web 管理介面。

## 功能特色

### 🔍 新聞爬取
- 支援多個中文新聞網站（聯合新聞網、中時新聞網、自由時報、中央社、BBC中文網等）
- 智能內容提取和關鍵詞分析
- 支援日期範圍和主題關鍵詞過濾
- 自動去重和資料清理

### 📊 主題分析
- 智能主題分類（政治、經濟、社會、國際、科技、體育、娛樂、環境）
- 主題熱度計算和趨勢分析
- 關鍵詞提取和頻率統計
- 情感分析功能

### ☁️ 文字雲生成
- 支援中文字體的文字雲生成
- 多種視覺化樣式和配色
- 主題比較文字雲
- 自動清理舊檔案

### 🌐 Web 管理介面
- 響應式設計，支援各種裝置
- 即時統計資訊顯示
- 互動式主題瀏覽
- 新聞列表和搜尋功能

## 安裝說明

### 1. 環境要求
- Python 3.8+
- Windows/macOS/Linux

### 2. 安裝依賴
```bash
pip install -r requirements.txt
```

### 3. 初始化資料庫
```bash
python app.py
```
首次運行會自動建立資料庫和必要的資料表。

### 4. 啟動應用程式
```bash
python app.py
```
應用程式將在 `http://localhost:5000` 啟動。

## 使用說明

### 1. 爬取新聞
1. 在 Web 介面中設定開始和結束日期
2. 輸入主題關鍵詞（可選）
3. 點擊「開始爬取」按鈕
4. 系統會在背景執行爬取任務

### 2. 查看分析結果
- **統計資訊**：查看總文章數、主題數量、新聞來源等
- **主題列表**：瀏覽所有主題及其文章數量
- **文字雲**：點擊主題查看對應的文字雲
- **新聞列表**：查看詳細的新聞內容

### 3. 主題管理
- 系統會自動分析新聞主題
- 支援自定義主題關鍵詞
- 可查看主題熱度和趨勢

## 專案結構

```
chinese_news_crawler/
├── app.py                    # Flask 主應用程式
├── requirements.txt          # 依賴套件清單
├── README.md                # 專案說明文件
├── analyzer/                # 分析器模組
│   ├── __init__.py
│   ├── topic_analyzer.py    # 主題分析器
│   └── wordcloud_generator.py # 文字雲生成器
├── crawler/                 # 爬蟲模組
│   ├── __init__.py
│   └── news_crawler.py      # 新聞爬蟲
├── templates/               # 前端模板
│   └── index.html          # 主頁面
├── static/                  # 靜態檔案
│   └── wordclouds/         # 文字雲圖片
└── news.db                 # SQLite 資料庫
```

## 技術架構

- **後端**：Flask + SQLAlchemy
- **資料庫**：SQLite
- **前端**：Bootstrap 5 + JavaScript
- **爬蟲**：requests + BeautifulSoup
- **分析**：jieba 分詞 + 自定義演算法
- **視覺化**：WordCloud + Matplotlib

## 支援的新聞網站

### 繁體中文
- 聯合新聞網 (udn.com)
- 中時新聞網 (chinatimes.com)
- 自由時報 (ltn.com.tw)
- 中央社 (cna.com.tw)
- BBC中文網 (bbc.com/zhongwen)
- RFI中文網 (rfi.fr/cn)

### 簡體中文
- 新浪新聞 (sina.com.cn)
- 搜狐新聞 (sohu.com)
- 人民網 (people.com.cn)

## 注意事項

1. **爬蟲限制**：請遵守各網站的 robots.txt 和使用條款
2. **中文字體**：系統會自動尋找系統中的中文字體，如無則使用預設字體
3. **資料庫**：使用 SQLite，資料會儲存在 `news.db` 檔案中
4. **效能**：大量爬取時請注意系統資源使用

## 開發者資訊

本專案使用 Python 開發，採用模組化設計，易於擴展和維護。

## 授權

MIT License
