#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文档生成器 - 生成带链接的 HTML 文档
通过 PHP 后端上传并获取访问链接
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path

class DocGenerator:
    """文档生成器"""
    
    def __init__(self, php_api_url):
        """
        初始化文档生成器
        
        Args:
            php_api_url: PHP 后端 API 地址，例如：http://your-server.com/api/upload.php
        """
        self.php_api_url = php_api_url.rstrip('/')
        
    def generate_html(self, title, content, author="openclaw"):
        """
        生成 HTML 文档
        
        Args:
            title: 文档标题
            content: 文档内容（支持 Markdown）
            author: 作者
            
        Returns:
            str: HTML 内容
        """
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .header {{
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            color: #2c3e50;
            font-size: 2em;
            margin-bottom: 10px;
        }}
        
        .meta {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        
        .content {{
            color: #34495e;
            line-height: 1.8;
        }}
        
        .content h1, .content h2, .content h3 {{
            color: #2c3e50;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        
        .content h1 {{ font-size: 1.8em; }}
        .content h2 {{ font-size: 1.5em; }}
        .content h3 {{ font-size: 1.3em; }}
        
        .content p {{
            margin-bottom: 15px;
        }}
        
        .content ul, .content ol {{
            margin-left: 30px;
            margin-bottom: 15px;
        }}
        
        .content li {{
            margin-bottom: 8px;
        }}
        
        .content code {{
            background: #f8f9fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "Courier New", monospace;
            color: #e74c3c;
        }}
        
        .content pre {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            overflow-x: auto;
            margin-bottom: 20px;
        }}
        
        .content pre code {{
            background: none;
            color: inherit;
            padding: 0;
        }}
        
        .content blockquote {{
            border-left: 4px solid #4CAF50;
            padding-left: 20px;
            margin: 20px 0;
            color: #7f8c8d;
            font-style: italic;
        }}
        
        .content table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        
        .content th, .content td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        
        .content th {{
            background: #4CAF50;
            color: white;
        }}
        
        .content tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #7f8c8d;
            font-size: 0.9em;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <div class="meta">
                作者: {author} | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </div>
        
        <div class="content">
            {self._markdown_to_html(content)}
        </div>
        
        <div class="footer">
            <p>本文档由 openclaw 文档生成器自动生成</p>
        </div>
    </div>
</body>
</html>"""
        return html
    
    def _markdown_to_html(self, markdown):
        """
        简单的 Markdown 转 HTML
        
        Args:
            markdown: Markdown 文本
            
        Returns:
            str: HTML 文本
        """
        html = markdown
        
        # 标题
        html = html.replace('### ', '<h3>').replace('\n### ', '</h3>\n<h3>')
        html = html.replace('## ', '<h2>').replace('\n## ', '</h2>\n<h2>')
        html = html.replace('# ', '<h1>').replace('\n# ', '</h1>\n<h1>')
        html = html.replace('\n<h1>', '\n<h1>')
        
        # 代码块
        lines = html.split('\n')
        in_code_block = False
        result = []
        
        for line in lines:
            if line.strip().startswith('```'):
                if not in_code_block:
                    result.append('<pre><code>')
                    in_code_block = True
                else:
                    result.append('</code></pre>')
                    in_code_block = False
            elif in_code_block:
                result.append(line)
            else:
                # 行内代码
                line = line.replace('`', '<code>').replace('`', '</code>')
                # 加粗
                line = line.replace('**', '<strong>').replace('**', '</strong>')
                # 链接
                import re
                line = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', line)
                result.append(line)
        
        html = '\n'.join(result)
        
        # 段落
        paragraphs = html.split('\n\n')
        html = '\n\n'.join(f'<p>{p.strip()}</p>' if p.strip() and not p.strip().startswith('<') else p.strip() for p in paragraphs)
        
        return html
    
    def upload_and_get_link(self, title, content, author="openclaw"):
        """
        生成 HTML 并上传到服务器，获取访问链接
        
        Args:
            title: 文档标题
            content: 文档内容（支持 Markdown）
            author: 作者
            
        Returns:
            dict: 包含访问链接的信息
        """
        # 生成 HTML
        html_content = self.generate_html(title, content, author)
        
        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{title.replace(' ', '_')}.html"
        
        # 上传到 PHP 后端
        try:
            files = {
                'file': (filename, html_content, 'text/html')
            }
            
            data = {
                'title': title,
                'author': author
            }
            
            response = requests.post(
                f"{self.php_api_url}/upload.php",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return {
                        'success': True,
                        'url': result.get('url'),
                        'filename': filename,
                        'message': '文档上传成功'
                    }
                else:
                    return {
                        'success': False,
                        'error': result.get('error', '上传失败')
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP 错误: {response.status_code}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


def main():
    """主函数 - 示例用法"""
    
    # 配置 PHP 后端地址
    PHP_API_URL = "http://your-server.com/api"  # 替换为你的服务器地址
    
    # 创建文档生成器
    generator = DocGenerator(PHP_API_URL)
    
    # 示例：生成文档
    title = "飞书文件查看优化方案"
    content = """## 背景

用户在和 openclaw（ai agent）通过飞书的对话过程中，发现查看文件不方便。

## 解决方案

通过生成 HTML 文档并上传到服务器，提供便捷的访问链接。

### 优势

1. **快速访问**：点击链接即可查看
2. **格式美观**：支持 Markdown 格式
3. **持久存储**：文档保存在服务器
4. **易于分享**：可以分享链接给他人

## 使用方法

1. Python 脚本生成 HTML 文档
2. 上传到 PHP 后端
3. 获取访问链接
4. 点击链接查看文档

## 技术栈

- **Python**: 文档生成和上传
- **PHP**: 文件接收和存储
- **MySQL**: 文档元数据存储
- **Nginx**: Web 服务器

"""
    
    # 上传并获取链接
    result = generator.upload_and_get_link(title, content)
    
    if result['success']:
        print(f"✅ 文档上传成功！")
        print(f"📄 访问链接: {result['url']}")
        print(f"📁 文件名: {result['filename']}")
    else:
        print(f"❌ 上传失败: {result['error']}")


if __name__ == "__main__":
    main()