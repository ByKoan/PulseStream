DROP DATABASE IF EXISTS music_db;
CREATE DATABASE IF NOT EXISTS music_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE music_db;

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin','user') NOT NULL DEFAULT 'user',
    total_songs INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_username ON users(username);

-- Tabla de canciones
CREATE TABLE IF NOT EXISTS songs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    uploaded_by VARCHAR(255) NOT NULL,
    plays INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(username) ON DELETE CASCADE
);

CREATE INDEX idx_song_uploaded_by ON songs(uploaded_by);
CREATE INDEX idx_song_title ON songs(title);

INSERT INTO users (username, password, role)
VALUES (
    'koan',
    'scrypt:32768:8:1$O4oe6AJ6beYNQbaQ$d7510787aa26d6acb9527839299b27490dfc88d6d925c5bb644479aeebaac6be231d9bd56bb1525411424e2e5ca6208aa8221a6db2678cfd6a87047e080cf9ca',
    'admin'
);