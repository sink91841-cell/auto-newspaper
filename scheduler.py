#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
定时任务管理模块 - 负责管理报纸下载定时任务
"""

import os
import time
import threading
import json
import schedule
from datetime import datetime, timedelta
from services.newspaper_tool import NewspaperTool
from downloader import download_newspaper_file
from ai_client import analyze_with_free_ai
from file_processor import save_content_to_file, parse_ai_content
from logger import logger

class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self):
        """初始化"""
        self.tasks = {}
        self.running_tasks = {}
        self.task_history = []
        self.scheduler_thread = None
        self.running = False
        self.config_file = 'scheduler_config.json'
        self.history_file = 'task_history.json'
        self.log_file = 'scheduler.log'
        
        # 加载配置
        self.load_config()
        self.load_history()
        
    def load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
                self.tasks = {}
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def load_history(self):
        """加载历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.task_history = json.load(f)
            except Exception as e:
                logger.error(f"加载历史记录失败: {e}")
                self.task_history = []
    
    def save_history(self):
        """保存历史记录"""
        try:
            # 只保留最近100条记录
            if len(self.task_history) > 100:
                self.task_history = self.task_history[-100:]
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.task_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存历史记录失败: {e}")
    
    def add_task(self, task_id, newspaper_name, time_str, enabled=True, use_ai=True, save_file=True, save_db=False):
        """添加定时任务"""
        # 验证时间格式
        try:
            datetime.strptime(time_str, '%H:%M')
        except ValueError:
            return False, "时间格式错误，请使用 HH:MM 格式"
        
        self.tasks[task_id] = {
            'newspaper_name': newspaper_name,
            'time': time_str,
            'enabled': enabled,
            'use_ai': use_ai,
            'save_file': save_file,
            'save_db': save_db,
            'created_at': datetime.now().isoformat()
        }
        
        self.save_config()
        self.update_schedule()
        return True, "任务添加成功"
    
    def update_task(self, task_id, **kwargs):
        """更新任务"""
        if task_id not in self.tasks:
            return False, "任务不存在"
        
        # 验证时间格式
        if 'time' in kwargs:
            try:
                datetime.strptime(kwargs['time'], '%H:%M')
            except ValueError:
                return False, "时间格式错误，请使用 HH:MM 格式"
        
        self.tasks[task_id].update(kwargs)
        self.save_config()
        self.update_schedule()
        return True, "任务更新成功"
    
    def delete_task(self, task_id):
        """删除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self.save_config()
            self.update_schedule()
            return True, "任务删除成功"
        return False, "任务不存在"
    
    def toggle_task(self, task_id):
        """切换任务状态"""
        if task_id in self.tasks:
            self.tasks[task_id]['enabled'] = not self.tasks[task_id]['enabled']
            self.save_config()
            self.update_schedule()
            status = "启用" if self.tasks[task_id]['enabled'] else "禁用"
            return True, f"任务已{status}"
        return False, "任务不存在"
    
    def update_schedule(self):
        """更新调度器"""
        # 清除所有任务
        schedule.clear()
        
        # 添加所有启用的任务
        for task_id, task in self.tasks.items():
            if task['enabled']:
                time_str = task['time']
                schedule.every().day.at(time_str).do(self.run_task, task_id)
    
    def run_task(self, task_id):
        """运行任务"""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        newspaper_name = task['newspaper_name']
        use_ai = task['use_ai']
        save_file = task['save_file']
        save_db = task['save_db']
        
        # 记录任务开始
        start_time = datetime.now()
        task_info = {
            'task_id': task_id,
            'newspaper_name': newspaper_name,
            'start_time': start_time.isoformat(),
            'status': 'running',
            'result': {}
        }
        
        self.running_tasks[task_id] = task_info
        self.log(f"任务开始: {task_id} - {newspaper_name}")
        
        try:
            # 下载报纸
            date_obj = datetime.now()
            date_str = date_obj.strftime('%Y-%m-%d')
            
            file_path = download_newspaper_file(newspaper_name, date_obj, date_str)
            
            if file_path:
                result = {
                    'newspaper_name': newspaper_name,
                    'date': date_str,
                    'file_path': file_path,
                    'ai_content': None,
                    'saved_files': [],
                    'saved_db': False
                }
                
                # AI解析
                if use_ai:
                    ai_content = analyze_with_free_ai(file_path, newspaper_name, date_str)
                    if ai_content:
                        result['ai_content'] = ai_content
                        
                        # 保存到文件
                        if save_file:
                            saved_file = save_content_to_file(ai_content, newspaper_name, date_str)
                            if saved_file:
                                result['saved_files'].append(saved_file)
                        
                        # 保存到数据库
                        if save_db:
                            tool = NewspaperTool()
                            if tool.db_manager.connect():
                                summaries = parse_ai_content(ai_content, newspaper_name, date_str)
                                if summaries:
                                    tool.db_manager.batch_insert_summaries(summaries)
                                    result['saved_db'] = True
                                tool.db_manager.close()
                
                task_info['result'] = result
                task_info['status'] = 'completed'
                self.log(f"任务完成: {task_id} - {newspaper_name}")
            else:
                task_info['status'] = 'failed'
                task_info['error'] = '报纸下载失败'
                self.log(f"任务失败: {task_id} - {newspaper_name} - 报纸下载失败")
                
        except Exception as e:
            task_info['status'] = 'failed'
            task_info['error'] = str(e)
            self.log(f"任务失败: {task_id} - {newspaper_name} - {str(e)}")
        
        # 记录任务结束
        end_time = datetime.now()
        task_info['end_time'] = end_time.isoformat()
        task_info['duration'] = (end_time - start_time).total_seconds()
        
        # 添加到历史记录
        self.task_history.append(task_info)
        self.save_history()
        
        # 从运行任务中移除
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
    
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        # 写入日志文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
        except Exception as e:
            pass
    
    def start(self):
        """启动调度器"""
        if not self.running:
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._run_scheduler)
            self.scheduler_thread.daemon = True
            self.scheduler_thread.start()
            self.log("调度器已启动")
    
    def _run_scheduler(self):
        """运行调度器"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        self.log("调度器已停止")
    
    def get_tasks(self):
        """获取所有任务"""
        return self.tasks
    
    def get_running_tasks(self):
        """获取运行中的任务"""
        return self.running_tasks
    
    def get_task_history(self, limit=50):
        """获取任务历史"""
        return self.task_history[-limit:]
    
    def get_task_logs(self, days=7):
        """获取任务日志"""
        logs = []
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            # 解析时间戳
                            if line.startswith('['):
                                timestamp_str = line[1:20]
                                try:
                                    log_time = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                    if (datetime.now() - log_time).days <= days:
                                        logs.append(line)
                                except:
                                    pass
            except Exception as e:
                pass
        return logs
    
    def delete_task_history(self, task_id=None):
        """删除任务历史
        
        Args:
            task_id: 要删除的任务ID，如果为None则删除所有历史
        """
        if task_id:
            # 删除指定任务的历史记录
            self.task_history = [history for history in self.task_history if history.get('task_id') != task_id]
        else:
            # 删除所有历史记录
            self.task_history = []
        
        self.save_history()
        return True, "任务历史删除成功"

# 全局调度器实例
scheduler = TaskScheduler()
