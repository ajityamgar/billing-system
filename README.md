# Supermarket Billing System (Flask)

INTRODUCTION -
Supermarket Billing System (Point-of-Sale Simulator)

The project titled “Supermarket Billing System” is a modern web application designed to simulate a supermarket billing counter end-to-end. In daily retail operations, manual billing or disparate tools can be slow, error-prone, and difficult to audit. This system streamlines checkout by combining fast product entry (product code or live barcode scanning), accurate cart computation (subtotal, GST/VAT, total), payment handling (Cash/UPI), WhatsApp bill delivery, and on-demand invoice PDF generation.

The application leverages web technologies and a lightweight Python backend (Flask). The frontend provides a clean cashier UI and integrates a live in-browser barcode scanner (Quagga2) to quickly identify products. The backend manages a session-based cart, looks up product details from a JSON database, calculates totals, builds a UPI deeplink and QR for digital payments, and sends the final bill to WhatsApp via pywhatkit or Twilio. For record keeping, the system generates a professional PDF invoice.

Designed for clarity and extensibility, this project can be adapted for small stores, training, demos, or as a foundation for a more complete POS. While optimized for local/offline-style demos, it outlines a path to production features such as persistent databases, role-based access, and inventory.


ACKNOWLEDGEMENT -
I extend my sincere gratitude to the open-source community and tools that made this system possible:
- Flask (Python web framework) for rapid development
- Quagga2 for in-browser barcode scanning
- pywhatkit and Twilio WhatsApp API for messaging
- ReportLab for professional PDF generation
- The broader web ecosystem (MDN, Stack Overflow, Python/JS communities) for references and learning resources


SCOPE OF THE SYSTEM -
The Supermarket Billing System is a cashier-focused POS simulator providing:
- Product Entry:
  - Enter product code manually (barcode simulation)
  - Scan physical barcodes via the device camera
- Cart Operations:
  - Add, update quantity, and remove items
  - Real-time table view and totals
- Billing:
  - Subtotal, tax (GST/VAT at a configurable rate), final total
- Payments:
  - Cash or UPI
  - UPI deeplink and QR for scan-and-pay
- Bill Delivery:
  - Send bill to WhatsApp (pywhatkit/Twilio)
  - Invoice PDF available via a shareable URL

Out of scope (demo limits): user accounts, roles/permissions, persistent inventory, discount engine, refunds/returns, and hardware printer drivers. These can be added in future enhancements.


REQUIREMENT ANALYSIS -
1) Product Entry and Lookup
- Input product code or scan barcode; lookup details from JSON database (name, price, category).
- Validate code existence; handle unknown codes gracefully.

2) Cart Management
- Add item with default or specified quantity.
- Update quantity (guard against zero/negative) and remove items.
- Maintain per-session cart to isolate different browsers/cashiers.

3) Billing
- Compute line totals, subtotal, tax (configurable rate), and final total.
- Reflect totals live in UI; return totals from backend for consistency.

4) Payments (Cash/UPI)
- Cash: mark as paid and finalize bill.
- UPI: generate deeplink (`upi://pay`) and a QR for scanning; include both in the bill message.

5) WhatsApp Integration
- pywhatkit: use WhatsApp Web to send messages (simple/local demo).
- Twilio: send programmatically via WhatsApp Business API when configured.
- Fallback: simulate send and log message if neither is available.

6) Invoice PDF
- Generate on demand from the last invoice in the session.
- Include itemized list, subtotal, tax, and totals with time stamp.

7) Non-Functional
- Simple, responsive UI with clear feedback
- Minimal setup; local-first demo
- Readable, modular code for extension


HARDWARE AND SOFTWARE REQUIREMENTS -
Hardware Requirements
- Device with a modern browser (desktop/laptop recommended)
- Integrated/USB camera for barcode scanning
- 4 GB RAM minimum (8 GB recommended) for comfortable development

Software Requirements
- OS: Windows 10/11 (or Linux/macOS)
- Python: 3.10+
- Browser: Chrome/Edge with camera access
- Dependencies (via `requirements.txt`): Flask, pywhatkit, twilio, qrcode, reportlab


