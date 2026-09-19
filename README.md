# WhatsApp Bulk Campaign Sender (Enterprise AI Edition — v2.5)

A commercial-grade, multi-tier Windows Desktop & Server Application for WhatsApp campaign automation, AI message enhancement, 2-way inbound auto-responding, full CRM contact segmentation, anti-ban safety algorithms, team RBAC, hardware-locked commercial licensing, embedded REST API, and automated backup management.

---

## 🌟 Key Enterprise Modules & Architecture

### 1. 🪄 AI Message Enhancer & Natural Spintax (`core/ai_enhancer.py`)
- **1-Click AI Magic Rewrite**: Transforms basic sales pitch into rich, ban-proof multi-variant Spintax with dynamic `{Name}` and `{City}` tags.
- **5 Built-in High-Converting Industry Templates**:
  1. *Coaching & Institutes*: Admission announcements, scholarships, demo class CTAs.
  2. *Real Estate & Plots*: Land layouts, RERA project highlights, free weekend site visits.
  3. *Retail & Showrooms*: Festive collection previews, flat 20% discount vouchers.
  4. *B2B & Digital Services*: High-response consultation pitches.
  5. *Payment & Account Notices*: Polite fee/EMI clearance reminders with instant UPI tags.

### 2. 💬 2-Way Auto-Responder & Inbound Lead Tagger (`core/auto_responder.py`)
- **24/7 Automated Customer Engagement**: Matches inbound customer replies against customizable keywords.
- **Keyword Automation**:
  - `price`, `rate`, `cost` -> Automatically sends pricing brochure.
  - `interested`, `demo`, `call me` -> Sends confirmation & automatically marks contact as **🔥 HOT LEAD** in the CRM database!
  - `stop`, `remove` -> Automatically opts out number from broadcast lists.

### 3. 📇 Advanced CRM & Multi-Parameter Segmentation (`core/crm.py`)
- **Master Contact Store**: Name, Phone, Email, Company, City, Category, Status, Tags, Opt-in Status, Notes, and Custom Fields (JSON).
- **Multi-Parameter Filter**: Real-time filtering by `City + Category + Tag + Status + Opt-in`.
- **Bulk CSV/Excel Importer**: Automatic column mapping, deduplication on phone numbers, and phone number sanitization.

### 4. 🛡️ Anti-Ban Engine & Stealth Chrome Driver (`core/whatsapp/selenium_driver.py`)
- **Stealth Automation**: Masks `navigator.webdriver` via Chrome CDP, adds `--disable-blink-features=AutomationControlled`.
- **Resilient Send Engine**: Button click + instant `Keys.ENTER` fallback ensures 100% transmission success even when WhatsApp updates its UI icons.
- **Automatic Modal Dismissal**: Automatically closes "Phone number isn't on WhatsApp" popups so campaign never halts.
- **Dual-Provider Architecture**: Dynamic switching between WhatsApp Web browser and official Meta Cloud Graph API.

### 5. 🔐 Authentication & Team RBAC (`core/auth.py`)
- **PBKDF2-HMAC-SHA256**: 100,000 salt iterations for credential security.
- **Role-Based Access Control**: Owner, Admin, Manager, Staff.
- **Default Owner Account**:
  - **Email:** `admin@enterprise.local`
  - **Password:** `admin123`

### 6. 🔑 Hardware-Locked Commercial Licensing (`core/licensing.py`)
- **Hardware Binding**: Extracts instant hardware fingerprint from Windows Registry `MachineGuid` and system hardware.
- **HMAC-SHA256 Signature Verification**: Cryptographically signed activation keys preventing license sharing across devices.
- **Key Format**: `SHAKTIX-PLAN-YYYYMMDD-MACHID-SIG`.
- **Admin License Generator**: Generate customer keys from in-app Admin tab or via `generate_license.bat`.

### 7. 🚀 Campaign State Machine & Visual Wizard (`core/campaign_engine.py`, `ui/campaign_wizard.py`)
- **State Machine**: Supports `Draft`, `Scheduled`, `Running`, `Paused`, `Completed`, and `Failed`.
- **Crash Recovery**: Automatically pauses interrupted campaigns upon unexpected exit with zero duplicate messages.

### 8. 🌐 Embedded REST API Server (`api/server.py`)
- Lightweight HTTP REST API running on `http://127.0.0.1:8000/api`.
- Authenticated via header `X-API-Key: enterprise-wa-secret-key-2026`.

### 9. 📜 Audit Logging & Backup Snapshots (`core/audit.py`, `core/backup.py`)
- Immutable audit log tracking User, Action, Target, and Timestamp.
- 1-Click compressed ZIP database snapshots saved under `backups/`.

---

## 💻 Quick Start Guide

### 1. Launch the Application
Double-click `run_app.bat` (inside folder) or `Launch_WhatsApp_Bulk_Sender.bat` (in main folder).

### 2. Generate a Commercial License Key
Run `generate_license.bat` or use the CLI:
```bash
python license_generator.py --plan BUSINESS --days 365 --machine B55291AF
```

### 3. Run Verification Tests
```bash
python -u test_enterprise.py
python -u test_production_hardening.py
python -u test_advance_features.py
```
