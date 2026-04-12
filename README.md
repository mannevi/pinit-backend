<div align="center">

<img src="images/logo.png" alt="PINIT Logo" width="100" height="100">

# PINIT — Backend API

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Supabase](https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com)
[![Render](https://img.shields.io/badge/Deployed_on-Render-46E3B7?style=flat-square&logo=render&logoColor=white)](https://pinit-backend.onrender.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

**[Live API](https://pinit-backend.onrender.com)** · **[API Docs](https://pinit-backend.onrender.com/docs)** · **[Admin Panel](https://image-crypto-analyzer.vercel.app)** · **[Mobile App](https://pinit-mobile.vercel.app)**

</div>

---

> PINIT embeds a unique UUID invisibly into every pixel of an image at the point of capture — creating a tamper-evident cryptographic fingerprint. Any modification made after embedding is detected through forensic comparison, proving both authenticity and ownership. This repository is the shared backend API powering both the PINIT Admin Panel and the PINIT Mobile App.

---

## 🏗️ Architecture

```
┌─────────────────────┐         ┌──────────────────────┐
│  Admin Web Panel    │         │   Mobile App (APK)    │
│  React · Vercel     │         │  React + Capacitor    │
└────────┬────────────┘         └──────────┬────────────┘
         │                                 │
         └──────────────┬──────────────────┘
                        │  HTTPS / REST
               ┌────────▼─────────┐
               │   PINIT Backend   │
               │  FastAPI · Render │
               └────────┬─────────┘
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
      Supabase      Cloudinary    Resend
    (PostgreSQL)  (Media Store)  (Email OTP)
```

### Project Structure

```
pinit-backend/
│
├── main.py                    # App entry point, CORS, router registration
├── requirements.txt           # Python dependencies
├── runtime.txt                # Python version pin for Render
├── .env.example               # Environment variable reference
│
├── routers/
│   ├── auth.py                # Registration, OTP, login, JWT, WebAuthn
│   ├── vault.py               # Certified image asset storage and retrieval
│   ├── compare.py             # Forensic image comparison and tamper detection
│   ├── certificates.py        # Certificate generation and verification
│   ├── share_links.py         # Public share link generation
│   └── admin.py               # Admin-only endpoints (role-guarded)
│
├── models/
│   └── schemas.py             # Pydantic v2 request and response models
│
├── db/
│   └── database.py            # Supabase client setup
│
├── utils/
│   ├── auth_helpers.py        # JWT decode, role enforcement, audit log
│   ├── cloudinary_helper.py   # Image upload and retrieval
│   └── email_helper.py        # OTP delivery via Resend
│
└── tests/
    ├── test_cloudinary.py
    └── test_connection.py
```

---

## 📡 API Reference

| Router | Prefix | Description |
|---|---|---|
| Auth | `/auth` | Registration, OTP verification, login, JWT, WebAuthn passkeys |
| Vault | `/vault` | Store and retrieve certified image assets |
| Compare | `/compare` | Forensic comparison — pHash, histogram, pixel diff |
| Certificates | `/certificates` | Generate and verify authenticity certificates |
| Share Links | `/api/share-links` | Create public share tokens for vault assets |
| Admin | `/admin` | User management, audit log, platform stats *(admin role only)* |

### Forensic Comparison — Verdict Tiers

The `/compare` endpoint returns a 5-tier verdict based on multi-signal analysis:

| Verdict | Description |
|---|---|
| `EXACT MATCH` | Image is unmodified — pixel-perfect match |
| `STRONG MATCH` | Minor compression artefacts only — no tampering detected |
| `PARTIAL MATCH` | Detectable changes — possible cropping or minor edits |
| `WEAK SIMILARITY` | Significant differences — likely tampered |
| `NO MATCH` | Images are unrelated or heavily altered |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- A [Supabase](https://supabase.com) project
- A [Cloudinary](https://cloudinary.com) account
- A [Resend](https://resend.com) account for email OTP

### Installation

1. Clone the repository

```sh
git clone https://github.com/mannevi/pinit-backend.git
cd pinit-backend
```

2. Create and activate a virtual environment

```sh
python -m venv venv
source venv/bin/activate
# Windows: venv\Scripts\activate
```

3. Install dependencies

```sh
pip install -r requirements.txt
```

4. Configure environment variables

```sh
cp .env.example .env
# Open .env and fill in your credentials
```

5. Start the development server

```sh
uvicorn main:app --reload
```

The API will be running at `http://localhost:8000`  
Interactive docs available at `http://localhost:8000/docs`

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and fill in the following:

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon (publishable) key |
| `SUPABASE_SERVICE_KEY` | Supabase service role key |
| `JWT_SECRET` | Secret key for signing access tokens |
| `JWT_EXPIRE_MINUTES` | Token expiry window in minutes |
| `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud identifier |
| `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `RESEND_API_KEY` | Resend API key for transactional email |
| `EMAIL_FROM` | Sender address shown in OTP emails |
| `APP_URL` | Frontend base URL — used in CORS and email links |
| `RP_ID` | WebAuthn relying party domain |
| `RP_NAME` | WebAuthn relying party display name |

> **Note:** Never commit `.env` to version control. In production, all variables are configured directly in the Render dashboard.

---

## 🔗 Related Repositories

| Repository | Description | URL |
|---|---|---|
| [pinit-admin](https://github.com/mannevi/image-crypto-analyzer) | Admin Web Panel (React) | https://image-crypto-analyzer.vercel.app |
| [pinit-mobile](https://github.com/mannevi/pinit-mobile) | User Mobile App (React + Capacitor / Android APK) | https://pinit-mobile.vercel.app |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
