# 项目结构说明

## 📁 核心文件结构

```
reddit-scraper/
├── 📄 main.py                    # 主程序入口
├── 📄 config.yaml               # 配置文件
├── 📄 requirements.txt          # Python依赖
├── 📄 setup_reddit_api.py       # Reddit API设置向导
├── 📄 test_reddit_api.py        # API功能测试
├── 📄 README.md                 # 项目说明
│
├── 📁 src/                      # 核心源代码
│   ├── 📄 scraper.py           # 主爬虫模块 (Reddit API)
│   ├── 📄 reddit_api_scraper.py # Reddit API具体实现
│   ├── 📄 data_processor.py    # 数据处理模块
│   ├── 📄 labeling_system.py   # 智能标签系统
│   ├── 📄 database_manager.py  # 数据库管理
│   ├── 📄 data_viewer.py       # 数据查看器
│   └── 📄 utils.py             # 工具函数
│
├── 📁 tests/                   # 单元测试
│   ├── 📄 test_scraper.py      # 爬虫测试
│   ├── 📄 test_data_processor.py # 数据处理测试
│   └── 📄 test_labeling_system.py # 标签系统测试
│
├── 📁 examples/                # 使用示例
│   └── 📄 usage_example.py     # 详细使用示例
│
├── 📄 setup_mysql.py           # MySQL数据库设置
├── 📄 MYSQL_SETUP.md           # MySQL设置指南
└── 📄 run_tests.py             # 测试运行器
```

## 🔧 核心模块说明

### 1. **主程序 (main.py)**
- 统一的命令行界面
- 支持完整流程或单独模块运行
- 数据查看和导出功能

### 2. **Reddit API爬虫 (src/reddit_api_scraper.py)**
- 使用PRAW库访问Reddit API
- 稳定可靠的数据获取
- 自动处理速率限制
- 支持多种数据获取模式

### 3. **数据处理 (src/data_processor.py)**
- 文本清洗和标准化
- 实体提取 (大学、专业、项目)
- 智能去重算法
- 关键内容提取

### 4. **标签系统 (src/labeling_system.py)**
- 申请难度分类
- 课程评价分析
- 情感倾向识别
- 置信度评估

### 5. **数据库管理 (src/database_manager.py)**
- 支持SQLite和MySQL
- 统一的数据库操作接口
- 自动表结构管理
- 连接池和事务处理

### 6. **数据查看器 (src/data_viewer.py)**
- 交互式数据浏览
- 多维度统计分析
- CSV导出功能
- 大学排名分析

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 设置Reddit API
```bash
python setup_reddit_api.py
```

### 3. 运行爬虫
```bash
python main.py --full
```

### 4. 查看数据
```bash
python main.py --view
```

## 📊 数据流程

```
Reddit API → 原始数据 → 数据清洗 → 实体提取 → 智能标签 → 数据库存储
     ↓           ↓          ↓          ↓          ↓          ↓
   PRAW库    JSON格式   文本处理   NLP分析   分类算法   MySQL/SQLite
```

## 🔍 主要功能

### 数据获取
- ✅ Reddit API集成
- ✅ 多子版块支持
- ✅ 自动去重
- ✅ 错误处理

### 数据处理
- ✅ 文本清洗
- ✅ 实体识别
- ✅ 内容摘要
- ✅ 质量过滤

### 智能分析
- ✅ 申请难度评估
- ✅ 课程质量分析
- ✅ 情感倾向识别
- ✅ 置信度评分

### 数据管理
- ✅ 双数据库支持
- ✅ 交互式查看
- ✅ 数据导出
- ✅ 统计分析

## 🧪 测试

```bash
# 运行所有测试
python run_tests.py

# 测试Reddit API
python test_reddit_api.py

# 测试特定模块
python -m pytest tests/test_scraper.py -v
```

## 📝 配置说明

主要配置项：
- `subreddits`: 目标子版块列表
- `reddit_api`: API凭据配置
- `scraping`: 爬取参数设置
- `database`: 数据库连接配置
- `processing`: 数据处理参数
- `labeling`: 标签系统配置

## 🔧 扩展性

项目采用模块化设计，易于扩展：
- 新增数据源：实现新的scraper类
- 新增分析功能：扩展labeling_system
- 新增数据库：扩展database_manager
- 新增可视化：扩展data_viewer

## 📚 依赖说明

### 核心依赖
- `praw`: Reddit API客户端
- `requests`: HTTP请求库
- `pandas`: 数据处理
- `mysql-connector-python`: MySQL连接

### NLP依赖
- `spacy`: 自然语言处理
- `nltk`: 文本分析工具
- `textblob`: 情感分析

### 可选依赖
- `transformers`: 深度学习模型
- `torch`: PyTorch框架
- `keybert`: 关键词提取

