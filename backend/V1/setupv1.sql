DROP DATABASE IF EXISTS MEDV1;
CREATE DATABASE IF NOT EXISTS MEDV1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE MEDV1;

-- Création de la table des stations
CREATE TABLE IF NOT EXISTS stations (
    station_id INT PRIMARY KEY,
    station_nom VARCHAR(100) NOT NULL,
    station_ligne VARCHAR(20) NOT NULL,
    station_est_terminus BOOLEAN NOT NULL,
    station_branchement INT NOT NULL
);

-- Création de la table des connexions
CREATE TABLE IF NOT EXISTS connexions (
    station1_id INT,
    station2_id INT,
    temps_en_secondes INT,
    PRIMARY KEY (station1_id, station2_id),
    FOREIGN KEY (station1_id) REFERENCES stations(station_id),
    FOREIGN KEY (station2_id) REFERENCES stations(station_id)
);

-- Création de la table des positions
CREATE TABLE IF NOT EXISTS positions (
    station_id INT PRIMARY KEY,
    position_x INT NOT NULL,
    position_y INT NOT NULL,
    nom VARCHAR(100) NOT NULL,
    FOREIGN KEY (station_id) REFERENCES stations(station_id)
);