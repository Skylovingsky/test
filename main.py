import requests
import asyncio
from urllib.parse import urlparse
import os
from dotenv import load_dotenv
import json
import logging

# ✅ 优化：设置日志级别，减少输出
logging.basicConfig(level=logging.WARNING)

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import FilterChain, DomainFilter, URLPatternFilter, ContentTypeFilter
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from openai import OpenAI

# 加载环境变量
load_dotenv('config.env')

# ============ 1. Google 搜索 ============

def google_search(query: str, api_key: str, cse_id: str, num_results: int = 30):
    """调用 Google Custom Search API，返回 URL 列表"""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cse_id,
        "num": 10
    }
    results = []
    start = 1
    while len(results) < num_results:
        params["start"] = start
        resp = requests.get(url, params=params).json()
        items = resp.get("items", [])
        for item in items:
            results.append(item["link"])
        start += 10
        if not items:
            break
    return results[:num_results]


def get_domain(url: str):
    return urlparse(url).netloc


# ============ 2. 深度爬取官网 ============

async def deep_crawl(url: str):
    """用 crawl4ai 对一个网址做深度爬取"""
    filter_chain = FilterChain([
        DomainFilter(allowed_domains=[get_domain(url)]),
        URLPatternFilter(patterns=["*contact*", "*about*", "*team*", "*procurement*"]),
        ContentTypeFilter(allowed_types=["text/html"])
    ])

    keyword_scorer = KeywordRelevanceScorer(
        keywords=["purchase", "procurement", "buyer", "contact", "email"],
        weight=0.8
    )

    config = CrawlerRunConfig(
        deep_crawl_strategy=BestFirstCrawlingStrategy(
            max_depth=2,
            include_external=False,
            filter_chain=filter_chain,
            url_scorer=keyword_scorer
        ),
        scraping_strategy=LXMLWebScrapingStrategy(),
        stream=True,
        verbose=False
    )

    async with AsyncWebCrawler() as crawler:
        pages = []
        async for result in await crawler.arun(url, config=config):
            pages.append(result)
        return pages


# ============ 3. AI 清洗联系人 ============

async def clean_contacts_with_openai(urls, openai_api_key: str):
    """使用 OpenAI API 对页面内容做AI清洗，提取联系人信息"""
    client = OpenAI(api_key=openai_api_key)
    
    results = []
    async with AsyncWebCrawler() as crawler:
        for url in urls:
            try:
                # 获取页面内容
                result = await crawler.arun(url)
                if result.success and result.markdown:
                    content = result.markdown
                    
                    # 使用 OpenAI 提取联系人信息
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": """你是一个专业的联系人信息提取助手。请从网页内容中提取联系人信息，特别关注采购、采购经理、采购负责人等相关职位。

请按照以下JSON格式输出结果：
{
  "contacts_found": [
    {
      "name": "联系人姓名",
      "position": "职位",
      "email": "邮箱地址",
      "phone": "电话号码",
      "department": "部门",
      "is_procurement_related": true/false
    }
  ],
  "search_hints": ["如果没找到联系人，提供后续搜索建议"]
}

