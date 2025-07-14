# 🚀 快速开始指南

## 📋 前置要求

- Python 3.8+
- MySQL 数据库 (推荐) 或 SQLite
- Reddit API 账号

## ⚡ 5分钟快速启动

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 设置Reddit API
```bash
python setup_reddit_api.py
```
按照向导完成Reddit API配置

### 3. 设置智能提取 (可选但推荐)
```bash
python setup_smart_extraction.py
```
安装spaCy和其他NLP模型

### 4. 配置数据库
```bash
# MySQL (推荐)
python setup_mysql.py

# 或使用SQLite (默认)
# 无需额外配置
```

### 5. 运行完整流程
```bash
python main.py --full
```

### 6. 查看结果
```bash
# 查看统计信息
python main.py --stats

# 交互式数据浏览
python main.py --view

# 导出数据
python main.py --export data.csv
```

## 🔧 常用命令

### 基础操作
```bash
# 只运行爬虫
python main.py --scrape

# 只运行数据处理
python main.py --process

# 只运行标签分类
python main.py --label

# 测试Reddit API
python main.py --test-api
```

### 测试和验证
```bash
# 测试智能提取
python test_smart_extraction.py

# 测试Reddit API
python test_reddit_api.py

# 运行所有单元测试
python run_tests.py
```

## 📊 配置说明

### 核心配置 (config.yaml)
```yaml
# Reddit API设置
reddit_api:
  client_id: "your_client_id"
  client_secret: "your_client_secret"
  user_agent: "StudyAbroadScraper/1.0"

# 智能提取设置
smart_extraction:
  enabled: true
  methods: ["spacy", "keyword", "pattern"]

# 数据库设置
database:
  type: "mysql"  # 或 "sqlite"
  mysql:
    host: "localhost"
    database: "reddit_study_abroad"
    username: "root"
    password: "your_password"
```

## 🎯 预期结果

### 数据抓取
- 每个子版块100个帖子 (可配置)
- 自动去重和内容验证
- 结构化存储到数据库

### 智能提取
- **大学识别**: MIT, Stanford, Harvard等
- **专业识别**: Computer Science, Engineering等  
- **项目识别**: PhD, Master, Bachelor等

### 数据分析
- 申请难度评估
- 课程质量分析
- 情感倾向识别
- 统计报告生成

## 🔍 故障排除

### 常见问题

1. **Reddit API错误**
   ```bash
   python main.py --test-api
   ```
   检查API配置是否正确

2. **智能提取不工作**
   ```bash
   python test_smart_extraction.py
   ```
   确认模型是否正确安装

3. **数据库连接失败**
   ```bash
   python setup_mysql.py
   ```
   重新配置数据库连接

4. **没有数据被提取**
   - 检查子版块名称是否正确
   - 确认网络连接正常
   - 查看日志文件了解详细错误

### 性能优化

1. **提高抓取速度**
   - 减少延迟时间: `scraping.delay_min/max`
   - 增加并发数 (谨慎使用)

2. **提高提取准确性**
   - 启用更多提取方法
   - 添加自定义关键词
   - 使用LLM API (需要API密钥)

3. **减少内存使用**
   - 禁用语义相似度匹配
   - 使用SQLite而非MySQL
   - 减少批处理大小

## 📚 进阶使用

### 自定义关键词
在`config.yaml`中添加:
```yaml
keywords:
  universities:
    - "Your University"
  majors:
    - "Your Major"
  programs:
    - "Your Program"
```

### LLM API集成
```yaml
smart_extraction:
  llm:
    enabled: true
    provider: "openai"  # 或 "anthropic"
    api_key: "your_api_key"
```

### 数据导出
```bash
# CSV格式
python main.py --export data.csv

# JSON格式  
python main.py --export data.json

# 指定字段
python main.py --export data.csv --fields university,major,program
```

## 🎉 完成！

现在你已经成功设置了Reddit留学数据挖掘系统！

- 📊 查看数据: `python main.py --view`
- 📈 分析统计: `python main.py --stats`  
- 📁 导出结果: `python main.py --export`

如有问题，请查看详细文档或运行相应的测试脚本。
