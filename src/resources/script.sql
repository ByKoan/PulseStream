DROP DATABASE music_db;
CREATE DATABASE IF NOT EXISTS music_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE music_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','user') NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE INDEX idx_username ON users(username);