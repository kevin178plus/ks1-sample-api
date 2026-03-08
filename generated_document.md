### 开发计划

#### 目标
在yun11服务器上部署一个简单的文档查看系统，用户可以通过浏览器访问生成的HTML文档。

#### 技术方案
1. **Python脚本**：用于处理文件，生成HTML文档。
2. **PHP脚本**：用于提供文件上传和文档查看功能。

#### 实现步骤

1. **Python脚本**：
   - 处理文件，生成HTML文档。
   - 将HTML文档保存到指定目录。

2. **PHP脚本**：
   - 提供文件上传功能。
   - 提供文档查看功能。

### Python脚本

```python
import os
import shutil
from jinja2 import Template

def generate_html(file_path, output_dir):
    # 读取文件内容
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 定义HTML模板
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ title }}</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: #f4f4f4;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background-color: #fff;
                padding: 20px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
            pre {
                background-color: #f4f4f4;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{{ title }}</h1>
            <pre>{{ content }}</pre>
        </div>
    </body>
    </html>
    """

    # 渲染HTML模板
    template = Template(html_template)
    html_content = template.render(title=os.path.basename(file_path), content=content)

    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 保存HTML文件
    output_file = os.path.join(output_dir, os.path.basename(file_path) + '.html')
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(html_content)

    return output_file

if __name__ == "__main__":
    file_path = input("请输入要转换的文件路径: ")
    output_dir = input("请输入输出目录: ")
    generate_html(file_path, output_dir)
    print(f"HTML文档已生成: {output_dir}")
```

### PHP脚本

```php
<?php
// 定义上传目录
$upload_dir = 'uploads/';
$html_dir = 'html/';

// 确保上传目录存在
if (!file_exists($upload_dir)) {
    mkdir($upload_dir, 0777, true);
}

// 确保HTML目录存在
if (!file_exists($html_dir)) {
    mkdir($html_dir, 0777, true);
}

// 处理文件上传
if ($_SERVER['REQUEST_METHOD'] == 'POST' && isset($_FILES['file'])) {
    $file = $_FILES['file'];
    $file_name = basename($file['name']);
    $file_path = $upload_dir . $file_name;

    if (move_uploaded_file($file['tmp_name'], $file_path)) {
        // 调用Python脚本生成HTML文档
        $output_file = $html_dir . $file_name . '.html';
        $command = "python generate_html.py " . escapeshellarg($file_path) . " " . escapeshellarg($html_dir);
        shell_exec($command);

        // 返回HTML文档链接
        echo "<p>文件已上传，HTML文档已生成: <a href='" . $output_file . "'>" . $output_file . "</a></p>";
    } else {
        echo "<p>文件上传失败</p>";
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>文档查看系统</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: #fff;
            padding: 20px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }
        form {
            margin-bottom: 20px;
        }
        input[type="file"] {
            margin-bottom: 10px;
        }
        input[type="submit"] {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>文档查看系统</h1>
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <input type="submit" value="上传文件">
        </form>
    </div>
</body>
</html>
```

### 部署步骤

1. **Python脚本**：
   - 将Python脚本保存为`generate_html.py`。
   - 确保Python环境中安装了`jinja2`库。

2. **PHP脚本**：
   - 将PHP脚本保存为`index.php`。
   - 将`index.php`放置在Nginx的网站根目录下。

3. **配置Nginx**：
   - 确保Nginx配置正确，可以访问PHP脚本。

4. **访问系统**：
   - 通过浏览器访问PHP脚本，上传文件并查看生成的HTML文档。

### 注意事项

1. 确保服务器上安装了Python和PHP环境。
2. 确保Nginx配置正确，可以处理PHP脚本。
3. 确保Python脚本有权限执行和访问上传目录和HTML目录。
4. 确保PHP脚本有权限执行和访问上传目录和HTML目录。

通过以上步骤，用户可以在yun11服务器上部署一个简单的文档查看系统，方便查看和管理文件。