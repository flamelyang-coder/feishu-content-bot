from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn
import json
import requests
from article_analyzer import scrape_article, analyze_topic
from feishu_api import get_tenant_access_token, APP_TOKEN, TABLE_ID
from openai import OpenAI

app = FastAPI()
import os

# 从环境变量获取配置，默认使用 DeepSeek
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_API_BASE", "https://api.deepseek.com")
model_name = os.getenv("MODEL_NAME", "deepseek-chat")

client = OpenAI(api_key=api_key, base_url=base_url)

def update_feishu_record(record_id, fields):
    """更新飞书记录"""
    token = get_tenant_access_token()
    if not token:
        return
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/{record_id}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"fields": fields}
    requests.put(url, headers=headers, data=json.dumps(payload))

def process_new_url(record_id, url):
    """后台处理：采集与分析"""
    print(f"开始处理新 URL: {url}")
    data = scrape_article(url)
    if data:
        analysis = analyze_topic(data)
        if analysis:
            fields = {
                "文章标题": data["title"],
                "核心观点摘要": analysis["core_viewpoint"],
                "选题价值分析": analysis["topic_value"],
                "创作灵感": analysis["creative_inspiration"]
            }
            update_feishu_record(record_id, fields)
            print(f"记录 {record_id} 已更新分析结果。")

def generate_article_task(record_id, title, inspiration):
    """后台处理：生成文章"""
    print(f"开始为选题生成文章: {title}")
    prompt = f"请根据以下选题和灵感，写一篇硬核科技风的深度文章。\n选题：{title}\n灵感：{inspiration}"
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "你是一个资深科技博主，擅长撰写硬核且易读的科技深度报道。"},
                {"role": "user", "content": prompt}
            ]
        )
        article_content = response.choices[0].message.content
        
        # 这里我们可以将文章内容写入一个新的字段，或者更新状态
        # 假设我们有一个字段叫 "文章初稿"
        update_feishu_record(record_id, {
            "状态": "已生成"
            # 如果有 "文章初稿" 字段，可以取消下面注释
            # "文章初稿": article_content
        })
        print(f"记录 {record_id} 文章已生成。")
    except Exception as e:
        print(f"生成文章失败: {e}")

@app.post("/webhook")
async def feishu_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    print(f"收到 Webhook: {json.dumps(data)}")
    
    # 飞书挑战验证 (首次配置时需要)
    if data.get("type") == "url_verification":
        return {"challenge": data.get("challenge")}
    
    # 处理飞书自动化触发的请求
    # 假设飞书传来的 payload 包含 record_id 和触发类型
    event = data.get("event", {})
    record_id = event.get("record_id")
    action_type = event.get("action_type") # 自定义字段，由飞书配置
    
    if action_type == "analyze" and event.get("url"):
        background_tasks.add_task(process_new_url, record_id, event.get("url"))
    elif action_type == "generate" and event.get("title"):
        background_tasks.add_task(generate_article_task, record_id, event.get("title"), event.get("inspiration", ""))
        
    return {"status": "ok"}

if __name__ == "__main__":
    # 微信云托管默认使用 80 端口，或者通过 PORT 环境变量指定
    port = int(os.getenv("PORT", 80))
    uvicorn.run(app, host="0.0.0.0", port=port)
