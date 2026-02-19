---
id: CAPABILITY-008
type: capability
title: Stock Optimization Capability
status: deprecated
owner: VP Engineering
created: '2024-04-12T01:43:22.921Z'
updated: '2025-08-09T12:33:30.523Z'
tags:
  - capability
  - inventory-management
summary: Stock Optimization Capability
evidence_links:
  - PROCESS-017
  - PROCESS-018
  - STANDARD-018
example: true
---

## Domain

- Inventory Management
- Supply Chain
- Merchant Operations

## Maturity (0-5)

**Current score: 2 / 5 (Repeatable)**

- **Level 0 - Initial**: No stock optimization tooling. Merchants manually review stock levels and reorder based on intuition. Stockouts and overstock situations are common.
- **Level 1 - Ad hoc**: Some merchants have built private spreadsheet models to estimate reorder timing. Results vary widely and the models are not maintained or shared.
- **Level 2 - Repeatable** (current): Configurable reorder points and automated PO generation are available via the Automated Reorder System. Velocity-based forecasting with stockout date projections is deployed. Overstock flags identify slow-moving SKUs. These tools operate independently without integration between them.
- **Level 3 - Defined**: Forecasting informs reorder point recommendations. Reorder rules are auto-suggested based on historical velocity and supplier lead times. Tools are integrated into a unified stock health dashboard.
- **Level 4 - Managed**: Optimization metrics (stockout rate, inventory turnover, days-of-stock) are tracked per merchant and reported. Automated alerts when a merchant's portfolio deviates from their target stock health profile.
- **Level 5 - Optimizing**: ML-based demand sensing adjusts forecasts dynamically based on seasonality, trends, and external signals. Automated reorder quantities optimized for carrying cost vs stockout risk.

**Gap to Level 3**: The forecasting tool and reorder system currently operate as independent products. Integration work is needed so the forecasting model's velocity data feeds the reorder point recommendation engine. This is planned for H1 2026.

## Metrics

- Stockout rate (merchants using auto-reorder): 4.2% of SKU-months, target < 3% at Level 3
- Overstock identification rate: 11% reduction in average days-of-stock across the merchant base since forecasting launch, target 15% reduction
- Merchant adoption of automated reordering: 38% of eligible merchants, target 40% at Level 2
- Forecast accuracy (7-day horizon): Mean absolute error 13.8%, target < 15%
- Average reorder lead time compliance: 78% of reorders triggered within the recommended window, target 85%

## Evidence Links

- [[PROCESS-017|Reorder Rule Configuration Process]] - Process for configuring and tuning automated reorder rules per SKU
- [[PROCESS-018|Warehouse Sync Monitoring Process]] - Process ensuring accurate stock data flows into the optimization models
- [[STANDARD-018|Inventory Forecasting Standard]] - Standard defining acceptable forecast models, accuracy thresholds, and model refresh cadences

## Notes

This capability is marked deprecated at the top-level because a successor capability document (CAPABILITY-031 - Intelligent Inventory Automation) is in preparation and will replace this one when the forecasting-reorder integration is complete in H1 2026. In the meantime, this document reflects the current state of the stock optimization capability.

Key improvements needed for Level 3:
- Integrate velocity data from the Inventory Forecasting Tool into the Automated Reorder System's ROP calculation, replacing static merchant-configured reorder points with dynamically suggested values
- Build a unified stock health dashboard combining forecast projections, reorder status, and overstock indicators in a single view
- Publish cross-merchant stock optimization benchmarks to the merchant portal so merchants can compare their performance against the platform median
