# 采购联系人查找器

基于 AI 的智能采购联系人查找系统，提供现代化的Web界面，能够自动搜索公司信息并提取采购相关联系人。

## 功能特点

- 🌐 **现代化Web界面**: 美观易用的前端界面
- 🔍 **Google 搜索**: 使用 Google Custom Search API 搜索公司相关信息
- 🕷️ **深度爬取**: 使用 crawl4ai 深度爬取官网，智能过滤相关页面
- 🤖 **AI 提取**: 使用 GPT-4o-mini 智能提取联系人信息
- ⚡ **异步处理**: 高效的异步爬取和处理
- 📊 **实时统计**: 显示搜索进度和结果统计
- 📱 **响应式设计**: 支持桌面和移动设备

## 安装依赖

```bash
pip install -r requirements.txt
```

或者手动安装：

```bash
pip install flask flask-cors requests python-dotenv crawl4ai openai
```

## 配置 API 密钥

1. 复制 `config.env` 文件
2. 填入您的 API 密钥：
   - `GOOGLE_API_KEY`: Google Custom Search API 密钥
   - `CSE_ID`: Google Custom Search Engine ID
   - `OPENAI_API_KEY`: OpenAI API 密钥

## 运行程序

### 方式一：使用Web界面（推荐）

```bash
python start_server.py
```

然后在浏览器中打开：http://localhost:5000

### 方式二：直接运行Flask应用

```bash
python app.py
```

### 方式三：命令行模式

```bash
python main.py
```

## 获取 Google Custom Search API

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 Custom Search API
4. 创建 API 密钥
5. 访问 [Google Custom Search Engine](https://cse.google.com/)
6. 创建自定义搜索引擎
7. 获取搜索引擎 ID (CSE_ID)

## 项目结构

```
purcahse manager finder/
├── app.py                       # Flask Web应用主文件
├── main.py                      # 核心搜索逻辑
├── start_server.py              # 启动脚本
├── config.env                   # API密钥配置
├── requirements.txt             # Python依赖
├── templates/
│   └── index.html              # Web前端界面
└── README.md                   # 项目说明

核心模块:
├── google_search()              # Google 搜索模块
├── deep_crawl()                 # 深度爬取模块  
├── clean_contacts_with_openai() # AI 联系人提取模块
├── investigate_company()        # 主流程控制
└── Flask API 接口               # Web API服务
```

## 核心流程

1. **Web界面输入**: 用户在前端输入公司名称
2. **Google 搜索**: 搜索公司名称，获取候选网址
3. **深度爬取**: 对候选网址进行深度爬取，过滤相关页面
4. **AI 提取**: 使用 GPT-4o-mini 智能提取联系人信息
5. **结果展示**: 在前端界面展示结构化的联系人信息
6. **统计报告**: 显示搜索统计和采购相关联系人

## Web界面功能

- 📝 **简单输入**: 只需输入公司名称即可开始搜索
- ⏳ **实时进度**: 显示搜索进度和状态
- 📊 **结果统计**: 显示找到的联系人数量统计
- 🏷️ **标签分类**: 自动标记采购相关联系人
- 💡 **搜索建议**: 提供后续搜索建议
- 📱 **移动友好**: 响应式设计，支持手机访问

## 注意事项

- 需要有效的 Google Custom Search API 和 OpenAI API 密钥
- 爬取过程可能需要一些时间，请耐心等待
- 建议在测试环境中先验证 API 密钥的有效性
- 程序会自动保存结果到 JSON 文件

## 故障排除

### 常见错误

1. **API 密钥错误**: 检查 `config.env` 文件中的密钥是否正确
2. **网络连接问题**: 确保网络连接正常
3. **依赖缺失**: 运行 `pip install` 安装所需依赖

### 调试模式

在代码中添加更多日志输出：
```python
config = CrawlerRunConfig(
    # ... 其他配置
    verbose=True  # 启用详细日志
)
```

## 输出格式

程序会生成以下输出：
- 控制台显示搜索进度和结果
- JSON 文件保存详细的联系人信息
- 自动识别采购相关联系人并优先显示
