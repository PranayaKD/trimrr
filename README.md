# Trimrr: Precision URL Shortener SaaS

Trimrr is a premium, high-performance URL shortening platform designed with a **"Liquid Smooth"** editorial aesthetic. Built for scalability and security, it offers real-time analytics, dynamic QR code generation, and integrated subscription management via Razorpay.

---

### 🌐 Landing Page
**A high-fidelity, "no-line" design built with Tailwind CSS and HTMX.**
![Trimrr Landing Page](stitch_trimrr_url_shortener_saas/landing_page/screen.png)

---

### 📊 Intelligence Dashboard
**Manage your links with precision. Track every click, visitor, and conversion in real-time.**
![Trimrr Dashboard](stitch_trimrr_url_shortener_saas/my_links_dashboard/screen.png)

---

### 📈 Deep Link Analytics
**Sub-second data freshness for statistics and charts. Visualize 7-day conversion velocity.**
![Trimrr Analytics](stitch_trimrr_url_shortener_saas/link_analytics/screen.png)

---

### 📱 Premium Mobile Experience
**Optimized for touch with hardware-accelerated transitions and responsive layouts.**
![Trimrr Mobile Onboarding](stitch_trimrr_url_shortener_saas/onboarding/screen.png)

---

## 🚀 Key Features

- **Liquid Smooth UI**: Minimalist interaction system with hardware-accelerated CSS reveals.
- **Precision Analytics**: Real-time click tracking, device/browser detection, and geographic mapping.
- **Dynamic QR Codes**: Generate high-precision QR codes with instant "Copy to Clipboard" functionality.
- **Secure by Design**: Built-in protection against redirect loops, malicious keywords, and malware-prone extensions.
- **Enterprise-Ready Backend**: Automated Redis caching with graceful fallback logic and Celery-powered background tasks.
- **Monetization Built-in**: Integrated Razorpay subscription gateway (Pro Tier at ₹399/year).

## 🛠️ Technology Stack

- **Backend**: Python 3.x, Django 5.x
- **Frontend**: Tailwind CSS, HTMX, Alpine.js
- **Database**: PostgreSQL (Production) / SQLite (Local)
- **Caching**: Redis (with LocMem fallback)
- **Async Tasks**: Celery
- **Payments**: Razorpay API
- **Emails**: SMTP (Gmail)

## 📦 Setup & Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/PranayaKD/trimrr.git
   cd trimrr
   ```

2. **Configure Environment**:
   Create a `.env` file in the root directory with your DB, Redis, Razorpay, and SMTP keys (refer to `.env.example`).

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Start Dev Server**:
   ```bash
   python manage.py runserver
   ```

---

© 2026 Trimrr Editorial. Crafted for Precision by [PranayaKD](https://github.com/PranayaKD).
