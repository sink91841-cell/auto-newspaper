#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI客户端模块 - 负责调用AI接口解析报纸内容
"""

import os
import time
from config import TONGYI_API_KEY, AI_ANALYSIS_PROMPT, AI_TEMPERATURE, AI_MAX_TOKENS, AI_TOP_P
from file_processor import image_to_base64, pdf_to_image_base64
from logger import logger


def analyze_with_free_ai(file_path, newspaper_name, date_str):
    """调用通义千问免费AI提取图片/PDF精华内容"""
    logger.info(f"开始AI解析 {newspaper_name} 内容")
    print(f"🤖 开始AI解析 {newspaper_name} 内容...")
    
    if not os.path.exists(file_path):
        logger.error(f"文件不存在：{file_path}")
        print(f"❌ 错误：文件 {file_path} 不存在")
        return None

    # 检查API Key是否配置
    if not TONGYI_API_KEY or TONGYI_API_KEY == "your-dashscope-api-key":
        logger.error("未配置通义千问API Key")
        print("❌ 错误：未配置通义千问API Key，请在.env文件中设置TONGYI_API_KEY")
        return None

    # 1. 处理文件，转为base64
    logger.debug(f"处理文件：{file_path}")
    if file_path.endswith(".pdf"):
        base64_data = pdf_to_image_base64(file_path)
    else:
        base64_data = image_to_base64(file_path)
    
    if not base64_data:
        logger.error("文件转base64失败")
        print("❌ 文件转base64失败，无法进行AI解析")
        return None

    # 2. 构建AI请求
    try:
        # 安装OpenAI SDK
        try:
            from openai import OpenAI
        except ImportError:
            logger.error("未安装OpenAI SDK，请运行: pip install openai")
            print("❌ 未安装OpenAI SDK，请运行: pip install openai")
            return None

        # 创建OpenAI客户端
        client = OpenAI(
            api_key=TONGYI_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

        # 构建提示词（根据报纸类型使用不同的提示词）
        default_prompt = """请客观分析这张报纸图片，仅提取其中的文字信息和新闻标题。请使用正式、中立的语言，不要添加任何评论或分析，只提供图片中实际存在的信息。

要求：
1. 只提取图片中实际存在的文字内容
2. 不要编造或重复任何信息
3. 每条新闻标题只出现一次
4. 如果图片内容较少，请如实反映
5. 避免任何形式的重复输出

格式要求：
- 每条新闻标题单独一行
- 使用简洁的语言
- 不要添加序号或编号"""
        
        # 针对纽约时报的特殊提示词（英文翻译成中文）
        if newspaper_name == "纽约时报":
            prompt = """请分析这张纽约时报报纸图片，完成以下任务：

1. 提取图片中的所有英文文字信息，包括新闻标题、副标题、摘要等
2. 将所有英文内容翻译成中文，保持原文的语气和风格
3. 用简洁的语言总结3-5条重要新闻，每条新闻包含：
   - 中文标题（翻译后的标题）
   - 英文原标题（括号内标注）
   - 中文摘要（50字左右）

重要要求：
- 只提取图片中实际存在的文字内容
- 不要编造或重复任何信息
- 每条新闻标题只出现一次
- 如果图片内容较少，请如实反映
- 避免任何形式的重复输出

请使用正式、中立的中文语言，确保翻译准确、流畅。"""
        else:
            # 其他报纸使用配置的提示词或默认提示词
            prompt_template = AI_ANALYSIS_PROMPT if AI_ANALYSIS_PROMPT else default_prompt
            prompt = prompt_template

        # 构建消息
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_data}"}}
                ]
            }
        ]

        # 3. 调用AI接口
        logger.info("正在调用通义千问AI解析...")
        print("🚀 正在调用通义千问AI解析...（请稍候）")
        
        # 检查base64数据长度，确保不超过API限制
        if base64_data and len(base64_data) > 10 * 1024 * 1024:  # 10MB限制
            logger.warning("图片数据过大，可能会被API拒绝")
            print("⚠️  图片数据过大，正在尝试压缩...")
        
        # 验证base64数据
        if not base64_data or base64_data.strip() == "":
            logger.error("Base64数据为空，无法进行AI解析")
            print("❌ Base64数据为空，无法进行AI解析")
            return None
        
        # 验证请求参数
        if not prompt or prompt.strip() == "":
            logger.error("提示词为空，无法进行AI解析")
            print("❌ 提示词为空，无法进行AI解析")
            return None
        
        # 添加请求重试机制
        max_retries = 3
        retry_delay = 2  # 初始重试延迟（秒）
        
        for retry in range(max_retries):
            try:
                completion = client.chat.completions.create(
                    model="qwen-vl-plus",  # 通义千问多模态模型
                    messages=messages,
                    temperature=AI_TEMPERATURE,
                    max_tokens=AI_MAX_TOKENS,
                    top_p=AI_TOP_P
                )
                break  # 成功，跳出重试循环
            except Exception as e:
                # 网络错误或API错误，进行重试
                if retry < max_retries - 1:
                    logger.warning(f"AI调用失败：{str(e)}，正在重试... ({retry + 1}/{max_retries})")
                    print(f"⚠️  AI调用失败：{str(e)}，正在重试... ({retry + 1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                    continue
                else:
                    logger.error(f"AI调用失败：{str(e)}")
                    print(f"❌ AI调用失败：{str(e)}")
                    return None
        
        # 处理AI返回结果
        try:
            if completion and completion.choices and len(completion.choices) > 0:
                ai_content = completion.choices[0].message.content.strip()
                
                if ai_content:
                    logger.info("AI解析完成")
                    print("✅ AI解析完成！")
                    print("-" * 70)
                    print(ai_content)
                    print("-" * 70)
                    return ai_content
                else:
                    logger.warning("AI返回空内容")
                    print("❌ AI返回空内容，可能是解析失败")
                    return None
            else:
                logger.error("AI返回格式异常")
                print("❌ AI返回格式异常")
                return None
        except Exception as e:
            logger.error(f"解析AI返回内容时出错：{str(e)}")
            print(f"❌ 解析AI返回内容失败：{str(e)}")
            return None

    except Exception as e:
        logger.error(f"AI调用失败：{str(e)}")
        print(f"❌ AI调用失败：{str(e)}")
        return None