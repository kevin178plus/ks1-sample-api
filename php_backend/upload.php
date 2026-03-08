<?php
/**
 * 文档上传接口
 * 接收 HTML 文件并保存到服务器
 */

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

// 配置
$config = [
    'upload_dir' => __DIR__ . '/documents/',
    'base_url' => 'http://your-server.com/documents/', // 替换为你的服务器地址
    'max_file_size' => 10 * 1024 * 1024, // 10MB
    'allowed_types' => ['text/html', 'application/xhtml+xml']
];

// 创建上传目录
if (!file_exists($config['upload_dir'])) {
    mkdir($config['upload_dir'], 0755, true);
}

// 检查请求方法
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    echo json_encode([
        'success' => false,
        'error' => '仅支持 POST 请求'
    ]);
    exit;
}

// 检查文件上传
if (!isset($_FILES['file'])) {
    echo json_encode([
        'success' => false,
        'error' => '未找到上传文件'
    ]);
    exit;
}

$file = $_FILES['file'];

// 验证文件
if ($file['error'] !== UPLOAD_ERR_OK) {
    echo json_encode([
        'success' => false,
        'error' => '文件上传错误: ' . $file['error']
    ]);
    exit;
}

// 验证文件大小
if ($file['size'] > $config['max_file_size']) {
    echo json_encode([
        'success' => false,
        'error' => '文件大小超过限制'
    ]);
    exit;
}

// 验证文件类型
$finfo = new finfo(FILEINFO_MIME_TYPE);
$mime_type = $finfo->file($file['tmp_name']);

if (!in_array($mime_type, $config['allowed_types'])) {
    echo json_encode([
        'success' => false,
        'error' => '不支持的文件类型: ' . $mime_type
    ]);
    exit;
}

// 获取文件信息
$title = isset($_POST['title']) ? $_POST['title'] : pathinfo($file['name'], PATHINFO_FILENAME);
$author = isset($_POST['author']) ? $_POST['author'] : 'openclaw';
$filename = $file['name'];
$file_path = $config['upload_dir'] . $filename;

// 检查文件是否已存在
if (file_exists($file_path)) {
    // 添加时间戳避免冲突
    $filename = pathinfo($filename, PATHINFO_FILENAME) . '_' . time() . '.html';
    $file_path = $config['upload_dir'] . $filename;
}

// 移动文件
if (!move_uploaded_file($file['tmp_name'], $file_path)) {
    echo json_encode([
        'success' => false,
        'error' => '文件保存失败'
    ]);
    exit;
}

// 生成访问链接
$url = $config['base_url'] . $filename;

// 保存元数据到数据库（可选）
save_metadata($filename, $title, $author, $file['size']);

// 返回成功响应
echo json_encode([
    'success' => true,
    'url' => $url,
    'filename' => $filename,
    'title' => $title,
    'author' => $author,
    'size' => $file['size'],
    'uploaded_at' => date('Y-m-d H:i:s')
]);

/**
 * 保存文档元数据到数据库
 */
function save_metadata($filename, $title, $author, $size) {
    try {
        $mysqli = new mysqli('localhost', 'root', '', 'documents_db');
        
        if ($mysqli->connect_error) {
            error_log('数据库连接失败: ' . $mysqli->connect_error);
            return false;
        }
        
        $stmt = $mysqli->prepare(
            "INSERT INTO documents (filename, title, author, size, uploaded_at) VALUES (?, ?, ?, ?, NOW())"
        );
        
        $stmt->bind_param('sssi', $filename, $title, $author, $size);
        $stmt->execute();
        $stmt->close();
        $mysqli->close();
        
        return true;
        
    } catch (Exception $e) {
        error_log('保存元数据失败: ' . $e->getMessage());
        return false;
    }
}
?>