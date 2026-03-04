#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻分析模块 - 负责分析历史新闻并提取关键词
"""

import os
import json
import re
import jieba
from collections import Counter
from datetime import datetime

class NewsAnalyzer:
    """新闻分析器"""
    
    def __init__(self):
        """初始化"""
        self.analysis_file = 'news_analysis.json'
        self.analyzed_news = {}
        self.keyword_frequency = Counter()
        self.news_by_keyword = {}
        
        # 加载分析结果
        self.load_analysis()
    
    def load_analysis(self):
        """加载分析结果"""
        if os.path.exists(self.analysis_file):
            try:
                with open(self.analysis_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.analyzed_news = data.get('analyzed_news', {})
                    self.keyword_frequency = Counter(data.get('keyword_frequency', {}))
                    self.news_by_keyword = data.get('news_by_keyword', {})
            except Exception as e:
                print(f"加载分析结果失败: {e}")
                self.analyzed_news = {}
                self.keyword_frequency = Counter()
                self.news_by_keyword = {}
    
    def save_analysis(self):
        """保存分析结果"""
        try:
            data = {
                'analyzed_news': self.analyzed_news,
                'keyword_frequency': dict(self.keyword_frequency),
                'news_by_keyword': self.news_by_keyword,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.analysis_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存分析结果失败: {e}")
    
    def extract_keywords(self, text, top_n=10):
        """提取关键词"""
        # 分词
        words = jieba.cut(text)
        
        # 过滤停用词和短词
        stop_words = self._get_stop_words()
        keywords = []
        for word in words:
            # 过滤停用词、数字、单个字符
            if word not in stop_words and not word.isdigit() and len(word) > 1:
                keywords.append(word)
        
        # 统计词频并返回Top N
        word_count = Counter(keywords)
        return [word for word, _ in word_count.most_common(top_n)]
    
    def _get_stop_words(self):
        """获取停用词"""
        stop_words = set([
            '的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'
        ])
        return stop_words
    
    def analyze_news(self, newspaper_name, date, content):
        """分析单条新闻"""
        news_id = f"{newspaper_name}_{date}"
        
        if news_id in self.analyzed_news:
            return
        
        # 提取关键词
        keywords = self.extract_keywords(content)
        
        # 记录分析结果
        self.analyzed_news[news_id] = {
            'newspaper_name': newspaper_name,
            'date': date,
            'keywords': keywords,
            'analyzed_at': datetime.now().isoformat()
        }
        
        # 更新关键词频率
        for keyword in keywords:
            self.keyword_frequency[keyword] += 1
            
            # 更新关键词与新闻的关联
            if keyword not in self.news_by_keyword:
                self.news_by_keyword[keyword] = []
            if news_id not in self.news_by_keyword[keyword]:
                self.news_by_keyword[keyword].append(news_id)
        
        self.save_analysis()
        return keywords
    
    def analyze_history(self):
        """分析历史新闻"""
        analyzed_count = 0
        
        # 分析报纸图片目录
        if os.path.exists('newspaper_images'):
            for file in os.listdir('newspaper_images'):
                if file.endswith(('.jpg', '.pdf')):
                    parts = file.replace('.jpg', '').replace('.pdf', '').split('_')
                    if len(parts) >= 2:
                        newspaper_name = parts[0]
                        date = parts[1]
                        news_id = f"{newspaper_name}_{date}"
                        
                        if news_id not in self.analyzed_news:
                            # 尝试读取对应的分析结果文件
                            analysis_file = os.path.join('newspaper_copies', f"{newspaper_name}_{date}_精华内容.txt")
                            if os.path.exists(analysis_file):
                                try:
                                    with open(analysis_file, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                        self.analyze_news(newspaper_name, date, content)
                                        analyzed_count += 1
                                except Exception as e:
                                    print(f"分析文件 {analysis_file} 失败: {e}")
        
        return analyzed_count
    
    def get_top_keywords(self, top_n=20):
        """获取高频关键词"""
        return self.keyword_frequency.most_common(top_n)
    
    def get_news_by_keyword(self, keyword):
        """根据关键词获取相关新闻"""
        news_ids = self.news_by_keyword.get(keyword, [])
        news_list = []
        
        for news_id in news_ids:
            if news_id in self.analyzed_news:
                news_info = self.analyzed_news[news_id]
                news_list.append({
                    'newspaper_name': news_info['newspaper_name'],
                    'date': news_info['date'],
                    'keywords': news_info['keywords']
                })
        
        return news_list
    
    def search_news(self, query):
        """搜索新闻"""
        results = []
        query_lower = query.lower()
        
        for news_id, news_info in self.analyzed_news.items():
            # 搜索关键词
            for keyword in news_info['keywords']:
                if query_lower in keyword.lower():
                    results.append({
                        'newspaper_name': news_info['newspaper_name'],
                        'date': news_info['date'],
                        'keywords': news_info['keywords']
                    })
                    break
        
        return results
    
    def advanced_search(self, start_date=None, end_date=None, categories=None, newspapers=None, keyword=None, exact_match=False, title_query=None, page=1, page_size=20):
        """高级搜索新闻
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            categories: 分类列表
            newspapers: 报纸来源列表
            keyword: 关键词
            exact_match: 是否精确匹配关键词
            title_query: 标题关键词
            page: 页码
            page_size: 每页数量
        """
        results = []
        
        for news_id, news_info in self.analyzed_news.items():
            # 时间范围筛选
            news_date = news_info['date']
            if start_date and news_date < start_date:
                continue
            if end_date and news_date > end_date:
                continue
            
            # 报纸来源筛选
            if newspapers and news_info['newspaper_name'] not in newspapers:
                continue
            
            # 关键词筛选
            if keyword:
                keyword_lower = keyword.lower()
                found = False
                for kw in news_info['keywords']:
                    if exact_match:
                        if kw.lower() == keyword_lower:
                            found = True
                            break
                    else:
                        if keyword_lower in kw.lower():
                            found = True
                            break
                if not found:
                    continue
            
            # 标题关键词筛选 (这里简化处理，实际应该从标题中提取)
            if title_query:
                # 由于我们没有存储标题，这里使用关键词来模拟
                title_match = False
                for kw in news_info['keywords']:
                    if title_query.lower() in kw.lower():
                        title_match = True
                        break
                if not title_match:
                    continue
            
            # 分类筛选 (需要与keyword_manager集成)
            # 这里暂时跳过，后续可以通过keyword_manager获取分类信息
            
            results.append({
                'newspaper_name': news_info['newspaper_name'],
                'date': news_info['date'],
                'keywords': news_info['keywords']
            })
        
        # 分页
        start = (page - 1) * page_size
        end = start + page_size
        paginated_results = results[start:end]
        
        return {
            'total': len(results),
            'page': page,
            'page_size': page_size,
            'results': paginated_results
        }
    
    def get_search_history(self, limit=10):
        """获取搜索历史"""
        # 这里简化处理，实际应该存储搜索历史
        # 暂时返回高频关键词作为历史搜索
        top_keywords = self.get_top_keywords(limit)
        return [kw for kw, _ in top_keywords]
    
    def get_related_keywords(self, keyword, top_n=5):
        """获取相关关键词"""
        related_keywords = Counter()
        
        # 获取包含该关键词的新闻
        news_ids = self.news_by_keyword.get(keyword, [])
        
        for news_id in news_ids:
            if news_id in self.analyzed_news:
                for kw in self.analyzed_news[news_id]['keywords']:
                    if kw != keyword:
                        related_keywords[kw] += 1
        
        return [kw for kw, _ in related_keywords.most_common(top_n)]

# 全局新闻分析器实例
news_analyzer = NewsAnalyzer()
