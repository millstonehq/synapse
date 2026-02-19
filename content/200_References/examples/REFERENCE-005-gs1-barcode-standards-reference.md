---
id: REFERENCE-005
type: reference
title: GS1 Barcode Standards Reference
status: published
owner: Security Team
created: '2024-03-31T07:53:50.987Z'
updated: '2025-04-20T02:54:24.238Z'
tags:
  - reference
  - inventory-management
summary: GS1 Barcode Standards Reference
upstream_url: https://docs.example.com/gs1-barcode-standards-reference
last_synced: '2025-05-15T01:17:44.620Z'
attribution: W3C
license: CC BY-SA 4.0
category: blog-post
example: true
---

## Overview

GS1 is the global organisation that maintains the standards for barcodes and electronic data interchange used in supply chain and inventory management. GS1 standards define how products, locations, shipments, and assets are uniquely identified and encoded in machine-readable form.

This reference summarises the GS1 barcode symbologies and identifier structures most relevant to our inventory platform, covering the encoding formats used at receiving, picking, and stock movement events. Our SKU Registry Service uses GS1 identifiers as the canonical product identification layer, and the Warehouse Integration Adapter processes GS1-encoded barcodes from WMS event feeds.

## GS1 Identification Keys

GS1 identification keys are numerical structures used to uniquely identify different objects in the supply chain.

### GTIN (Global Trade Item Number)

The GTIN is the primary identifier for a product or product variant. It is 14 digits and is the identifier stored as the `gtin` field on a SKU record in our system. GTINs are encoded in barcodes in several formats:

- **GTIN-8** (EAN-8): 8-digit GTIN for small packages where space is limited
- **GTIN-12** (UPC-A): 12-digit GTIN, predominant in North America
- **GTIN-13** (EAN-13): 13-digit GTIN, predominant internationally; zero-padded to 14 digits internally
- **GTIN-14**: Full 14-digit GTIN including the packaging indicator digit; used for cases and pallets

When scanning at receiving, all GTIN variants are normalised to 14 digits by left-padding with zeros. The SKU Registry's barcode lookup accepts any GTIN length and resolves to the canonical SKU record.

### GLN (Global Location Number)

The GLN is a 13-digit identifier for a physical location: a warehouse, a dock door, a bin location, or a business entity. Our system uses GLNs as the canonical `location_id` for warehouses that have GLN assignments. Warehouses without a GLN assignment use an internal `WH-NNN` identifier.

### SSCC (Serial Shipping Container Code)

The SSCC is an 18-digit identifier for a logistics unit (a pallet or carton). SSCCs appear in EDI 856 Advance Shipping Notices and on GS1-128 pallet labels. Our receiving flow captures the SSCC from incoming ASNs to link carton-level tracking to the receipt record.

## Barcode Symbologies

### EAN-13 / UPC-A

The most common retail barcode format. EAN-13 encodes a 13-digit GTIN; UPC-A encodes a 12-digit GTIN. Both are linear (1D) barcodes. Our handheld scanners at receiving and picking support both symbologies natively.

**Limitations**: EAN-13 and UPC-A encode only the GTIN. They cannot carry additional data such as batch number, expiry date, or serial number. For items requiring these attributes, GS1-128 or GS1 DataMatrix is required.

### GS1-128

A linear (1D) barcode using the Code 128 symbology with GS1 Application Identifiers (AIs) to encode structured data beyond the GTIN. GS1-128 is the primary format on warehouse shipping labels and pallet labels.

Common Application Identifiers used in our context:

| AI | Data Element | Format |
|----|-------------|--------|
| (00) | SSCC | 18 digits |
| (01) | GTIN | 14 digits |
| (10) | Batch/Lot Number | Up to 20 alphanumeric |
| (11) | Production Date | YYMMDD |
| (15) | Best Before Date | YYMMDD |
| (17) | Expiry Date | YYMMDD |
| (310n) | Net Weight (kg) | 6 digits with implied decimal |
| (37) | Count of Items | Up to 8 digits |

Our Warehouse Integration Adapter parses GS1-128 barcodes and extracts the GTIN, batch number, expiry date, and SSCC where present. These are stored on the stock event record.

### GS1 DataMatrix

A 2D barcode format used on small products (pharmaceuticals, surgical instruments, electronic components) where a 1D barcode would be too large. GS1 DataMatrix can encode the same Application Identifiers as GS1-128 in a compact 2D format. Our receiving scanners support DataMatrix scanning; the decoded payload is processed identically to GS1-128.

### GS1 QR Code

GS1's application of the QR Code symbology for consumer-facing product information (GS1 Digital Link). Not currently used in our warehouse receiving workflow but may be relevant for returns processing where customers scan consumer packaging.

## Application Identifiers in Receiving

When a warehouse scanner reads a GS1-128 label at receiving, our Warehouse Integration Adapter extracts the following fields and maps them to the stock event:

1. Extract GTIN from AI (01) and resolve to `sku_id` via SKU Registry barcode lookup
2. Extract SSCC from AI (00) and store as `container_id` on the receipt line
3. Extract batch number from AI (10) if present and store as `batch_ref`
4. Extract expiry date from AI (17) or best-before from AI (15) if present; validate that expiry is in the future
5. Publish `StockReceived` event with the resolved `sku_id`, `batch_ref`, and `expiry_date`

Barcodes without AI (01) (GTIN) are flagged as unreadable and require manual SKU lookup before the receipt can be completed.

## Sync Notes

This reference covers GS1 barcode standards as they apply to our inventory platform integration. For the full GS1 General Specifications, consult the GS1 website. Re-sync this document when the GS1 General Specifications are updated (typically annually) or when our supported barcode types change.
