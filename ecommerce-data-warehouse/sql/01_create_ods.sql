-- ============================================================
-- ShopEasy 电商数据仓库
-- 01: ODS 层 (Operational Data Store) - 操作数据层
-- 说明：ODS 层保持与源系统一致的数据结构，不做业务逻辑加工
--       仅进行轻量的列名规范化和类型统一
-- ============================================================

-- ----------------------------------------------------------
-- ODS 用户信息表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS ods.ods_users (
    user_id           VARCHAR(20)   PRIMARY KEY,
    register_time     DATE          NOT NULL,
    city              VARCHAR(50),
    membership_level  VARCHAR(20)   NOT NULL,
    channel           VARCHAR(20),
    gender            VARCHAR(5),
    age_group         VARCHAR(20)
);

-- ----------------------------------------------------------
-- ODS 商品信息表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS ods.ods_products (
    product_id    VARCHAR(20)   PRIMARY KEY,
    category_l1   VARCHAR(50)   NOT NULL,
    category_l2   VARCHAR(50)   NOT NULL,
    brand         VARCHAR(100),
    unit_price    DECIMAL(12,2) NOT NULL,
    cost_price    DECIMAL(12,2) NOT NULL,
    supplier      VARCHAR(50)
);

-- ----------------------------------------------------------
-- ODS 订单事实表
-- ----------------------------------------------------------
CREATE TABLE IF NOT EXISTS ods.ods_orders (
    order_id        VARCHAR(20)    PRIMARY KEY,
    user_id         VARCHAR(20)    NOT NULL,
    product_id      VARCHAR(20)    NOT NULL,
    quantity        INTEGER        NOT NULL,
    unit_price      DECIMAL(12,2)  NOT NULL,
    order_amount    DECIMAL(12,2)  NOT NULL,
    discount        DECIMAL(12,2)  DEFAULT 0,
    discount_rate   DECIMAL(5,2)   DEFAULT 0,
    actual_amount   DECIMAL(12,2)  NOT NULL,
    order_status    VARCHAR(20)    NOT NULL,
    order_time      TIMESTAMP      NOT NULL,
    payment_time    TIMESTAMP,
    shipping_city   VARCHAR(50)
);
