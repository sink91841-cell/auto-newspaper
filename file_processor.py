#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理模块 - 负责文件转换和内容保存
"""

import os
import base64
import io
from PIL import Image
from config import COPY_FOLDER


def image_to_base64(image_path):
    """将图片转为base64编码（适配AI接口）"""
    try:
        # 打开并压缩图片（减少传输大小）
        img = Image.open(image_path)
        
        # 调整图片大小，确保符合API要求
        max_size = 800  # 更小的尺寸，减少内容审核风险
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # 确保图片模式为RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 保存到字节流并转base64
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=75)  # 适中的质量
        img_byte_arr = img_byte_arr.getvalue()
        
        # 检查数据大小
        if len(img_byte_arr) > 3 * 1024 * 1024:  # 3MB限制
            print("⚠️  图片数据过大，正在进一步压缩...")
            # 进一步压缩
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=60)
            img_byte_arr = img_byte_arr.getvalue()
        
        base64_data = base64.b64encode(img_byte_arr).decode('utf-8')
        print(f"✅ 图片转base64成功，数据大小：{len(base64_data) / 1024:.2f} KB")
        return base64_data
    except Exception as e:
        print(f"❌ 图片转base64失败：{str(e)}")
        return None


def pdf_to_image_base64(pdf_path):
    """将PDF第一页转为图片并编码为base64"""
    try:
        from pdf2image import convert_from_path
        
        # 提取PDF第一页（降低dpi以减少大小）
        print("📄 正在提取PDF第一页并转为图片...")
        pages = convert_from_path(
            pdf_path, 
            first_page=1, 
            last_page=1, 
            dpi=120,  # 更低的dpi，减少内容审核风险
            poppler_path=None  # Windows用户需指定poppler路径，如 r'C:\poppler-24.02.0\Library\bin'
        )
        
        # 处理图片
        img = pages[0]
        
        # 调整图片大小，确保符合API要求
        max_size = 800  # 更小的尺寸，减少内容审核风险
        if img.width > max_size or img.height > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # 确保图片模式为RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # 转为base64
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=75)  # 适中的质量
        img_byte_arr = img_byte_arr.getvalue()
        
        # 检查数据大小
        if len(img_byte_arr) > 3 * 1024 * 1024:  # 3MB限制
            print("⚠️  图片数据过大，正在进一步压缩...")
            # 进一步压缩
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='JPEG', quality=60)
            img_byte_arr = img_byte_arr.getvalue()
        
        base64_data = base64.b64encode(img_byte_arr).decode('utf-8')
        print(f"✅ PDF转base64成功，数据大小：{len(base64_data) / 1024:.2f} KB")
        return base64_data
    
    except ImportError:
        print("❌ 缺少PDF处理库，请先安装：pip install pdf2image")
        print("💡 Windows用户还需下载poppler：https://github.com/oschwartz10612/poppler-windows/releases")
        return None
    except Exception as e:
        print(f"❌ PDF转图片失败：{str(e)}")
        return None


def clean_ai_content(content):
    """清理AI生成的内容，去除重复和无效信息"""
    if not content or not content.strip():
        return ""
    
    lines = content.strip().split('\n')
    cleaned_lines = []
    seen_titles = set()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 检测重复标题
        if '**' in line and line.count('**') >= 2:
            # 提取标题内容（去除**标记）
            title = line.replace('**', '').strip()
            if title in seen_titles:
                continue  # 跳过重复标题
            seen_titles.add(title)
        
        # 检测数字编号的重复行
        if '.' in line and line.split('.')[0].strip().isdigit():
            # 检查是否是重复编号
            num_part = line.split('.')[0].strip()
            content_part = line.split('.', 1)[1].strip() if '.' in line else line
            if content_part in seen_titles:
                continue
            seen_titles.add(content_part)
        
        cleaned_lines.append(line)
    
    # 如果清理后内容过少，可能是AI幻觉，返回空内容
    if len(cleaned_lines) <= 3:
        return "⚠️ AI解析结果可能存在问题，建议重新解析或检查图片质量"
    
    return '\n'.join(cleaned_lines)

def parse_ai_content(content, newspaper_name, date_str):
    """解析AI生成的内容，提取新闻标题和摘要"""
    if not content or not content.strip():
        return []
    
    # 先清理内容
    cleaned_content = clean_ai_content(content)
    if cleaned_content.startswith('⚠️'):
        print(cleaned_content)
        return []
    
    summaries = []
    lines = cleaned_content.strip().split('\n')
    current_title = None
    current_summary = []
    seen_titles = set()
    
    for line in lines:
        line = line.strip()
        if line.startswith('【头条新闻'):
            # 保存上一条新闻
            if current_title and current_summary:
                if current_title not in seen_titles:
                    summaries.append((newspaper_name, date_str, current_title, ' '.join(current_summary)))
                    seen_titles.add(current_title)
            # 提取新标题
            title_match = line.split('】', 1)
            if len(title_match) > 1:
                current_title = title_match[1].strip()
                current_summary = []
        elif line.startswith('📝 核心内容：') and current_title:
            # 提取摘要
            summary = line.replace('📝 核心内容：', '').strip()
            current_summary.append(summary)
        elif '**' in line and line.count('**') >= 2:
            # 处理加粗标题格式
            title = line.replace('**', '').strip()
            if title not in seen_titles:
                summaries.append((newspaper_name, date_str, title, ""))
                seen_titles.add(title)
    
    # 保存最后一条新闻
    if current_title and current_summary and current_title not in seen_titles:
        summaries.append((newspaper_name, date_str, current_title, ' '.join(current_summary)))
    
    return summaries

def save_content_to_file(content, newspaper_name, date_str):
    """保存AI解析后的精华内容"""
    if not content or not content.strip():
        print("❌ 内容为空，无法保存")
        return None

    filename = f"{newspaper_name}_{date_str}_精华内容.txt"
    file_path = os.path.join(COPY_FOLDER, filename)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 精华内容已保存到：{file_path}")
        return file_path
    except Exception as e:
        print(f"❌ 保存失败：{str(e)}")
        return None
