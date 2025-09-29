from wordcloud import WordCloud
import matplotlib.pyplot as plt
import jieba
import numpy as np
from PIL import Image
import os
import re
from collections import Counter
import logging
import time

logger = logging.getLogger(__name__)

class WordCloudGenerator:
    def __init__(self):
        # 設定中文字體（需要下載中文字體檔案）
        self.font_path = self._get_chinese_font()
        
        # 停用詞列表
        self.stop_words = {
            '的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一個', 
            '上', '也', '很', '到', '說', '要', '去', '你', '會', '著', '沒有', '看', '好', 
            '自己', '這', '那', '什麼', '可以', '因為', '所以', '但是', '如果', '或者', 
            '而且', '然後', '已經', '還是', '就是', '新聞', '報導', '消息', '最新', 
            '今天', '昨天', '明天', '今年', '去年', '明年', '台灣', '中國', '美國', 
            '日本', '韓國', '香港', '澳門', '新加坡', '馬來西亞', '記者', '編輯', 
            '來源', '圖片', '照片', '影片', '視頻', '直播', '現場', '即時', '快訊'
        }
        
        # 建立輸出目錄
        self.output_dir = 'static/wordclouds'
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _get_chinese_font(self):
        """獲取中文字體路徑"""
        # 常見的中文字體路徑
        font_paths = [
            'C:/Windows/Fonts/msyh.ttc',  # 微軟雅黑
            'C:/Windows/Fonts/simhei.ttf',  # 黑體
            'C:/Windows/Fonts/simsun.ttc',  # 宋體
            'C:/Windows/Fonts/simkai.ttf',  # 楷體
            'C:/Windows/Fonts/simfang.ttf',  # 仿宋
            '/System/Library/Fonts/PingFang.ttc',  # macOS
            '/System/Library/Fonts/STHeiti Light.ttc',  # macOS
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                return font_path
        
        # 如果找不到中文字體，返回None（會使用預設字體）
        logger.warning("找不到中文字體，將使用預設字體")
        return None

    def generate_wordcloud(self, texts, width=800, height=600, max_words=100, 
                          background_color='white', colormap='viridis'):
        """生成文字雲"""
        try:
            # 合併所有文字
            combined_text = ' '.join(texts) if isinstance(texts, list) else texts
            
            # 使用jieba分詞
            words = jieba.lcut(combined_text)
            
            # 過濾停用詞和短詞
            filtered_words = []
            for word in words:
                if (len(word) > 1 and 
                    word not in self.stop_words and 
                    re.match(r'[\u4e00-\u9fff]', word) and  # 只保留中文字符
                    not word.isdigit()):  # 排除純數字
                    filtered_words.append(word)
            
            # 計算詞頻
            word_freq = Counter(filtered_words)
            
            # 如果沒有足夠的詞，返回預設圖片
            if len(word_freq) < 5:
                return self._generate_default_wordcloud()
            
            # 建立文字雲
            wordcloud = WordCloud(
                font_path=self.font_path,
                width=width,
                height=height,
                max_words=max_words,
                background_color=background_color,
                colormap=colormap,
                relative_scaling=0.5,
                random_state=42
            ).generate_from_frequencies(word_freq)
            
            # 生成檔案名
            filename = f"wordcloud_{int(time.time())}.png"
            filepath = os.path.join(self.output_dir, filename)
            
            # 儲存圖片
            plt.figure(figsize=(width/100, height/100), dpi=100)
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.tight_layout(pad=0)
            plt.savefig(filepath, bbox_inches='tight', pad_inches=0, dpi=100)
            plt.close()
            
            logger.info(f"文字雲已生成: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"生成文字雲時發生錯誤: {e}")
            return self._generate_default_wordcloud()

    def _generate_default_wordcloud(self):
        """生成預設文字雲"""
        try:
            # 建立一個簡單的預設文字雲
            default_text = "新聞 主題 分析 文字雲 生成 中文字體 支援"
            
            wordcloud = WordCloud(
                font_path=self.font_path,
                width=800,
                height=600,
                background_color='white',
                colormap='viridis'
            ).generate(default_text)
            
            filename = f"default_wordcloud_{int(time.time())}.png"
            filepath = os.path.join(self.output_dir, filename)
            
            plt.figure(figsize=(8, 6), dpi=100)
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.tight_layout(pad=0)
            plt.savefig(filepath, bbox_inches='tight', pad_inches=0, dpi=100)
            plt.close()
            
            return filepath
            
        except Exception as e:
            logger.error(f"生成預設文字雲時發生錯誤: {e}")
            return None

    def generate_topic_wordcloud(self, topic, articles, width=800, height=600):
        """為特定主題生成文字雲"""
        try:
            # 提取該主題的所有文章文字
            texts = []
            for article in articles:
                if article.topic == topic:
                    text = article.title + ' ' + (article.content or '')
                    texts.append(text)
            
            if not texts:
                return self._generate_default_wordcloud()
            
            return self.generate_wordcloud(texts, width, height)
            
        except Exception as e:
            logger.error(f"生成主題文字雲時發生錯誤: {e}")
            return self._generate_default_wordcloud()

    def generate_comparison_wordcloud(self, topics_data, width=800, height=600):
        """生成比較文字雲（多個主題並排顯示）"""
        try:
            num_topics = len(topics_data)
            if num_topics == 0:
                return self._generate_default_wordcloud()
            
            # 計算子圖佈局
            cols = min(3, num_topics)
            rows = (num_topics + cols - 1) // cols
            
            fig, axes = plt.subplots(rows, cols, figsize=(width/100 * cols, height/100 * rows))
            if num_topics == 1:
                axes = [axes]
            elif rows == 1:
                axes = axes
            else:
                axes = axes.flatten()
            
            for i, (topic, texts) in enumerate(topics_data.items()):
                if i >= len(axes):
                    break
                
                # 生成該主題的文字雲
                combined_text = ' '.join(texts) if isinstance(texts, list) else texts
                words = jieba.lcut(combined_text)
                
                filtered_words = []
                for word in words:
                    if (len(word) > 1 and 
                        word not in self.stop_words and 
                        re.match(r'[\u4e00-\u9fff]', word) and
                        not word.isdigit()):
                        filtered_words.append(word)
                
                word_freq = Counter(filtered_words)
                
                if len(word_freq) < 5:
                    continue
                
                wordcloud = WordCloud(
                    font_path=self.font_path,
                    width=width//cols,
                    height=height//rows,
                    max_words=50,
                    background_color='white',
                    colormap='viridis'
                ).generate_from_frequencies(word_freq)
                
                axes[i].imshow(wordcloud, interpolation='bilinear')
                axes[i].set_title(topic, fontsize=14, pad=10)
                axes[i].axis('off')
            
            # 隱藏多餘的子圖
            for i in range(num_topics, len(axes)):
                axes[i].axis('off')
            
            plt.tight_layout()
            
            # 儲存圖片
            filename = f"comparison_wordcloud_{int(time.time())}.png"
            filepath = os.path.join(self.output_dir, filename)
            plt.savefig(filepath, bbox_inches='tight', dpi=100)
            plt.close()
            
            return filepath
            
        except Exception as e:
            logger.error(f"生成比較文字雲時發生錯誤: {e}")
            return self._generate_default_wordcloud()

    def cleanup_old_wordclouds(self, max_age_hours=24):
        """清理舊的文字雲檔案"""
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.output_dir):
                if filename.endswith('.png'):
                    filepath = os.path.join(self.output_dir, filename)
                    file_age = current_time - os.path.getmtime(filepath)
                    
                    if file_age > max_age_seconds:
                        os.remove(filepath)
                        logger.info(f"已刪除舊的文字雲檔案: {filename}")
                        
        except Exception as e:
            logger.error(f"清理舊文字雲檔案時發生錯誤: {e}")
