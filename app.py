from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import asyncio
import json
import os
from dotenv import load_dotenv
import logging

# 导入现有的功能模块
from main import investigate_company, google_search, deep_crawl, clean_contacts_with_openai

# 设置日志
logging.basicConfig(level=logging.WARNING)

# 加载环境变量
load_dotenv('config.env')

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 全局变量存储API密钥
API_KEYS = {
    'google_api_key': os.getenv('GOOGLE_API_KEY'),
    'cse_id': os.getenv('CSE_ID'),
    'openai_api_key': os.getenv('OPENAI_API_KEY')
}

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_company():
    """搜索公司联系人API"""
    try:
        data = request.get_json()
        company_name = data.get('company_name', '').strip()
        
        if not company_name:
            return jsonify({
                'success': False,
                'error': '公司名称不能为空'
            }), 400
        
        # 检查API密钥
        if not all(API_KEYS.values()):
            return jsonify({
                'success': False,
                'error': 'API密钥配置不完整，请检查config.env文件'
            }), 500
        
        print(f"🔍 开始搜索公司: {company_name}")
        
        # 调用现有的调查函数
        result = investigate_company(
            company_name,
            API_KEYS['google_api_key'],
            API_KEYS['cse_id'],
            API_KEYS['openai_api_key']
        )
        
        if result:
            return jsonify({
                'success': True,
                'data': result
            })
        else:
            return jsonify({
                'success': False,
                'error': '搜索失败，请稍后重试'
            }), 500
            
    except Exception as e:
        print(f"API错误: {e}")
        return jsonify({
            'success': False,
            'error': f'服务器内部错误: {str(e)}'
        }), 500

@app.route('/api/status', methods=['GET'])
def api_status():
    """API状态检查"""
    return jsonify({
        'success': True,
        'message': 'API运行正常',
        'api_keys_configured': all(API_KEYS.values())
    })

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置状态（不返回敏感信息）"""
    return jsonify({
        'google_api_configured': bool(API_KEYS['google_api_key']),
        'cse_id_configured': bool(API_KEYS['cse_id']),
        'openai_api_configured': bool(API_KEYS['openai_api_key'])
    })

if __name__ == '__main__':
    # 检查API密钥配置
    if not all(API_KEYS.values()):
        print("⚠️  警告: API密钥配置不完整")
        print("请确保在config.env文件中配置了以下密钥:")
        print("  - GOOGLE_API_KEY")
        print("  - CSE_ID") 
        print("  - OPENAI_API_KEY")
        print()
    
    print("🚀 Flask API服务器启动")
    print("📱 前端地址: http://localhost:5000")
    print("🔗 API文档: http://localhost:5000/api/status")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
