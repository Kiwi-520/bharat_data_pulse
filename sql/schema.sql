CREATE TABLE dim_location(
    location_id INT PRIMARY KEY AUTO_INCREMENT,
    district VARCHAR(50),
    state VARCHAR(50),
    market VARCHAR(50)
);

CREATE TABLE dim_commodity(
    commodity_id INT PRIMARY KEY AUTO_INCREMENT,
    commodity VARCHAR(50),
    commodity_code INT
);

CREATE TABLE fact_daily_price(
    price_id INT PRIMARY KEY AUTO_INCREMENT,
    location_id INT NOT NULL,
    commodity_id INT NOT NULL,
    FOREIGN KEY (location_id) REFERENCES dim_location(location_id),
    FOREIGN KEY (commodity_id) REFERENCES dim_commodity(commodity_id),
    min_price DECIMAL(10,3),
    max_price DECIMAL(10,3),
    modal_price DECIMAL(10,3),
    grade VARCHAR(20),
    variety VARCHAR(50),
    arrival_date DATE
);