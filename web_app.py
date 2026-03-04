#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web界面 - 为报纸抓取工具提供Web界面
"""

from flask import Flask, render_template, request, jsonify, send_file
import os
import threading
import time
from datetime import datetime, timedelta
from services.newspaper_tool import NewspaperTool
from utils import init_folders
import json
from scheduler import scheduler
from keyword_manager import keyword_manager
from news_analyzer import news_analyzer

app = Flask(__name__)
app.config['SECRET_KEY'] = 'newspaper_tool_secret_key'

# 全局变量存储任务状态
task_status = {
    'running': False,
    'progress': 0,
    'message': '',
    'result': None,
    'error': None
}

def run_newspaper_task(newspaper_name, date_str, use_ai, save_file, save_db):
    """在后台运行报纸抓取任务"""
    global task_status
    
    try:
        task_status['running'] = True
        task_status['progress'] = 10
        task_status['message'] = '初始化文件夹...'
        
        # 初始化文件夹
        init_folders()
        
        task_status['progress'] = 20
        task_status['message'] = '创建报纸工具实例...'
        
        # 创建工具实例
        tool = NewspaperTool()
        
        # 解析日期
        if date_str == 'today':
            date_obj = datetime.now()
        elif date_str == 'yesterday':
            date_obj = datetime.now() - timedelta(days=1)
        elif date_str == 'before_yesterday':
            date_obj = datetime.now() - timedelta(days=2)
        else:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        date_formatted = date_obj.strftime('%Y-%m-%d')
        
        task_status['progress'] = 30
        task_status['message'] = f'开始下载 {newspaper_name} ({date_formatted})...'
        
        # 下载报纸文件
        from downloader import download_newspaper_file
        file_path = download_newspaper_file(newspaper_name, date_obj, date_formatted)
        
        if not file_path:
            task_status['error'] = '报纸下载失败'
            task_status['running'] = False
            return
        
        task_status['progress'] = 60
        task_status['message'] = '报纸下载成功！'
        
        result = {
            'newspaper_name': newspaper_name,
            'date': date_formatted,
            'file_path': file_path,
            'ai_content': None,
            'saved_files': [],
            'saved_db': False
        }
        
        # AI解析
        if use_ai:
            task_status['progress'] = 70
            task_status['message'] = '正在使用AI解析内容...'
            
            from ai_client import analyze_with_free_ai
            ai_content = analyze_with_free_ai(file_path, newspaper_name, date_formatted)
            
            if ai_content:
                result['ai_content'] = ai_content
                task_status['progress'] = 80
                task_status['message'] = 'AI解析完成！'
                
                # 保存到文件
                if save_file:
                    from file_processor import save_content_to_file
                    saved_file = save_content_to_file(ai_content, newspaper_name, date_formatted)
                    if saved_file:
                        result['saved_files'].append(saved_file)
                
                # 保存到数据库
                if save_db:
                    if tool.db_manager.connect():
                        from file_processor import parse_ai_content
                        summaries = parse_ai_content(ai_content, newspaper_name, date_formatted)
                        if summaries:
                            tool.db_manager.batch_insert_summaries(summaries)
                            result['saved_db'] = True
                        tool.db_manager.close()
        
        task_status['progress'] = 100
        task_status['message'] = '任务完成！'
        task_status['result'] = result
        
    except Exception as e:
        task_status['error'] = str(e)
        task_status['message'] = f'任务失败: {str(e)}'
    finally:
        task_status['running'] = False

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/task/status')
def get_task_status():
    """获取任务状态"""
    return jsonify(task_status)

@app.route('/api/task/start', methods=['POST'])
def start_task():
    """开始新任务"""
    global task_status
    
    if task_status['running']:
        return jsonify({'error': '已有任务正在运行'})
    
    data = request.json
    newspaper_name = data.get('newspaper_name', '人民日报')
    date_str = data.get('date', 'today')
    use_ai = data.get('use_ai', True)
    save_file = data.get('save_file', True)
    save_db = data.get('save_db', False)
    
    # 重置任务状态
    task_status = {
        'running': True,
        'progress': 0,
        'message': '任务开始...',
        'result': None,
        'error': None
    }
    
    # 在后台运行任务
    thread = threading.Thread(
        target=run_newspaper_task,
        args=(newspaper_name, date_str, use_ai, save_file, save_db)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': '任务已开始'})

@app.route('/api/task/stop', methods=['POST'])
def stop_task():
    """停止任务"""
    global task_status
    task_status['running'] = False
    task_status['message'] = '任务已停止'
    return jsonify({'message': '任务已停止'})

@app.route('/api/download/<filename>')
def download_file(filename):
    """下载文件"""
    file_path = os.path.join('newspaper_copies', filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    return jsonify({'error': '文件不存在'})

@app.route('/api/history')
def get_history():
    """获取历史记录"""
    history = []
    
    # 检查报纸图片目录
    if os.path.exists('newspaper_images'):
        for file in os.listdir('newspaper_images'):
            if file.endswith(('.jpg', '.pdf')):
                parts = file.replace('.jpg', '').replace('.pdf', '').split('_')
                if len(parts) >= 2:
                    history.append({
                        'newspaper_name': parts[0],
                        'date': parts[1],
                        'type': 'image',
                        'file_path': f'newspaper_images/{file}',
                        'timestamp': os.path.getctime(f'newspaper_images/{file}')
                    })
    
    # 检查解析结果目录
    if os.path.exists('newspaper_copies'):
        for file in os.listdir('newspaper_copies'):
            if file.endswith('.txt'):
                parts = file.replace('_精华内容.txt', '').split('_')
                if len(parts) >= 2:
                    history.append({
                        'newspaper_name': parts[0],
                        'date': parts[1],
                        'type': 'analysis',
                        'file_path': f'newspaper_copies/{file}',
                        'timestamp': os.path.getctime(f'newspaper_copies/{file}')
                    })
    
    # 按时间排序
    history.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify(history)

@app.route('/api/history/delete', methods=['POST'])
def delete_history():
    """删除历史记录"""
    data = request.json
    file_path = data.get('file_path')
    
    if not file_path:
        return jsonify({'success': False, 'message': '文件路径不能为空'})
    
    # 验证文件路径安全性
    if '..' in file_path or not (file_path.startswith('newspaper_images/') or file_path.startswith('newspaper_copies/')):
        return jsonify({'success': False, 'message': '无效的文件路径'})
    
    try:
        # 检查文件是否存在
        if os.path.exists(file_path):
            # 删除文件
            os.remove(file_path)
            return jsonify({'success': True, 'message': '删除成功'})
        else:
            return jsonify({'success': False, 'message': '文件不存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})

# 定时任务API
@app.route('/api/scheduler/tasks')
def get_scheduler_tasks():
    """获取所有定时任务"""
    return jsonify(scheduler.get_tasks())

@app.route('/api/scheduler/tasks', methods=['POST'])
def add_scheduler_task():
    """添加定时任务"""
    data = request.json
    task_id = f"task_{int(time.time())}"
    newspaper_name = data.get('newspaper_name', '人民日报')
    time_str = data.get('time', '08:00')
    enabled = data.get('enabled', True)
    use_ai = data.get('use_ai', True)
    save_file = data.get('save_file', True)
    save_db = data.get('save_db', False)
    
    success, message = scheduler.add_task(task_id, newspaper_name, time_str, enabled, use_ai, save_file, save_db)
    if success:
        return jsonify({'success': True, 'message': message, 'task_id': task_id})
    else:
        return jsonify({'success': False, 'message': message})

@app.route('/api/scheduler/tasks/<task_id>', methods=['PUT'])
def update_scheduler_task(task_id):
    """更新定时任务"""
    data = request.json
    success, message = scheduler.update_task(task_id, **data)
    return jsonify({'success': success, 'message': message})

@app.route('/api/scheduler/tasks/<task_id>', methods=['DELETE'])
def delete_scheduler_task(task_id):
    """删除定时任务"""
    success, message = scheduler.delete_task(task_id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/scheduler/tasks/<task_id>/toggle', methods=['POST'])
def toggle_scheduler_task(task_id):
    """切换任务状态"""
    success, message = scheduler.toggle_task(task_id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/scheduler/running')
def get_running_tasks():
    """获取运行中的任务"""
    return jsonify(scheduler.get_running_tasks())

@app.route('/api/scheduler/history')
def get_task_history():
    """获取任务历史"""
    limit = request.args.get('limit', 50, type=int)
    return jsonify(scheduler.get_task_history(limit))

@app.route('/api/scheduler/logs')
def get_task_logs():
    """获取任务日志"""
    days = request.args.get('days', 7, type=int)
    return jsonify(scheduler.get_task_logs(days))

@app.route('/api/scheduler/history/delete', methods=['POST'])
def delete_task_history():
    """删除任务历史"""
    data = request.json
    task_id = data.get('task_id')
    
    success, message = scheduler.delete_task_history(task_id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/scheduler/start', methods=['POST'])
def start_scheduler():
    """启动调度器"""
    scheduler.start()
    return jsonify({'success': True, 'message': '调度器已启动'})

@app.route('/api/scheduler/stop', methods=['POST'])
def stop_scheduler():
    """停止调度器"""
    scheduler.stop()
    return jsonify({'success': True, 'message': '调度器已停止'})

# 关键词管理API
@app.route('/api/keywords')
def get_keywords():
    """获取所有关键词"""
    return jsonify(keyword_manager.get_keywords())

@app.route('/api/keywords', methods=['POST'])
def add_keyword():
    """添加关键词"""
    data = request.json
    keyword = data.get('keyword')
    categories = data.get('categories', [])
    
    success, message = keyword_manager.add_keyword(keyword, categories)
    return jsonify({'success': success, 'message': message})

@app.route('/api/keywords/<keyword>', methods=['PUT'])
def update_keyword(keyword):
    """更新关键词"""
    data = request.json
    categories = data.get('categories', [])
    
    success, message = keyword_manager.update_keyword(keyword, categories)
    return jsonify({'success': success, 'message': message})

@app.route('/api/keywords/<keyword>', methods=['DELETE'])
def delete_keyword(keyword):
    """删除关键词"""
    success, message = keyword_manager.delete_keyword(keyword)
    return jsonify({'success': success, 'message': message})

@app.route('/api/keywords/search')
def search_keywords():
    """搜索关键词"""
    query = request.args.get('q', '')
    results = keyword_manager.search_keywords(query)
    return jsonify(results)

@app.route('/api/keywords/by-category/<category>')
def get_keywords_by_category(category):
    """按分类获取关键词"""
    results = keyword_manager.get_keywords_by_category(category)
    return jsonify(results)

# 分类管理API
@app.route('/api/categories')
def get_categories():
    """获取所有分类"""
    return jsonify(keyword_manager.get_categories())

@app.route('/api/categories', methods=['POST'])
def add_category():
    """添加分类"""
    data = request.json
    category_id = data.get('id')
    name = data.get('name')
    description = data.get('description', '')
    
    success, message = keyword_manager.add_category(category_id, name, description)
    return jsonify({'success': success, 'message': message})

@app.route('/api/categories/<category_id>', methods=['PUT'])
def update_category(category_id):
    """更新分类"""
    data = request.json
    name = data.get('name')
    description = data.get('description', '')
    
    success, message = keyword_manager.update_category(category_id, name, description)
    return jsonify({'success': success, 'message': message})

@app.route('/api/categories/<category_id>', methods=['DELETE'])
def delete_category(category_id):
    """删除分类"""
    success, message = keyword_manager.delete_category(category_id)
    return jsonify({'success': success, 'message': message})

# 导入导出API
@app.route('/api/keywords/import', methods=['POST'])
def import_keywords():
    """导入关键词"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': '没有上传文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': '文件名为空'})
    
    if file and file.filename.endswith('.csv'):
        file_path = f'keywords_import_{int(time.time())}.csv'
        file.save(file_path)
        
        success, message = keyword_manager.import_keywords(file_path)
        os.remove(file_path)
        
        return jsonify({'success': success, 'message': message})
    else:
        return jsonify({'success': False, 'message': '请上传CSV文件'})

