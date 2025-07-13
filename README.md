# Reddit Study Abroad Data Scraper

**Reddit 留学数据挖掘与处理**

这是一个完整的Reddit爬虫系统，专门用于抓取和分析留学相关的讨论数据。项目实现了从数据抓取到智能标签化的完整流程。

## 项目概述

本项目实现了技术文档中描述的三个核心部分：

1. **Part 1: 爬虫流程设计与实现** - 从Reddit抓取留学相关讨论数据
2. **Part 2: 结构化数据处理策略** - 数据清洗、去重和结构化处理
3. **Part 3: 标签化策略设计** - 自动化内容分类和情感分析

## 功能特性

### 🕷️ Reddit API爬虫系统
- **Reddit API**: 稳定、快速、无IP限制的官方API接口
- 支持多个留学相关子版块 (r/ApplyingToCollege, r/gradadmissions, r/studyabroad等)
- 智能延迟和速率限制处理
- 自动去重和内容验证
- 结构化数据获取

### 🧹 数据处理引擎
- 高级文本清洗和标准化
- 实体提取：大学名称、专业、项目类型
- 智能去重：基于内容相似度的模糊去重
- 多语言检测和过滤
- 关键内容提取和摘要生成

### 🏷️ 智能标签系统
- **申请难度分类**：极难/难/中等/易
- **课程评价分类**：优秀/良好/一般/差
- **情感倾向分析**：积极/消极/中性 (含0-10评分)
- 基于关键词匹配和上下文分析
- 置信度评估和阈值过滤

## 安装和设置

### 环境要求
- Python 3.8+
- SQLite3 (内置) 或 MySQL 5.7+

### 安装依赖
```bash
pip install -r requirements.txt
```

### Reddit API设置
```bash
# 1. 运行API设置向导
python setup_reddit_api.py

# 2. 测试API连接
python main.py --test-api
```

### 配置设置
主要配置项在 `config.yaml` 文件中：

```yaml
# 目标子版块
subreddits:
  - "ApplyingToCollege"
  - "gradadmissions"
  - "studyabroad"

# Reddit API设置
reddit_api:
  client_id: "your_client_id"
  client_secret: "your_client_secret"
  user_agent: "StudyAbroadScraper/1.0"

# 爬虫设置
scraping:
  max_posts_per_subreddit: 100
  max_comments_per_post: 50
```

## 使用方法

### 命令行界面

```bash
# 运行完整流程 (推荐)
python main.py --full

# 只运行爬虫
python main.py --scrape

# 只运行数据处理
python main.py --process

# 只运行标签化
python main.py --label

# 查看数据统计
python main.py --stats

# 使用自定义配置
python main.py --config custom.yaml --full
```

### 编程接口

```python
from src.scraper import RedditScraper
from src.data_processor import DataProcessor
from src.labeling_system import LabelingSystem

# 1. 数据抓取
scraper = RedditScraper("config.yaml")
results = scraper.run_scraper()
scraper.close()

# 2. 数据处理
processor = DataProcessor("config.yaml")
processor.process_all_posts()
processor.remove_invalid_data()

# 3. 标签化
labeler = LabelingSystem("config.yaml")
labeler.label_all_posts()
stats = labeler.get_labeling_stats()
```

## 数据库结构

项目使用SQLite数据库存储数据，主要表结构：

```sql
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id TEXT UNIQUE,
    subreddit TEXT,
    question_title TEXT,
    answer_content_raw TEXT,
    answer_content_cleaned TEXT,
    university_name TEXT,
    major_name TEXT,
    program_name TEXT,
    key_content TEXT,
    content_hash TEXT,
    difficulty_label TEXT,
    course_evaluation_label TEXT,
    sentiment_label TEXT,
    sentiment_score REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);
```

## 测试

运行单元测试：

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定模块测试
python -m pytest tests/test_scraper.py -v
python -m pytest tests/test_data_processor.py -v
python -m pytest tests/test_labeling_system.py -v

# 生成覆盖率报告
python -m pytest tests/ --cov=src --cov-report=html
```

## 项目结构

```
reddit-scraper/
├── src/                    # 源代码
│   ├── __init__.py
│   ├── scraper.py         # 爬虫模块
│   ├── data_processor.py  # 数据处理模块
│   ├── labeling_system.py # 标签系统模块
│   └── utils.py           # 工具函数
├── tests/                 # 测试文件
│   ├── test_scraper.py
│   ├── test_data_processor.py
│   └── test_labeling_system.py
├── main.py               # 主程序入口
├── config.yaml           # 配置文件
├── requirements.txt      # 依赖列表
└── README.md            # 项目文档
```

## 技术实现亮点

### 1. 反爬虫策略
- 随机User-Agent轮换
- 智能请求延迟 (1-3秒随机)
- 异常处理和重试机制
- 支持代理IP池扩展

### 2. 数据质量保证
- 多层次文本清洗
- 基于相似度的智能去重
- 实体识别和标准化
- 内容有效性验证

### 3. 智能标签系统
- 多维度分类 (难度/评价/情感)
- 上下文感知的关键词匹配
- 置信度评估和阈值过滤
- 否定句处理和情感强度分析

## 性能和扩展性

- **处理能力**：支持数千条帖子的批量处理
- **存储效率**：SQLite数据库，支持索引优化
- **模块化设计**：各组件独立，易于扩展
- **配置驱动**：通过YAML文件灵活配置

## 注意事项

1. **合规使用**：请遵守Reddit的使用条款和robots.txt
2. **速率限制**：建议设置合理的请求延迟，避免IP被封
3. **数据备份**：重要数据请及时备份
4. **网络环境**：某些地区可能需要代理访问Reddit

## 未来改进方向

1. **深度学习集成**：使用BERT/GPT等模型提升标签准确性
2. **实时监控**：添加数据质量监控和异常告警
3. **可视化界面**：开发Web界面用于数据查看和管理
4. **分布式处理**：支持多进程/多机器并行处理
5. **API接口**：提供RESTful API供其他系统调用

