# Reddit 留学数据挖掘系统

基于Reddit API的留学数据采集、处理和分析系统。

## 技术架构

### 数据采集模块
- Reddit API (PRAW库)
- 多子版块数据获取
- 自动去重和验证

### 数据处理模块
- 多模型实体提取 (spaCy NER + 关键词匹配 + 模式识别)
- 大学、专业、项目类型识别
- 文本清洗和标准化
- 内容摘要生成

### 智能标签模块
- 申请难度分析 (极难/难/中等/易)
- 课程质量评价 (优秀/良好/一般/差)
- 情感倾向分析 (积极/消极/中性)
- 多模型融合 (规则+机器学习+深度学习)

### 数据存储模块
- MySQL / SQLite 双数据库支持
- 自动表结构管理
- 连接池和事务处理

## 技术实现

### 爬虫系统
- Reddit API (PRAW)
- 支持子版块: ApplyingToCollege, gradadmissions, studyabroad等
- 速率限制处理
- 数据去重验证

### 数据处理
- spaCy NER实体识别
- 关键词匹配算法
- 正则表达式模式匹配
- 文本清洗和标准化
- 相似度去重

### 标签分类
- 申请难度: 极难/难/中等/易
- 课程评价: 优秀/良好/一般/差
- 情感分析: 积极/消极/中性 (0-10评分)
- 多模型融合: Pattern + TextBlob + VADER + Transformers

## 安装配置

### 环境要求
- Python 3.8+
- MySQL 5.7+ / SQLite3

### 安装依赖
```bash
pip install -r requirements.txt
```

### Reddit API配置
```bash
python setup_reddit_api.py
```

### 配置文件 (config.yaml)
```yaml
subreddits:
  - "ApplyingToCollege"
  - "gradadmissions"
  - "studyabroad"

reddit_api:
  client_id: "your_client_id"
  client_secret: "your_client_secret"
  user_agent: "StudyAbroadScraper/1.0"

smart_labeling:
  enabled: true
  methods: ["pattern", "textblob", "vader", "transformers"]
```

## 使用方法

### 命令行接口

```bash
# 完整流程
python main.py --full

# 分步执行
python main.py --scrape    # 数据抓取
python main.py --process   # 数据处理
python main.py --label     # 标签分类

# 查看结果
python main.py --stats     # 统计信息
python main.py --view      # 数据查看
python main.py --export data.csv  # 导出数据
```

## 数据库结构

```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    post_id VARCHAR(20) UNIQUE,
    subreddit VARCHAR(50),
    question_title TEXT,
    answer_content_raw TEXT,
    answer_content_cleaned TEXT,
    university_name VARCHAR(200),
    major_name VARCHAR(200),
    program_name VARCHAR(100),
    key_content TEXT,
    difficulty_label VARCHAR(20),
    course_evaluation_label VARCHAR(20),
    sentiment_label VARCHAR(20),
    sentiment_score FLOAT,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 技术栈

- Python 3.8+
- PRAW (Reddit API)
- spaCy (NLP)
- TextBlob, VADER (情感分析)
- Transformers (深度学习)
- MySQL / SQLite (数据库)
- pandas (数据处理)

## 项目结构

```
reddit-scraper/
├── main.py                    # 主程序入口
├── config.yaml               # 配置文件
├── requirements.txt          # 依赖列表
├── src/                      # 源代码
│   ├── scraper.py           # 爬虫模块
│   ├── reddit_api_scraper.py # API实现
│   ├── smart_entity_extractor.py # 实体提取
│   ├── data_processor.py    # 数据处理
│   ├── smart_labeling_analyzer.py # 智能标签
│   ├── labeling_system.py   # 标签系统
│   ├── database_manager.py  # 数据库管理
│   ├── data_viewer.py       # 数据查看
│   └── utils.py             # 工具函数
├── tests/                   # 单元测试
├── examples/                # 使用示例
└── setup_reddit_api.py     # API设置
```

