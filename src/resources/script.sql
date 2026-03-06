-- Crear base de datos
DROP DATABASE music_db;
CREATE DATABASE IF NOT EXISTS music_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE music_db;

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice extra (opcional pero recomendado)
CREATE INDEX idx_username ON users(username);