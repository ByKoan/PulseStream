CREATE DATABASE IF NOT EXISTS music_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE music_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','user') NOT NULL DEFAULT 'user',
    total_songs INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username)
);

CREATE TABLE IF NOT EXISTS songs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    uploaded_by VARCHAR(255) NOT NULL,
    plays INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_song_uploaded_by (uploaded_by),
    INDEX idx_song_title (title),
    FOREIGN KEY (uploaded_by) REFERENCES users(username) ON DELETE CASCADE
);

INSERT IGNORE INTO users (username, password, role)
VALUES (
    'koan',
    'scrypt:32768:8:1$O4oe6AJ6beYNQbaQ$d7510787aa26d6acb9527839299b27490dfc88d6d925c5bb644479aeebaac6be231d9bd56bb1525411424e2e5ca6208aa8221a6db2678cfd6a87047e080cf9ca',
    'admin'
);