CREATE DATABASE solar_db CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

CREATE TABLE measurement (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    ts DATETIME NOT NULL,              -- 측정 시각 (필수)
    solar_v DECIMAL(6,2) NULL,         -- 태양광 전압 (V)
    solar_i DECIMAL(6,3) NULL,         -- 태양광 전류 (A)
    solar_p DECIMAL(7,2) NULL,         -- 전력(W) = V * I
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

TRUNCATE TABLE measurement;

DROP TABLE measurement;