@app.route('/api/keywords/export')
def export_keywords():
    """导出关键词"""
    file_path = f'keywords_export_{int(time.time())}.csv'
    success, message = keyword_manager.export_keywords(file_path)
    
    if success:
        return send_file(file_path, as_attachment=True, download_name='keywords.csv')
    else:
        return jsonify({'success': False, 'message': message})

# 新闻分类API
@app.route('/api/categorize', methods=['POST'])
def categorize_news():
    """新闻分类"""
    data = request.json
    title = data.get('title', '')
    content = data.get('content', '')
    
    categories = keyword_manager.categorize_news(title, content)
    return jsonify({'categories': categories})

# 新闻分析API
@app.route('/api/analyze/history')
def analyze_history():
    """分析历史新闻"""
    analyzed_count = news_analyzer.analyze_history()
    return jsonify({'success': True, 'analyzed_count': analyzed_count, 'message': f'成功分析 {analyzed_count} 条新闻'})

@app.route('/api/analyze/keywords')
def get_top_keywords():
    """获取高频关键词"""
    top_n = request.args.get('top_n', 20, type=int)
    keywords = news_analyzer.get_top_keywords(top_n)
    # 转换为列表格式
    keywords_list = [{'keyword': kw, 'frequency': freq} for kw, freq in keywords]
    return jsonify(keywords_list)

