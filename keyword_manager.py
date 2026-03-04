#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词管理模块 - 负责新闻关键词的管理和分类
"""

import os
import json
import csv
from datetime import datetime

class KeywordManager:
    """关键词管理器"""
    
    def __init__(self):
        """初始化"""
        self.keywords_file = 'keywords.json'
        self.categories_file = 'categories.json'
        self.keywords = {}
        self.categories = {}
        
        # 加载数据
        self.load_keywords()
        self.load_categories()
    
    def load_keywords(self):
        """加载关键词"""
        if os.path.exists(self.keywords_file):
            try:
                with open(self.keywords_file, 'r', encoding='utf-8') as f:
                    self.keywords = json.load(f)
            except Exception as e:
                print(f"加载关键词失败: {e}")
                self.keywords = {}
    
    def save_keywords(self):
        """保存关键词"""
        try:
            with open(self.keywords_file, 'w', encoding='utf-8') as f:
                json.dump(self.keywords, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存关键词失败: {e}")
    
    def load_categories(self):
        """加载分类"""
        if os.path.exists(self.categories_file):
            try:
                with open(self.categories_file, 'r', encoding='utf-8') as f:
                    self.categories = json.load(f)
            except Exception as e:
                print(f"加载分类失败: {e}")
                self.categories = {}
        
        # 默认分类
        if not self.categories:
            self.categories = {
                'politics': {'name': '政治', 'description': '政治新闻'}, 
                'economy': {'name': '经济', 'description': '经济新闻'},
                'technology': {'name': '科技', 'description': '科技新闻'},
                'sports': {'name': '体育', 'description': '体育新闻'},
                'entertainment': {'name': '娱乐', 'description': '娱乐新闻'},
                'health': {'name': '健康', 'description': '健康新闻'},
                'education': {'name': '教育', 'description': '教育新闻'},
                'international': {'name': '国际', 'description': '国际新闻'}
            }
            self.save_categories()
    
    def save_categories(self):
        """保存分类"""
        try:
            with open(self.categories_file, 'w', encoding='utf-8') as f:
                json.dump(self.categories, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存分类失败: {e}")
    
    def add_keyword(self, keyword, categories=None):
        """添加关键词"""
        if not keyword or keyword.strip() == '':
            return False, "关键词不能为空"
        
        keyword = keyword.strip()
        if keyword in self.keywords:
            return False, "关键词已存在"
        
        self.keywords[keyword] = {
            'categories': categories or [],
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self.save_keywords()
        return True, "关键词添加成功"
    
    def update_keyword(self, keyword, categories=None):
        """更新关键词"""
        if keyword not in self.keywords:
            return False, "关键词不存在"
        
        self.keywords[keyword]['categories'] = categories or []
        self.keywords[keyword]['updated_at'] = datetime.now().isoformat()
        self.save_keywords()
        return True, "关键词更新成功"
    
    def delete_keyword(self, keyword):
        """删除关键词"""
        if keyword in self.keywords:
            del self.keywords[keyword]
            self.save_keywords()
            return True, "关键词删除成功"
        return False, "关键词不存在"
    
    def get_keywords(self):
        """获取所有关键词"""
        return self.keywords
    
    def get_keywords_by_category(self, category):
        """按分类获取关键词"""
        result = []
        for keyword, info in self.keywords.items():
            if category in info['categories']:
                result.append(keyword)
        return result
    
    def search_keywords(self, query):
        """搜索关键词"""
        result = []
        query = query.lower()
        for keyword in self.keywords:
            if query in keyword.lower():
                result.append(keyword)
        return result
    
    def add_category(self, category_id, name, description):
        """添加分类"""
        if not category_id or not name:
            return False, "分类ID和名称不能为空"
        
        if category_id in self.categories:
            return False, "分类已存在"
        
        self.categories[category_id] = {
            'name': name,
            'description': description,
            'created_at': datetime.now().isoformat()
        }
        self.save_categories()
        return True, "分类添加成功"
    
    def update_category(self, category_id, name, description):
        """更新分类"""
        if category_id not in self.categories:
            return False, "分类不存在"
        
        self.categories[category_id]['name'] = name
        self.categories[category_id]['description'] = description
        self.save_categories()
        return True, "分类更新成功"
    
    def delete_category(self, category_id):
        """删除分类"""
        if category_id in self.categories:
            del self.categories[category_id]
            # 同时从所有关键词中移除该分类
            for keyword, info in self.keywords.items():
                if category_id in info['categories']:
                    info['categories'].remove(category_id)
            self.save_categories()
            self.save_keywords()
            return True, "分类删除成功"
        return False, "分类不存在"
    
    def get_categories(self):
        """获取所有分类"""
        return self.categories
    
    def import_keywords(self, file_path):
        """导入关键词（CSV格式）"""
        try:
            imported = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    keyword = row.get('keyword', '').strip()
                    categories = row.get('categories', '').split(',')
                    categories = [c.strip() for c in categories if c.strip()]
                    
                    if keyword:
                        if keyword in self.keywords:
                            self.update_keyword(keyword, categories)
                        else:
                            self.add_keyword(keyword, categories)
                        imported += 1
            return True, f"成功导入 {imported} 个关键词"
        except Exception as e:
            return False, f"导入失败: {str(e)}"
    
    def export_keywords(self, file_path):
        """导出关键词（CSV格式）"""
        try:
            with open(file_path, 'w', encoding='utf-8', newline='') as f:
                fieldnames = ['keyword', 'categories', 'created_at', 'updated_at']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for keyword, info in self.keywords.items():
                    row = {
                        'keyword': keyword,
                        'categories': ','.join(info['categories']),
                        'created_at': info.get('created_at', ''),
                        'updated_at': info.get('updated_at', '')
                    }
                    writer.writerow(row)
            return True, "关键词导出成功"
        except Exception as e:
            return False, f"导出失败: {str(e)}"
    
    def categorize_news(self, title, content):
        """根据标题和内容自动分类"""
        matched_categories = set()
        text = (title + ' ' + content).lower()
        
        for keyword, info in self.keywords.items():
            if keyword.lower() in text:
                matched_categories.update(info['categories'])
        
        return list(matched_categories)

# 全局关键词管理器实例
keyword_manager = KeywordManager()
