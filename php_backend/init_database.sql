-- 创建数据库
CREATE DATABASE IF NOT EXISTS documents_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE documents_db;

-- 创建文档表
CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    filename VARCHAR(255) NOT NULL UNIQUE,
    title VARCHAR(500) NOT NULL,
    author VARCHAR(100) NOT NULL,
    size BIGINT NOT NULL,
    upload_count INT DEFAULT 0,
    last_accessed_at DATETIME,
    uploaded_at DATETIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_filename (filename),
    INDEX idx_author (author),
    INDEX idx_uploaded_at (uploaded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建访问日志表（可选）
CREATE TABLE IF NOT EXISTS access_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    document_id INT NOT NULL,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    accessed_at DATETIME NOT NULL,
    INDEX idx_document_id (document_id),
    INDEX idx_accessed_at (accessed_at),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建文档统计视图
CREATE OR REPLACE VIEW document_stats AS
SELECT 
    d.id,
    d.filename,
    d.title,
    d.author,
    d.size,
    d.upload_count,
    d.uploaded_at,
    d.last_accessed_at,
    COUNT(al.id) as total_access_count
FROM documents d
LEFT JOIN access_logs al ON d.id = al.document_id
GROUP BY d.id;

-- 插入示例数据（可选）
-- INSERT INTO documents (filename, title, author, size, uploaded_at)
-- VALUES ('example.html', '示例文档', 'openclaw', 1024, NOW());