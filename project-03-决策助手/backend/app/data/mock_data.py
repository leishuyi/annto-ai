WAREHOUSE_STOCK = [
    {"warehouse_id":"WH-华东-001","sku":"SKU-AC-001","product":"美的空调KFR-35GW","qty":2500,"max":5000},
    {"warehouse_id":"WH-华东-002","sku":"SKU-FR-001","product":"美的冰箱BCD-470","qty":1800,"max":3000},
    {"warehouse_id":"WH-华南-001","sku":"SKU-AC-001","product":"美的空调KFR-35GW","qty":3200,"max":5000},
    {"warehouse_id":"WH-华北-001","sku":"SKU-AC-001","product":"美的空调KFR-35GW","qty":1200,"max":3000},
]
IN_TRANSIT = [
    {"order_id":"ORD-0724-001","sku":"SKU-AC-001","qty":500,"origin":"佛山","dest":"上海","eta":"2026-07-28","status":"运输中"},
    {"order_id":"ORD-0724-002","sku":"SKU-FR-001","qty":300,"origin":"合肥","dest":"北京","eta":"2026-07-26","status":"运输中"},
]
SALES_HISTORY = [{"date":f"2026-07-{d:02d}","sku":"SKU-AC-001","region":"华东","sales":110+d} for d in range(1,24)]
