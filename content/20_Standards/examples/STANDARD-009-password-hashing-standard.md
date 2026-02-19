---
id: STANDARD-009
type: standard
title: Password Hashing Standard
status: review
owner: Compliance Officer
created: '2024-02-01T18:12:25.359Z'
updated: '2025-01-27T22:18:39.605Z'
tags:
  - standard
  - user-authentication
summary: Password Hashing Standard
related_policies:
  - POLICY-008
  - POLICY-009
example: true
related_systems:
  - SYSTEM-008
  - SYSTEM-009
---

## Area

This standard defines the required algorithms, parameters, and practices for hashing passwords and other one-way-stored credentials in all systems operated by the engineering organization. It applies to any service that accepts and stores user-supplied passwords, PINs, or recovery codes.

## Controls

- Argon2id is the required hashing algorithm for new password storage implementations; bcrypt (cost factor >= 12) is acceptable for existing systems pending migration
- MD5, SHA-1, SHA-256, and unsalted hashing are explicitly prohibited for password storage
- Each password hash must include a unique, cryptographically random salt of at least 128 bits generated at hash time
- Argon2id parameters must meet minimum thresholds: memory cost >= 64 MiB, iterations >= 3, parallelism >= 1
- Password hashes must be stored in a dedicated column or field and must never be concatenated with other data
- Hash upgrades must be performed transparently at next successful login when a user's stored hash uses a deprecated algorithm
- Hash computation must be performed server-side; client-side pre-hashing before transmission does not satisfy this standard

## Compliance Mappings

- NIST SP 800-132: Recommendation for Password-Based Key Derivation
- OWASP Password Storage Cheat Sheet (Argon2id recommendation)
- ISO 27001 A.9.4.3: Password Management System

## Related Policies

- [[POLICY-008|Multi-Factor Authentication Policy]]
- [[POLICY-009|Session Management Policy]]
