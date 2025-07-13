# MySQL数据库连接设置指南

本指南将帮助你配置MySQL数据库来存储和查看Reddit爬虫数据。

## 📋 前提条件

### 1. 安装MySQL服务器
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install mysql-server

# CentOS/RHEL
sudo yum install mysql-server

# macOS (使用Homebrew)
brew install mysql

# Windows
# 下载并安装MySQL Installer from https://dev.mysql.com/downloads/installer/
```

### 2. 启动MySQL服务
```bash
# Linux
sudo systemctl start mysql
sudo systemctl enable mysql

# macOS
brew services start mysql

# Windows
# 通过服务管理器启动MySQL服务
```

### 3. 安装Python依赖
```bash
pip install mysql-connector-python PyMySQL SQLAlchemy
```

## ⚙️ 配置步骤

### 1. 修改配置文件
编辑 `config.yaml` 文件，将数据库类型改为MySQL：

```yaml
# Database settings
database:
  # Database type: 'sqlite' or 'mysql'
  type: "mysql"
  
  # MySQL settings (used when type = 'mysql')
  mysql:
    host: "localhost"          # MySQL服务器地址
    port: 3306                 # MySQL端口
    database: "reddit_study_abroad"  # 数据库名称
    username: "root"    # 用户名
    password: "668818"  # 密码
    charset: "utf8mb4"         # 字符集
    autocommit: true
```

### 2. 运行数据库设置脚本
```bash
python setup_mysql.py
```

这个脚本会：
- 创建数据库 `reddit_study_abroad`
- 创建用户并分配权限
- 测试数据库连接
- 创建必要的数据表

### 3. 验证设置
```bash
# 查看数据库统计
python main.py --stats

# 启动交互式数据查看器
python main.py --view
```

## 🔍 数据查看方法

### 1. 命令行统计
```bash
# 显示基本统计信息
python main.py --stats
```

### 2. 交互式数据查看器
```bash
# 启动交互式查看器
python main.py --view
```

交互式查看器提供以下功能：
- 📊 基本统计信息
- 📝 查看最新帖子
- 🏫 按大学搜索
- 🔍 关键词搜索
- 😊 情感分析统计
- 📈 申请难度分析
- 📄 导出CSV数据
- 🏆 大学排名

### 3. 直接SQL查询
你也可以直接连接MySQL数据库进行查询：

```bash
# 连接到MySQL
mysql -u reddit_user -p reddit_study_abroad

# 或使用MySQL Workbench等图形化工具
```

### 4. 常用SQL查询示例

```sql
-- 查看所有表
SHOW TABLES;

-- 查看posts表结构
DESCRIBE posts;

-- 查看总帖子数
SELECT COUNT(*) FROM posts;

-- 按子版块统计
SELECT subreddit, COUNT(*) as count 
FROM posts 
GROUP BY subreddit 
ORDER BY count DESC;

-- 查看情感分析结果
SELECT sentiment_label, COUNT(*) as count, AVG(sentiment_score) as avg_score
FROM posts 
WHERE sentiment_label IS NOT NULL
GROUP BY sentiment_label;

-- 查看大学提及排名
SELECT university_name, COUNT(*) as mentions, AVG(sentiment_score) as avg_sentiment
FROM posts 
WHERE university_name IS NOT NULL AND university_name != ''
GROUP BY university_name
HAVING mentions >= 3
ORDER BY avg_sentiment DESC, mentions DESC;

-- 搜索特定关键词
SELECT post_id, subreddit, question_title, sentiment_score
FROM posts 
WHERE question_title LIKE '%MIT%' OR answer_content_cleaned LIKE '%MIT%'
ORDER BY sentiment_score DESC;

-- 查看申请难度分布
SELECT difficulty_label, COUNT(*) as count
FROM posts 
WHERE difficulty_label IS NOT NULL
GROUP BY difficulty_label
ORDER BY 
    CASE difficulty_label 
        WHEN '极难' THEN 1 
        WHEN '难' THEN 2 
        WHEN '中等' THEN 3 
        WHEN '易' THEN 4 
    END;
```

## 📊 数据导出

### 1. 导出为CSV
```bash
# 导出所有数据
python main.py --export reddit_data.csv

# 或在交互式查看器中选择导出选项
python main.py --view
```

### 2. 使用pandas进行分析
```python
import pandas as pd
import mysql.connector

# 连接数据库
conn = mysql.connector.connect(
    host='localhost',
    database='reddit_study_abroad',
    user='reddit_user',
    password='your_password'
)

# 读取数据到DataFrame
df = pd.read_sql('SELECT * FROM posts', conn)

# 进行数据分析
print(df.describe())
print(df['sentiment_label'].value_counts())

conn.close()
```

## 🔧 高级配置

### 1. 性能优化
```sql
-- 添加更多索引以提高查询性能
CREATE INDEX idx_sentiment_score ON posts(sentiment_score);
CREATE INDEX idx_created_at ON posts(created_at);
CREATE INDEX idx_university_sentiment ON posts(university_name, sentiment_score);
```

### 2. 数据备份
```bash
# 备份数据库
mysqldump -u reddit_user -p reddit_study_abroad > backup.sql

# 恢复数据库
mysql -u reddit_user -p reddit_study_abroad < backup.sql
```

### 3. 远程连接配置
如果需要从其他机器连接MySQL：

```sql
-- 创建远程用户
CREATE USER 'reddit_user'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON reddit_study_abroad.* TO 'reddit_user'@'%';
FLUSH PRIVILEGES;
```

修改MySQL配置文件 `/etc/mysql/mysql.conf.d/mysqld.cnf`：
```ini
bind-address = 0.0.0.0
```

## 🚨 故障排除

### 常见问题及解决方案

1. **连接被拒绝**
   ```bash
   # 检查MySQL服务状态
   sudo systemctl status mysql
   
   # 重启MySQL服务
   sudo systemctl restart mysql
   ```

2. **权限错误**
   ```sql
   -- 重新授权
   GRANT ALL PRIVILEGES ON reddit_study_abroad.* TO 'reddit_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **字符编码问题**
   ```sql
   -- 检查数据库字符集
   SHOW CREATE DATABASE reddit_study_abroad;
   
   -- 修改字符集
   ALTER DATABASE reddit_study_abroad CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

4. **端口被占用**
   ```bash
   # 检查端口使用情况
   netstat -tlnp | grep :3306
   
   # 修改MySQL端口（在my.cnf中）
   port = 3307
   ```

## 📈 监控和维护

### 1. 查看数据库状态
```sql
SHOW STATUS LIKE 'Connections';
SHOW STATUS LIKE 'Uptime';
SHOW PROCESSLIST;
```

### 2. 优化查询
```sql
-- 分析慢查询
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';

-- 查看表大小
SELECT 
    table_name AS 'Table',
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.tables 
WHERE table_schema = 'reddit_study_abroad';
```

现在你可以使用MySQL数据库来存储和分析Reddit爬虫数据了！🎉
