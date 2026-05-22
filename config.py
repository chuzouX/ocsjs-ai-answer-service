# -*- coding: utf-8 -*-
"""
配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 基础配置
class Config:
    # 服务配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # OpenAI配置
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    # OpenAI API Base URL，如果不设置则使用默认值
    OPENAI_API_BASE = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # 安全配置（可选）
    ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", None)
    
    # 响应配置
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 500))
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))
    
    # 缓存配置
    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "True").lower() == "true"
    CACHE_EXPIRATION = int(os.getenv("CACHE_EXPIRATION", 86400))  # 默认缓存24小时
    
    # 备用API配置（可选）
    BACKUP_OPENAI_API_KEY = os.getenv("BACKUP_OPENAI_API_KEY", "")
    BACKUP_OPENAI_MODEL = os.getenv("BACKUP_OPENAI_MODEL", "gpt-3.5-turbo")
    BACKUP_OPENAI_API_BASE = os.getenv("BACKUP_OPENAI_API_BASE", "https://api.openai.com/v1")
    
    # 代理配置（可选）
    OPENAI_PROXY = os.getenv("OPENAI_PROXY", "")
    BACKUP_OPENAI_PROXY = os.getenv("BACKUP_OPENAI_PROXY", "")