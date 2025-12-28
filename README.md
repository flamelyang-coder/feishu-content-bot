# Feishu Content Bot

这是一个自动化的内容创作与分发智能体，集成了飞书多维表格、文章采集分析和 AI 内容生成功能。

## 功能特点
- **自动采集**：通过 Webhook 触发，自动抓取并分析文章。
- **AI 分析**：利用 GPT-4 级别模型进行选题深度拆解。
- **飞书集成**：自动同步分析结果至飞书多维表格。
- **自动生成**：一键生成硬核科技风深度文章。

## 部署说明
本仓库支持在 Zeabur, Railway 或任何支持 Docker 的平台上进行一键部署。
请确保配置以下环境变量：
- `OPENAI_API_KEY`
- `FEISHU_APP_ID`
- `FEISHU_APP_SECRET`
- `FEISHU_APP_TOKEN`
- `FEISHU_TABLE_ID`
