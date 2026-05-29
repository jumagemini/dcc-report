# 📋 Field Report Generator

![Image](./static/images/dashboard.png "Project Dashboard UI")
A Django‑based web application for collecting field installation data of network devices (ONU, Indoor APs, Outdoor AP) at institutions. It generates a **per‑institution PDF report** and a **per‑DCC Excel summary** with installation photos. A RESTful API enables integration with external systems.

---

## ✨ Features

### Core Functionality
- **Interactive web form** – mimics official paper‑based installation forms with dynamic QTY and N/A placeholders.
- **PDF generation** – each institution gets a polished, A4‑sized PDF report (supports preview and download).
- **Excel reports** – two‑sheet workbook per DCC:
  - Sheet 1: Device summary table mirroring official serial‑number logs.
  - Sheet 2: Before/After installation photos with device‑type labels.
- **Bulk import** – upload an Excel file and a ZIP of photos to automatically create multiple institution records.
- **Device labels (Word)** – generate a printable Word document with institution‑wise device stickers.

### Dashboard & User Management
- **Unified Dashboard** – a responsive, card‑based interface where authenticated users see only their assigned DCCs and can quickly add, view/edit institutions, download reports, and more.
- **User Authentication & Authorization** – login required for all actions. Super admins assign DCCs to users; each user can only manage institutions in their assigned DCCs.
- **User‑Specific Limits** – admins can set a maximum number of institutions a user may install per DCC. The dashboard shows live counts.
- **Admin‑Approved Deletion** – normal users request deletion; the request appears in the Django admin where an admin can approve or reject (with an optional reason). Users receive notifications about the outcome.
- **User Notifications** – a bell‑icon notification system alerts users when a deletion request is approved/rejected or when an admin sends them a message.
- **Admin Messaging** – from the Django admin, administrators can send messages to the creator(s) of selected institutions, which appear as notifications.

### Photo Management & Reports
- **Photo Collection per Institution** – before/after photos for each device (ONU, Indoor AP1‑AP3, Outdoor AP1) are stored and viewable in edit mode.
- **Photo Report (Word)** – a per‑DCC Word document with images arranged exactly like Excel Sheet 2.
- **Photo Report (Excel)** – the existing Sheet 2 with images and N/A placeholders.
- **PhotoBucket** – download a ZIP of all photos for an institution (with sub‑folders for before/after).
- **DCC Photos** – download a master ZIP of all institution photos for a DCC.
- **DCC Photo Dump (Word)** – download a single Word file containing all institutions' photos for a DCC.

### Installation Modes
- **Passive Installation** – traditional file‑upload form for selecting photos from the device gallery.
- **Active Installation** – a separate form that uses the device camera to capture photos. Integrated with **OCR** (Tesseract) to automatically read device serial numbers from the captured before‑photos and fill the form fields, reducing manual data entry and errors.

### Digital Signature
- **Canvas‑based signature** – users can draw their signature directly on the form using a mouse or touch screen.
- **Default Signature** – the user’s profile signature is used as a fallback for institutions if no new signature is drawn.
- The signature is embedded in the generated PDF.

### Progressive Web App (PWA) & Offline Support
- **Installable** – the app can be added to a device’s home screen and launched in standalone mode, with a custom icon and splash screen.
- **Offline Data Entry** – when the network is unavailable, institution data is saved locally (IndexedDB) and automatically synced when the connection returns.
- **Landscape‑First Design** – a friendly prompt encourages landscape orientation on mobile devices for the best form‑filling experience.
- **Service Worker Caching** – core assets are cached for fast loading and basic offline viewing.

### Admin‑Friendly
- **Django Admin Integration** – clickable preview/download links for PDFs and Excel reports.
- **Deletion Request Management** – approve/reject deletion requests with optional reason.
- **Bulk Actions** – download Excel reports, send messages to users, approve/reject deletion requests.

### REST API
- Full CRUD for DCCs, Institutions, and Photos.
- Custom endpoints: PDF download, Excel download, photo upload.
- Swagger documentation available at `/api/swagger/`.

---

## 🛠️ Tech Stack

- Python 3.8+
- Django 4.2+
- WeasyPrint (PDF generation)
- openpyxl (Excel generation)
- Pillow (image handling)
- Django REST Framework (API)
- drf‑yasg (Swagger docs)
-  Tesseract OCR (via pytesseract) for serial number recognition
- Celery + Redis (for asynchronous OCR tasks)
- Signature Pad (JavaScript library for digital signatures)

---

## ⚙️ Prerequisites

