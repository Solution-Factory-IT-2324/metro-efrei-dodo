DROP DATABASE IF EXISTS MEDV2;
CREATE DATABASE IF NOT EXISTS MEDV2 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE MEDV2;

CREATE TABLE IF NOT EXISTS agency (
    agency_id VARCHAR(50) PRIMARY KEY,
    agency_name VARCHAR(100) NOT NULL,
    agency_url VARCHAR(200) NOT NULL,
    agency_timezone VARCHAR(50) NOT NULL,
    agency_lang VARCHAR(10),
    agency_phone VARCHAR(20),
    agency_email VARCHAR(100),
    agency_fare_url VARCHAR(200)
);

CREATE TABLE IF NOT EXISTS calendar (
    service_id VARCHAR(50) PRIMARY KEY,
    monday TINYINT NOT NULL,
    tuesday TINYINT NOT NULL,
    wednesday TINYINT NOT NULL,
    thursday TINYINT NOT NULL,
    friday TINYINT NOT NULL,
    saturday TINYINT NOT NULL,
    sunday TINYINT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS calendar_dates (
    service_id VARCHAR(50) NOT NULL,
    date DATE NOT NULL,
    exception_type TINYINT NOT NULL,
    PRIMARY KEY (service_id, date)
);

CREATE TABLE IF NOT EXISTS pathways (
    pathway_id VARCHAR(255) PRIMARY KEY NOT NULL,
    from_stop_id VARCHAR(50) NOT NULL,
    to_stop_id VARCHAR(50) NOT NULL,
    pathway_mode TINYINT NOT NULL,
    is_bidirectional TINYINT NOT NULL,
    length DECIMAL(9, 2),
    traversal_time INT,
    stair_count INT,
    max_slope DECIMAL(5, 2),
    min_width DECIMAL(5, 2),
    signposted_as VARCHAR(100),
    reversed_signposted_as VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS routes (
    route_id VARCHAR(50) PRIMARY KEY,
    agency_id VARCHAR(50) NOT NULL ,
    route_short_name VARCHAR(10) NOT NULL ,
    route_long_name VARCHAR(100) NOT NULL ,
    route_desc VARCHAR(255),
    route_type TINYINT NOT NULL,
    route_url VARCHAR(200),
    route_color VARCHAR(6),
    route_text_color VARCHAR(6),
    route_sort_order INT
);

CREATE TABLE IF NOT EXISTS stop_extensions (
    object_id VARCHAR(50) NOT NULL,
    object_system VARCHAR(50),
    object_code VARCHAR(50),
    PRIMARY KEY (object_id, object_system, object_code)
);


CREATE TABLE IF NOT EXISTS stop_times (
    trip_id VARCHAR(255) NOT NULL,
    arrival_time TIME NOT NULL,
    departure_time TIME NOT NULL,
    stop_id VARCHAR(50) NOT NULL,
    stop_sequence INT NOT NULL,
    pickup_type TINYINT,
    drop_off_type TINYINT,
    local_zone_id VARCHAR(50),
    stop_headsign VARCHAR(100),
    timepoint TINYINT,
    PRIMARY KEY (trip_id, stop_sequence)
);

CREATE TABLE IF NOT EXISTS stops (
    stop_id VARCHAR(50) PRIMARY KEY NOT NULL,
    stop_code VARCHAR(50),
    stop_name VARCHAR(100) NOT NULL,
    stop_desc VARCHAR(255),
    stop_lon DECIMAL(9, 6) NOT NULL,
    stop_lat DECIMAL(9, 6) NOT NULL,
    zone_id VARCHAR(50), -- Can be null because value = 100 when not submitted is not applied in dataset
    stop_url VARCHAR(200),
    location_type TINYINT,
    parent_station VARCHAR(50),
    stop_timezone VARCHAR(50),
    level_id VARCHAR(50),
    wheelchair_boarding TINYINT,
    platform_code VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS transfers (
    from_stop_id VARCHAR(50) NOT NULL,
    to_stop_id VARCHAR(50) NOT NULL,
    transfer_type TINYINT NOT NULL,
    min_transfer_time INT,
    PRIMARY KEY (from_stop_id, to_stop_id)
);

CREATE TABLE IF NOT EXISTS trips (
    route_id VARCHAR(50) NOT NULL,
    service_id VARCHAR(50) NOT NULL,
    trip_id VARCHAR(255) PRIMARY KEY NOT NULL,
    trip_headsign VARCHAR(100),
    trip_short_name VARCHAR(50),
    direction_id TINYINT,
    block_id VARCHAR(50),
    shape_id VARCHAR(50),
    wheelchair_accessible TINYINT,
    bikes_allowed TINYINT
);