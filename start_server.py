#!/usr/bin/env python3
"""
采购联系人查找器 - 启动脚本
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """检查依赖是否安装"""
    try:
        import flask
        import requests
        import dotenv
        import crawl4ai
        import openai
        print("✅ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_config():
    """检查配置文件"""
    config_file = Path("config.env")
    if not config_file.exists():
        print("❌ 配置文件 config.env 不存在")
        return False
    
    # 读取配置
    from dotenv import load_dotenv
    load_dotenv(config_file)
    
    required_keys = ['GOOGLE_API_KEY', 'CSE_ID', 'OPENAI_API_KEY']
    missing_keys = []
    
    for key in required_keys:
        if not os.getenv(key):
            missing_keys.append(key)
    
    if missing_keys:
        print(f"❌ 配置文件中缺少以下密钥: {', '.join(missing_keys)}")
        print("请在 config.env 文件中配置所有必需的API密钥")
        return False
    
    print("✅ 配置文件检查通过")
    return True

def main():
    """主函数"""
    print("🚀 采购联系人查找器启动器")
    print("=" * 50)
    
    # 检查依赖
    if not check_requirements():
        return 1
    
    # 检查配置
    if not check_config():
        return 1
    
    print("\n🌐 启动Web服务器...")
    print("📱 前端地址: http://localhost:5000")
    print("🔗 API状态: http://localhost:5000/api/status")
    print("\n按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    try:
        # 启动Flask应用
        from app import app
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
        return 0
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
