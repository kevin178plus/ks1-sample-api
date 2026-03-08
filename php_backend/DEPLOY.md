# 文档生成系统部署指南

## 系统要求

- 操作系统: Windows Server 2012
- PHP: 7.4+
- MySQL: 5.7+
- Nginx: 1.15+
- Python: 3.7+ (用于运行文档生成脚本)

## 部署步骤

### 1. 部署 PHP 后端

#### 1.1 上传文件

将以下文件上传到服务器:
```
/var/www/html/
├── api/
│   └── upload.php
└── documents/
    (自动创建)
```

#### 1.2 创建数据库

```bash
# 登录 MySQL
mysql -u root -p

# 执行初始化脚本
source /path/to/init_database.sql
```

#### 1.3 配置权限

```bash
# 设置目录权限
chmod 755 /var/www/html/api
chmod 777 /var/www/html/documents
chown -R www-data:www-data /var/www/html
```

#### 1.4 配置 Nginx

```bash
# 复制配置文件
cp nginx.conf /etc/nginx/sites-available/documents

# 创建软链接
ln -s /etc/nginx/sites-available/documents /etc/nginx/sites-enabled/

# 测试配置
nginx -t

# 重启 Nginx
service nginx restart
```

#### 1.5 修改配置

编辑 `upload.php`，修改以下配置:
```php
$config = [
    'upload_dir' => '/var/www/html/documents/',
    'base_url' => 'http://your-server.com/documents/',
    'max_file_size' => 10 * 1024 * 1024,
    'allowed_types' => ['text/html', 'application/xhtml+xml']
];
```

编辑数据库连接:
```php
$mysqli = new mysqli('localhost', 'root', 'your_password', 'documents_db');
```

### 2. 配置 Python 脚本

#### 2.1 安装依赖

```bash
pip install requests
```

#### 2.2 配置 API 地址

编辑 `doc_generator.py`，修改:
```python
PHP_API_URL = "http://your-server.com/api"
```

### 3. 测试部署

#### 3.1 测试 PHP 后端

```bash
curl -X POST http://your-server.com/api/upload.php \
  -F "file=@test.html" \
  -F "title=测试文档" \
  -F "author=openclaw"
```

#### 3.2 测试 Python 脚本

```bash
python doc_generator.py
```

### 4. 使用方法

#### 4.1 在 Python 中使用

```python
from doc_generator import DocGenerator

# 创建生成器
generator = DocGenerator("http://your-server.com/api")

# 生成并上传文档
result = generator.upload_and_get_link(
    title="我的文档",
    content="# 标题\n\n内容...",
    author="openclaw"
)

if result['success']:
    print(f"访问链接: {result['url']}")
```

#### 4.2 命令行使用

```bash
python doc_generator.py
```

## 文件结构

```
服务器端 (yun11):
/var/www/html/
├── api/
│   └── upload.php          # 上传接口
├── documents/              # 文档存储目录
│   └── *.html             # 生成的 HTML 文档
└── index.php              # 可选：文档列表页面

客户端 (本机):
doc_generator.py            # 文档生成脚本
```

## 安全建议

1. **文件验证**: 严格验证上传文件的类型和内容
2. **访问控制**: 添加身份验证和授权
3. **HTTPS**: 使用 SSL/TLS 加密传输
4. **文件名安全**: 对文件名进行安全处理
5. **访问日志**: 记录所有上传和访问行为
6. **定期清理**: 定期清理过期文档

## 故障排查

### 上传失败

1. 检查 PHP 错误日志: `/var/log/nginx/documents_error.log`
2. 检查文件权限: `ls -la /var/www/html/documents/`
3. 检查数据库连接: 确认 MySQL 用户名和密码

### 无法访问文档

1. 检查 Nginx 配置: `nginx -t`
2. 检查文件是否存在: `ls -la /var/www/html/documents/`
3. 检查目录权限: `chmod 755 /var/www/html/documents`

### 数据库错误

1. 检查数据库是否创建: `SHOW DATABASES;`
2. 检查表是否创建: `USE documents_db; SHOW TABLES;`
3. 检查数据库权限: `GRANT ALL PRIVILEGES ON documents_db.* TO 'user'@'localhost';`

## 维护

### 定期清理过期文档

```sql
-- 删除 30 天前的文档
DELETE FROM documents 
WHERE uploaded_at < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- 物理删除文件
find /var/www/html/documents/ -name "*.html" -mtime +30 -delete
```

### 监控磁盘空间

```bash
df -h
du -sh /var/www/html/documents/
```

## 性能优化

1. **启用 Gzip**: 已在 Nginx 配置中启用
2. **缓存静态文件**: 配置浏览器缓存
3. **CDN 加速**: 使用 CDN 分发文档
4. **数据库索引**: 已在初始化脚本中创建

## 联系支持

如有问题，请检查:
- PHP 错误日志: `/var/log/nginx/documents_error.log`
- Nginx 访问日志: `/var/log/nginx/documents_access.log`
- MySQL 慢查询日志: `/var/log/mysql/slow.log`