如果没有找到任何联系人信息，请将 contacts_found 设为空数组，并在 search_hints 中提供搜索建议。"""
                            },
                            {
                                "role": "user",
                                "content": f"请从以下网页内容中提取联系人信息：\n\nURL: {url}\n\n内容：\n{content[:4000]}"  # 限制内容长度
                            }
                        ],
                        temperature=0.1
                    )
                    
                    try:
                        extracted_data = json.loads(response.choices[0].message.content)
                        results.append({
                            "url": url,
                            "contacts": extracted_data.get("contacts_found", []),
                            "search_hints": extracted_data.get("search_hints", [])
                        })
                    except json.JSONDecodeError:
                        # 如果JSON解析失败，尝试提取文本中的信息
                        text_content = response.choices[0].message.content
                        results.append({
                            "url": url,
                            "contacts": [],
                            "search_hints": [text_content],
                            "raw_response": text_content
                        })
                        
            except Exception as e:
                print(f"Error processing {url}: {e}")
                results.append({
                    "url": url,
                    "contacts": [],
                    "search_hints": [f"处理错误: {str(e)}"],
                    "error": str(e)
                })
    
    return results


# ============ 4. 总体流程 ============

def investigate_company(company_name, google_api_key, cse_id, openai_api_key):
    """调查公司并提取采购联系人信息"""
    print(f"🔍 正在搜索公司: {company_name}")
    
    # Step 1: Google 搜索
    urls = google_search(company_name, google_api_key, cse_id)
    print(f"找到 {len(urls)} 个候选网址")
    
    if not urls:
        print("❌ 没有找到相关网址")
        return []
    
    # Step 2: 深度爬取
    print("🌐 正在爬取候选网址...")
    all_urls = []
    for url in urls[:3]:  # 限制前3个URL避免过多请求
        try:
            pages = asyncio.run(deep_crawl(url))
            all_urls.extend([p.url for p in pages])
            print(f"从 {url} 爬取了 {len(pages)} 个页面")
        except Exception as e:
            print(f"爬取 {url} 时出错: {e}")
    
    if not all_urls:
        print("❌ 没有成功爬取到任何页面")
        return []
    
    print(f"总共收集到 {len(all_urls)} 个页面URL")
    
    # Step 3: AI 清洗联系人
    print("🤖 正在用 AI 提取联系人信息...")
    contacts_results = asyncio.run(clean_contacts_with_openai(all_urls, openai_api_key))
    
    # 汇总结果
    all_contacts = []
    all_search_hints = []
    
    for result in contacts_results:
        all_contacts.extend(result["contacts"])
        all_search_hints.extend(result["search_hints"])
    
    # 过滤出采购相关联系人
    procurement_contacts = [c for c in all_contacts if c.get("is_procurement_related", False)]
    
    print(f"\n📊 结果统计:")
    print(f"总联系人: {len(all_contacts)}")
    print(f"采购相关联系人: {len(procurement_contacts)}")
    
    if procurement_contacts:
        print("\n✅ 找到采购相关联系人：")
        for contact in procurement_contacts:
            print(f"  - {contact.get('name', 'N/A')} ({contact.get('position', 'N/A')})")
            if contact.get('email'):
                print(f"    邮箱: {contact['email']}")
            if contact.get('phone'):
                print(f"    电话: {contact['phone']}")
            print()
    elif all_contacts:
        print("\n⚠️ 找到联系人但无采购相关：")
        for contact in all_contacts[:5]:  # 只显示前5个
            print(f"  - {contact.get('name', 'N/A')} ({contact.get('position', 'N/A')})")
    else:
        print("\n❌ 未找到任何联系人信息")
        if all_search_hints:
            print("搜索建议：")
            for hint in all_search_hints[:3]:
                print(f"  - {hint}")
    
    return {
        "company": company_name,
        "total_contacts": len(all_contacts),
        "procurement_contacts": len(procurement_contacts),
        "contacts": all_contacts,
        "procurement_contacts_list": procurement_contacts,
        "search_hints": all_search_hints
    }


# ============ 5. 主程序入口 ============

if __name__ == "__main__":
    # 从环境变量获取API密钥
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    CSE_ID = os.getenv('CSE_ID')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    if not all([GOOGLE_API_KEY, CSE_ID, OPENAI_API_KEY]):
        print("❌ 请确保在 config.env 文件中配置了所有必需的API密钥：")
        print("   - GOOGLE_API_KEY")
        print("   - CSE_ID")
        print("   - OPENAI_API_KEY")
        exit(1)
    
    # 测试公司
    company = "Shree Prayag Air Controls"
    
    print("🚀 采购联系人查找器启动")
    print("=" * 50)
    
    result = investigate_company(company, GOOGLE_API_KEY, CSE_ID, OPENAI_API_KEY)
    
    print("\n" + "=" * 50)
    print("🎯 调查完成")
    
    # 保存结果到文件
    if result:
        with open(f"{company.replace(' ', '_')}_contacts.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"📁 结果已保存到: {company.replace(' ', '_')}_contacts.json")
