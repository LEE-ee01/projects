# ShopEasy 电商数据仓库 — 数据血缘

## 整体数据流

```
                         ┌─────────────────┐
                         │  业务源系统       │
                         │  (CSV 文件)      │
                         └───┬───┬───┬─────┘
                             │   │   │
                    ┌────────┘   │   └────────┐
                    ▼            ▼            ▼
              users.csv    products.csv   orders.csv
                    │            │            │
              ┌─────┴────────────┴────────────┴─────┐
              │             ODS 层                   │
              │  ods_users  ods_products  ods_orders │
              └─────┬────────────┬────────────┬─────┘
                    │            │            │
              ┌─────┴────────────┴────────────┴─────┐
              │             DWD 层                   │
              │  dwd_users  dwd_products  dwd_orders │
              └─────┬────────────┬────────────┬─────┘
                    │            │            │
         ┌──────────┼────────────┼────────────┼──────────┐
         │          │            │            │          │
         ▼          ▼            ▼            ▼          ▼
    ┌─────────┐ ┌────────┐ ┌─────────┐ ┌────────┐
    │DWS 层    │ │        │ │         │ │        │
    │ 用户汇总  │ │商品汇总 │ │城市汇总  │ │品类汇总 │
    └────┬────┘ └───┬────┘ └────┬────┘ └───┬────┘
         │          │          │          │
         └──────────┼──────────┼──────────┘
                    │          │
         ┌──────────┴──────────┴──────────┐
         │            ADS 层               │
         │  (10 张业务指标表)              │
         │                                 │
         │  ads_daily_kpi                  │
         │  ads_user_cohort                │
         │  ads_category_ranking           │
         │  ads_city_performance           │
         │  ads_membership_analysis        │
         │  ads_hourly_traffic             │
         │  ads_brand_share                │
         │  ads_discount_effectiveness     │
         │  ads_user_rfm                   │
         │  ads_monthly_summary            │
         └──────────────┬─────────────────┘
                        │
                        ▼
                 ┌──────────────┐
                 │  CSV 报表导出  │
                 │  (output/reports/) │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │  Streamlit   │
                 │  运营看板     │
                 └──────────────┘
```

## 表级血缘明细

| 目标表 | 上游表 | 关系 |
|--------|--------|------|
| ods.ods_users | users.csv | 1:1 直接导入 |
| ods.ods_products | products.csv | 1:1 直接导入 |
| ods.ods_orders | orders.csv | 1:1 直接导入 |
| dwd.dwd_users | ods.ods_users | 1:1 清洗 |
| dwd.dwd_products | ods.ods_products | 1:1 清洗 |
| dwd.dwd_orders | ods.ods_orders | 1:1 清洗+拆分 |
| dws.dws_daily_user_orders | dwd.dwd_orders | N:1 日聚合 |
| dws.dws_daily_product_sales | dwd.dwd_orders + dwd.dwd_products | N:1 日聚合+JOIN |
| dws.dws_daily_city_sales | dwd.dwd_orders | N:1 日聚合 |
| dws.dws_daily_category_sales | dwd.dwd_orders + dwd.dwd_products | N:1 日聚合+JOIN |
| ads.ads_daily_kpi | dwd.dwd_orders | 日聚合 |
| ads.ads_user_cohort | dwd.dwd_users + dwd.dwd_orders | 周聚合+JOIN |
| ads.ads_category_ranking | dws.dws_daily_category_sales | 月聚合+窗口函数 |
| ads.ads_city_performance | dws.dws_daily_city_sales | 月聚合+窗口函数 |
| ads.ads_membership_analysis | dwd.dwd_orders + dwd.dwd_users | 月聚合+JOIN |
| ads.ads_hourly_traffic | dwd.dwd_orders | 小时聚合 |
| ads.ads_brand_share | dws.dws_daily_product_sales + dwd.dwd_products | 全量聚合+JOIN |
| ads.ads_discount_effectiveness | dwd.dwd_orders | 月聚合 |
| ads.ads_user_rfm | dwd.dwd_orders | 全量聚合+NTILE |
| ads.ads_monthly_summary | dwd.dwd_orders + dwd.dwd_users | 月聚合 |
