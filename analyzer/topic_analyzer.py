import jieba
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TopicAnalyzer:
    def __init__(self):
        # 停用詞列表
        self.stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一個', 
            '上', '也', '很', '到', '說', '要', '去', '你', '會', '著', '沒有', '看', '好', 
            '自己', '這', '那', '什麼', '可以', '因為', '所以', '但是', '如果', '或者', 
            '而且', '然後', '已經', '還是', '就是', '就是', '就是', '就是', '就是',
            '新聞', '報導', '消息', '最新', '今天', '昨天', '明天', '今年', '去年', '明年',
            '台灣', '中國', '美國', '日本', '韓國', '香港', '澳門', '新加坡', '馬來西亞'
        }
        
        # 主題關鍵詞映射
        self.topic_keywords = {
            '政治': {
                'keywords': ['政治', '選舉', '政府', '總統', '立法院', '政黨', '政策', '官員', '部長', '院長', '市長', '縣長', '議員', '立法委員', '國會', '議會', '選舉', '投票', '候選人', '民調', '支持率', '執政', '在野', '反對黨', '執政黨'],
                'weight': 1.0
            },
            '經濟': {
                'keywords': ['經濟', '股市', '金融', '投資', '企業', '商業', '貿易', '就業', '失業', '通膨', '通縮', '利率', '匯率', 'GDP', '成長', '衰退', '景氣', '消費', '物價', '薪資', '工資', '銀行', '證券', '基金', '保險', '房地產', '房價', '租金'],
                'weight': 1.0
            },
            '社會': {
                'keywords': ['社會', '犯罪', '事故', '災害', '教育', '醫療', '環保', '交通', '治安', '安全', '健康', '疾病', '疫情', '疫苗', '醫院', '學校', '學生', '老師', '家長', '家庭', '婚姻', '離婚', '生育', '人口', '老化', '長照', '社福', '福利'],
                'weight': 1.0
            },
            '國際': {
                'keywords': ['國際', '外交', '戰爭', '和平', '聯合國', '美國', '中國', '日本', '韓國', '俄羅斯', '歐洲', '歐盟', '北約', 'G7', 'G20', 'APEC', 'WTO', 'WHO', 'UN', '安理會', '大使', '領事', '簽證', '護照', '移民', '難民', '恐怖主義', '反恐'],
                'weight': 1.0
            },
            '科技': {
                'keywords': ['科技', 'AI', '人工智慧', '網路', '手機', '電腦', '創新', '數位', '電子', '軟體', '硬體', '程式', '程式設計', '開發', '研發', '專利', '發明', '機器人', '自動化', '大數據', '雲端', '物聯網', '區塊鏈', '加密貨幣', '比特幣', '虛擬實境', 'AR', 'VR'],
                'weight': 1.0
            },
            '體育': {
                'keywords': ['體育', '運動', '足球', '籃球', '棒球', '網球', '羽球', '桌球', '游泳', '田徑', '奧運', '亞運', '世運', '比賽', '選手', '冠軍', '金牌', '銀牌', '銅牌', '紀錄', '破紀錄', '教練', '訓練', '健身', '瑜珈', '跑步', '騎車', '登山'],
                'weight': 1.0
            },
            '娛樂': {
                'keywords': ['娛樂', '電影', '音樂', '明星', '電視', '節目', '藝人', '演出', '演唱會', '音樂會', '戲劇', '舞台劇', '舞蹈', '繪畫', '攝影', '設計', '時尚', '美容', '化妝', '服裝', '珠寶', '美食', '餐廳', '旅遊', '觀光', '景點', '飯店', '民宿'],
                'weight': 1.0
            },
            '環境': {
                'keywords': ['環境', '環保', '氣候', '全球暖化', '溫室效應', '碳排放', '碳足跡', '再生能源', '太陽能', '風力', '水力', '核能', '核電', '核廢料', '污染', '空氣污染', '水污染', '土壤污染', '噪音污染', '垃圾', '回收', '再利用', '永續', '綠能', '節能', '減碳'],
                'weight': 1.0
            }
        }

    def analyze_topics(self, articles=None):
        """分析主題"""
        if not articles:
            # 如果沒有提供文章，從資料庫獲取
            from app import NewsArticle, db
            articles = NewsArticle.query.all()
        
        # 按主題分組統計
        topic_stats = defaultdict(lambda: {
            'count': 0,
            'sources': set(),
            'keywords': Counter(),
            'articles': []
        })
        
        for article in articles:
            topic = self._classify_article_topic(article)
            if topic:
                topic_stats[topic]['count'] += 1
                topic_stats[topic]['sources'].add(article.source)
                topic_stats[topic]['articles'].append(article)
                
                # 統計關鍵詞
                if article.keywords:
                    keywords = article.keywords.split(',') if isinstance(article.keywords, str) else article.keywords
                    for keyword in keywords:
                        if keyword.strip():
                            topic_stats[topic]['keywords'][keyword.strip()] += 1
        
        # 計算主題熱度
        topic_heat = self._calculate_topic_heat(topic_stats)
        
        return {
            'topic_stats': dict(topic_stats),
            'topic_heat': topic_heat,
            'analysis_time': datetime.now()
        }

    def _classify_article_topic(self, article):
        """分類文章主題"""
        text = (article.title + ' ' + (article.content or '')).lower()
        
        topic_scores = {}
        
        for topic, config in self.topic_keywords.items():
            score = 0
            for keyword in config['keywords']:
                if keyword in text:
                    score += config['weight']
            
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        
        return '其他'

    def _calculate_topic_heat(self, topic_stats):
        """計算主題熱度"""
        total_articles = sum(stats['count'] for stats in topic_stats.values())
        
        topic_heat = {}
        for topic, stats in topic_stats.items():
            # 計算熱度分數（基於文章數量、來源多樣性、關鍵詞豐富度）
            article_ratio = stats['count'] / total_articles if total_articles > 0 else 0
            source_diversity = len(stats['sources']) / 10  # 假設最多10個來源
            keyword_richness = len(stats['keywords']) / 50  # 假設最多50個關鍵詞
            
            heat_score = (article_ratio * 0.5 + source_diversity * 0.3 + keyword_richness * 0.2) * 100
            
            topic_heat[topic] = {
                'score': round(heat_score, 2),
                'article_count': stats['count'],
                'source_count': len(stats['sources']),
                'keyword_count': len(stats['keywords']),
                'top_keywords': [kw for kw, count in stats['keywords'].most_common(5)]
            }
        
        # 按熱度分數排序
        return dict(sorted(topic_heat.items(), key=lambda x: x[1]['score'], reverse=True))

    def extract_trending_keywords(self, articles, top_n=20):
        """提取熱門關鍵詞"""
        all_keywords = Counter()
        
        for article in articles:
            if article.keywords:
                keywords = article.keywords.split(',') if isinstance(article.keywords, str) else article.keywords
                for keyword in keywords:
                    keyword = keyword.strip()
                    if keyword and keyword not in self.stop_words:
                        all_keywords[keyword] += 1
        
        return all_keywords.most_common(top_n)

    def analyze_sentiment(self, text):
        """簡單的情感分析"""
        positive_words = ['好', '棒', '讚', '優秀', '成功', '勝利', '進步', '改善', '提升', '增加', '成長', '發展', '創新', '突破', '成就', '榮譽', '光榮', '驕傲', '滿意', '開心', '快樂', '興奮', '期待', '希望', '樂觀']
        negative_words = ['壞', '糟', '差', '失敗', '失敗', '退步', '惡化', '下降', '減少', '衰退', '落後', '問題', '困難', '危機', '危險', '威脅', '擔憂', '擔心', '失望', '憤怒', '悲傷', '痛苦', '絕望', '悲觀']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'

    def get_topic_timeline(self, topic, days=7):
        """獲取主題時間線"""
        from app import NewsArticle, db
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        articles = NewsArticle.query.filter(
            NewsArticle.topic == topic,
            NewsArticle.publish_date >= start_date,
            NewsArticle.publish_date <= end_date
        ).order_by(NewsArticle.publish_date).all()
        
        timeline = defaultdict(int)
        for article in articles:
            date_key = article.publish_date.strftime('%Y-%m-%d')
            timeline[date_key] += 1
        
        return dict(timeline)