SYSTEM DESIGN -
Frontend (templates/)
- `index.html`: Cashier UI with product code input, Scan Barcode modal, cart table, totals, payment options, WhatsApp number, and action buttons
- `style.css`: Styling for modern POS look, including scanner modal
- `script.js`: Cart logic, API calls, Quagga2 integration; keeps scanner running to scan multiple products (with duplicate throttling)

Backend (`app.py`)
- Core Routes:
  - `/` UI
  - `/style.css`, `/script.js` serve assets from `templates` (no static folder required)
  - `/cart` get current cart snapshot
  - `/add_to_cart` add by code and quantity
  - `/update_item` change quantity
  - `/remove_item` remove item
  - `/checkout` compute totals
  - `/send_bill` WhatsApp bill send (Cash/UPI)
  - `/upi_qr` generate QR for UPI deeplink
  - `/invoice_pdf` generate downloadable invoice PDF
- Business Logic:
  - Product lookup from `data/products.json`
  - Session-based cart
  - Totals calculation centralized server-side
  - UPI deeplink builder; QR via `qrcode`
  - WhatsApp: pywhatkit first; Twilio when credentials set; simulate otherwise
  - PDF: ReportLab

Data
- `data/products.json`: Sample product catalog with codes, names, categories, and prices


DATABASE TABLES (Reference for Real DB) -
While the demo uses a JSON file and session memory, the production model typically includes:
- products(id, code, name, category, price, created_at, updated_at)
- invoices(id, customer_phone, subtotal, tax, total, payment_method, created_at)
- invoice_items(id, invoice_id, product_id, price, quantity, line_total)
- payments(id, invoice_id, method, status, transaction_ref, created_at)


Advantages -
- Fast checkout with barcode scanning and code entry
- Accurate totals with tax; consistent server-side calculation
- UPI payment request delivered as link and QR
- WhatsApp delivery for digital receipts; optional Twilio for production
- Clean UI; minimal setup for demos and training
- Extensible architecture for real-world POS features

Limitations -
- Session-only cart; no persistent database by default
- No user authentication/roles in demo
- Barcode success depends on camera quality and lighting
- pywhatkit relies on WhatsApp Web being logged in and visible
- Local URLs for PDF/QR are not internet-accessible without tunneling


FUTURE ENHANCEMENT -
- Persistent database (SQLite/PostgreSQL) with ORM models
- Authentication and role-based access (cashier, manager)
- Inventory management, discounts, refunds/returns
- Thermal printer integration for receipts
- Product catalog management UI and bulk import
- Cloud deployment, HTTPS, domain, and CDN for assets
- PWA/offline support and mobile-friendly cashier app
- Multi-register syncing and consolidated reporting dashboard


CONCLUSION -
The Supermarket Billing System demonstrates a practical, end-to-end POS flow: rapid product entry, reliable cart and billing, UPI payment request, WhatsApp delivery, and professional PDF invoices. It is intentionally lightweight to keep onboarding simple while providing clear extension points for production needs. With the proposed enhancements, it can evolve into a robust POS suitable for small to medium retail operations.


BIBLIOGRAPHY -
- Flask Documentation – `https://flask.palletsprojects.com/`
- Quagga2 (Barcode Scanner) – `https://github.com/ericblade/quagga2`
- pywhatkit – `https://pypi.org/project/pywhatkit/`
- Twilio WhatsApp – `https://www.twilio.com/whatsapp`
- ReportLab – `https://www.reportlab.com/dev/docs/`
- MDN Web Docs – `https://developer.mozilla.org/`
- Python Packaging (pip) – `https://pip.pypa.io/`


PROJECT STRUCTURE -
```
├─ app.py
├─ data/
│  └─ products.json
├─ templates/
│  ├─ index.html
│  ├─ style.css
│  └─ script.js
├─ requirements.txt
└─ README.md
```

SETUP GUIDE (QUICK START) -
Windows PowerShell:
```bash
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
py -3 app.py
```
Open: `http://127.0.0.1:5000`

Optional Environment Variables:
- `FLASK_SECRET_KEY="<random>"`
- `TAX_RATE=0.18`
- `UPI_VPA=merchant@upi`
- `UPI_NAME=Supermarket`
- Twilio (optional): `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM`