- Python 3.8+ and pip
- Virtual environment tools (virtualenv, venv, or pipenv)
- System libraries for WeasyPrint:
  - **Ubuntu/Debian**: `sudo apt-get install build-essential python3-dev libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info`
  - **macOS**: `brew install cairo pango gdk-pixbuf libffi`
  - **Windows**: install GTK3 runtime from [GTK for Windows](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)
- Tesseract OCR (for Active Installation serial number detection) – install from your system package manager or [Tesseract GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
- Redis (for Celery) – install and run `redis-ser
---

## 📥 Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/jumagemini/dcc-report.git
   
   cd dcc-report
   ```
2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   venv\Scripts\activate      # Window
   ```
3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   If no *requirements.txt* exists, install manually:
   ```bash
   pip install django openpyxl WeasyPrint Pillow djangorestframework drf-yasg celery redis pytesseract
   ```
4. **Configure environment variables (optional)**
   
   Create a *.env* file or export variables for sensitive settings. In *settings.py*, replace hard‑coded values with *os.environ.get()*.
5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```
6. **Create a superuser (for admin access)**
   ```bash
   python manage.py createsuperuser
   ```
7. **Collect static files (if needed)**
   ```bash
   python manage.py collectstatic
   ```         
8. **Start Redis (in a separate terminal)**
   ```bash
   systemctl start redis-server
   ```
9. **Start Celery worker (in another terminal)**
   ```bash
   celery -A field_project worker -l info
   ```   
10. **Start the development server**
	```bash
	python manage.py runserver 0.0.0.0:8000
	```
11. **Access the application**
   
  * Web form: http://127.0.0.1:8000/dcc/1/add/ (create a DCC via admin first)

* Admin panel: http://127.0.0.1:8000/admin/

* Dashboard: http://127.0.0.1:8000/dashboard/

* API demo: http://127.0.0.1:8000/api/demo/

* Swagger UI: http://127.0.0.1:8000/api/swagger/
   
## 🚀 Quick Start

1. Log in to the Django Admin and create a DCC entry (e.g., TINDERET DCC).

2. Create a User Profile and assign the user to that DCC.

3. (Optional) Set a maximum institution limit via User DCC Limit.

4. Log in as the user and go to /dashboard/. You’ll see the DCC card with action buttons.

5. Click ➕ Passive Installation or 📸 Active Installation to add an institution.

* Passive: fill the form and upload photos from files.

* Active: use the camera to take photos; OCR will attempt to read serial numbers from before‑images and fill the form automatically.

6. After saving, the generated PDF opens in a new tab. The dashboard remains open for the next entry.

7. From the dashboard, you can also View/Edit institutions, download Excel/Word reports, device labels, photo buckets, and request deletion.

8. To test offline: switch your device to airplane mode, fill the form, and submit. The data is saved locally. When you reconnect, it will sync automatically.

## 📂 Project Structure
![Image](./static/images/tree.png "Project Directory Structure")

* field_project/ – Django project settings and Celery configuration.

* reports/ – main app: models, views, templates, admin, forms, tasks (OCR), utilities (Word/Excel generation, stickers, photo ZIP).

* api/ – REST API app with serializers, viewsets, Swagger docs, and demo page.

* static/images/ – logos (kplc.png, ict.png) and other static assets.

* media/ – uploaded photos, signatures, and bulk import files.

* templates/ – shared base template, admin overrides, registration templates.
## 📝 API Documentation
The API provides endpoints for managing DCCs, institutions, and photos. When the server is running, visit:

Swagger UI: **http://127.0.0.1:8000/api/swagger/**

ReDoc: **http://127.0.0.1:8000/api/redoc/**

## Authentication
To use authenticated endpoints, obtain a token:

```bash
curl -X POST http://127.0.0.1:8000/api/auth/ -H "Content-Type: application/json" -d '{"username":"admin","password":"yourpassword"}'
```
Then include the token in requests:

```bash
curl -H "Authorization: Token your_generated_token" http://127.0.0.1:8000/api/dccs/
```
## 🧪 Running Tests
```bash
python manage.py test api -v 2
```
Or use pytest for a more interactive output:

```bash
pip install pytest pytest-django pytest-sugar

pytest api/tests.py
```
## 🤝 Contributing
Contributions are welcome! Please [open an issue](https://github.com/jumagemini/dcc-report/issues "Project Issue") or submit a pull request.
## 💡 Need Help?
If you encounter any issues, please [open an issue](https://github.com/jumagemini/dcc-report/issues "Project Issue") with a clear description and steps to reproduce.

 
