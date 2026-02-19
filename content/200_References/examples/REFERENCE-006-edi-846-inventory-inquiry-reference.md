---
id: REFERENCE-006
type: reference
title: EDI 846 Inventory Inquiry Reference
status: published
owner: Platform Team
created: '2025-05-16T01:37:11.608Z'
updated: '2025-12-10T05:31:03.970Z'
tags:
  - reference
  - inventory-management
summary: EDI 846 Inventory Inquiry Reference
upstream_url: https://docs.example.com/edi-846-inventory-inquiry-reference
last_synced: '2026-01-11T02:54:24.123Z'
attribution: ISO
license: CC BY-SA 4.0
category: tutorial
example: true
---

## Overview

EDI 846 (Inventory Inquiry/Advice) is an ANSI X12 electronic data interchange transaction set used in supply chain and retail to communicate current inventory levels between trading partners. It is most commonly sent by a supplier or distributor to a retailer or wholesale buyer to report on-hand stock positions without a request, or in response to an inventory inquiry.

In our inventory platform, EDI 846 is one of the three supported protocols for the Warehouse Integration Adapter. Warehouse partners who use EDI-capable WMS systems can push inventory snapshots or incremental updates to our platform using this format. This reference documents the segments and data elements our adapter parses, along with implementation notes for trading partners setting up an EDI 846 feed.

## Transaction Set Structure

An EDI 846 transaction follows the standard X12 envelope structure:

```
ISA  - Interchange Control Header
  GS   - Functional Group Header
    ST   - Transaction Set Header
    BIA  - Beginning Segment for Inventory Inquiry/Advice
    LIN  - Item Identification (repeating, one per SKU)
      QTY  - Quantity (repeating, one per quantity type)
      DTM  - Date/Time Reference (optional)
      REF  - Reference Identification (optional)
    SE   - Transaction Set Trailer
  GE   - Functional Group Trailer
IEA  - Interchange Control Trailer
```

Each LIN-QTY group represents one SKU's inventory position at a specific location.

## Key Segments

### ISA - Interchange Control Header

The ISA segment identifies the sender and receiver of the interchange and carries the interchange control number used for deduplication. Our adapter uses the ISA13 (interchange control number) as the idempotency key for the entire interchange to prevent duplicate processing if the same file is received more than once.

| Element | Position | Description |
|---------|----------|-------------|
| ISA06 | Sender ID | Trading partner's EDI identifier |
| ISA08 | Receiver ID | Our platform's EDI identifier (`OURINVPLTFRM`) |
| ISA13 | Control Number | Unique 9-digit interchange number |

### BIA - Beginning Segment for Inventory Inquiry/Advice

The BIA segment indicates whether the 846 is a full snapshot or an incremental update, and the reference date for the inventory positions.

| Element | Code | Description |
|---------|------|-------------|
| BIA01 | 00 | Original transaction |
| BIA02 | SR (Status Report) | Full inventory snapshot for the specified location |
| BIA02 | CH (Change) | Incremental update (only changed SKUs included) |
| BIA03 | Reference Number | Partner's internal reference for this transmission |
| BIA04 | Date | Date the inventory positions are valid as of (YYYYMMDD) |

Our adapter treats `SR` transmissions as a full reconciliation snapshot: it compares the transmitted quantities against current system quantities and generates `StockAdjusted` events for any differences. `CH` transmissions are treated as incremental events and generate `StockReceived` or `StockAdjusted` events for each changed line.

### LIN - Item Identification

The LIN segment identifies the product. Multiple qualifier codes are supported:

| LIN02 Qualifier | Description |
|-----------------|-------------|
| `UP` | UPC (GTIN-12) |
| `EN` | EAN-13 (GTIN-13) |
| `UK` | GTIN-14 |
| `SK` | Seller's SKU (partner's internal part number) |
| `VN` | Vendor's item number |

Our adapter attempts to resolve the item to a SKU in the following order: GTIN-14 (`UK`), GTIN-13 (`EN`), GTIN-12 (`UP`), then seller's part number (`SK`) via the SKU Registry's partner-number mapping table. If resolution fails, the line is written to the DLQ for manual review.

### QTY - Quantity

The QTY segment follows the LIN segment and carries the quantity for a specific quantity type code.

| QTY01 Code | Description | Our Usage |
|------------|-------------|-----------|
| `1` | Discrete Quantity | On-hand quantity (total physical stock) |
| `21` | Ordered Quantity | Quantity on open purchase orders |
| `QA` | Available for Sale | Available quantity (on-hand minus reserved) |
| `ZZZ` | Mutually Defined | Vendor-specific; documented per trading partner |

Our adapter maps QTY code `1` to `on_hand_qty` and code `QA` to the available quantity cross-check. If only `QA` is present (no `1`), the adapter uses `QA` as the on-hand quantity and logs a warning.

### DTM - Date/Time Reference

Optional segment carrying date qualifiers for the inventory position.

| DTM01 Code | Description |
|------------|-------------|
| `036` | Expiration Date |
| `007` | Effective Date |
| `AAB` | Pick Date |

### REF - Reference Identification

Optional segment for additional cross-reference data. Common usage includes warehouse location code (`REF*ZZ*WH-EAST`) or bin location (`REF*BN*AISLE-04-BIN-12`). Our adapter maps the `ZZ` (mutually defined) qualifier to the `location_id` field on the stock event if a matching warehouse is configured.

## Full Example - SR (Snapshot) Transmission

```
ISA*00*          *00*          *ZZ*PARTNERXYZ       *ZZ*OURINVPLTFRM    *250615*1430*^*00501*000000042*0*P*>~
GS*IB*PARTNERXYZ*OURINVPLTFRM*20250615*1430*42*X*005010~
ST*846*0001~
BIA*00*SR*INV-2025-0615*20250615~
LIN*1*UK*10012345678901~
QTY*1*250~
QTY*QA*198~
REF*ZZ*WH-NORTH~
LIN*2*EN*5901234123457~
QTY*1*0~
QTY*QA*0~
REF*ZZ*WH-NORTH~
SE*9*0001~
GE*1*42~
IEA*1*000000042~
```

This example transmits a snapshot for two SKUs at warehouse `WH-NORTH`. SKU identified by GTIN-14 `10012345678901` has 250 units on hand, 198 available. SKU identified by EAN-13 `5901234123457` has zero stock.

## Implementation Notes for Trading Partners

- **Segment terminator**: Our adapter expects `~` as the segment terminator. Files using `\r\n` or other terminators must be reconfigured. A mismatched terminator is the most common cause of EDI 846 parse failures in our system.
- **Repetition separator and composite element separator**: Use `^` and `>` respectively (as shown in the ISA segment above).
- **Encoding**: Files must be ASCII-encoded. UTF-8 is accepted but non-ASCII characters in reference fields will be stripped.
- **File delivery**: 846 files may be delivered via SFTP to the partner's designated inbound directory or via AS2. Consult the Warehouse Integration Adapter onboarding guide for connection details.
- **Frequency**: Snapshot (`SR`) transmissions should be sent no more than once per hour per location. Incremental (`CH`) transmissions can be sent as frequently as every 5 minutes.
- **Missing segments**: The `QTY` segment is mandatory for each `LIN`. Files with `LIN` segments that have no following `QTY` will be rejected.

## Sync Notes

This reference covers the EDI 846 X12 implementation as used in our warehouse integration adapter. For the full ANSI X12 005010 specification, consult the official X12 documentation. Re-sync this reference when the adapter adds support for new segments or qualifier codes.