@app.route('/api/analyze/news/<keyword>')
def get_news_by_keyword(keyword):
    """根据关键词获取相关新闻"""
    news = news_analyzer.get_news_by_keyword(keyword)
    return jsonify(news)

@app.route('/api/analyze/search')
def search_news():
    """搜索新闻"""
    query = request.args.get('q', '')
    results = news_analyzer.search_news(query)
    return jsonify(results)

@app.route('/api/analyze/related/<keyword>')
def get_related_keywords(keyword):
    """获取相关关键词"""
    top_n = request.args.get('top_n', 5, type=int)
    related = news_analyzer.get_related_keywords(keyword, top_n)
    return jsonify(related)

@app.route('/api/analyze/advanced-search', methods=['POST'])
def advanced_search():
    """高级搜索新闻"""
    data = request.json
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    categories = data.get('categories')
    newspapers = data.get('newspapers')
    keyword = data.get('keyword')
    exact_match = data.get('exact_match', False)
    title_query = data.get('title_query')
    page = data.get('page', 1)
    page_size = data.get('page_size', 20)
    
    results = news_analyzer.advanced_search(
        start_date=start_date,
        end_date=end_date,
        categories=categories,
        newspapers=newspapers,
        keyword=keyword,
        exact_match=exact_match,
        title_query=title_query,
        page=page,
        page_size=page_size
    )
    return jsonify(results)

@app.route('/api/analyze/search-history')
def get_search_history():
    """获取搜索历史"""
    limit = request.args.get('limit', 10, type=int)
    history = news_analyzer.get_search_history(limit)
    return jsonify(history)

# 创建模板目录
if not os.path.exists('templates'):
    os.makedirs('templates')

# 创建HTML模板
@app.route('/templates/<path:filename>')
def serve_template(filename):
    """提供模板文件"""
    return send_file(os.path.join('templates', filename))

if __name__ == '__main__':
    # 确保必要的目录存在
    init_folders()
    
    print("🚀 启动Web界面...")
    print("📱 访问地址: http://localhost:5000")
    print("💡 按 Ctrl+C 停止服务")
    
    app.run(debug=True, host='0.0.0.0', port=5000)