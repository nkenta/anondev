# Anonymisation Reports

A professional, open-source, and highly configurable web application for **deep anonymisation of lived experience narratives**, supporting multi-level anonymisation, global entity coverage, file uploads, and modern authentication. 

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [How It Works](#how-it-works)
- [Screenshots](#screenshots)
- [Setup & Installation](#setup--installation)
  - [Requirements](#requirements)
  - [Environment Setup](#environment-setup)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
- [Configuration](#configuration)
  - [API Keys](#api-keys)
  - [spaCy Model](#spacy-model)
  - [Advanced Model Usage](#advanced-model-usage)
- [Usage](#usage)
  - [User Authentication](#user-authentication)
  - [Anonymisation Levels](#anonymisation-levels)
  - [Supported File Types](#supported-file-types)
  - [Viewing & Downloading Reports](#viewing--downloading-reports)
- [Data Security & Privacy](#data-security--privacy)
- [Extending & Customisation](#extending--customisation)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Disclaimer](#disclaimer)
- [References](#references)

---

## Overview

**Anonymisation Reports** is a Flask-based web platform for anonymising sensitive, lived experience texts—such as personal stories, case notes, or health/social care reports. It combines classical NLP (spaCy + regex), AI-powered models (OpenAI GPT, Hugging Face), and global fake data generation (Faker) to replace personal details with realistic but non-identifying alternatives.

This tool is ideal for researchers, academics, and organisations needing to de-identify qualitative data while retaining narrative flow.

---

## Features

- **Multi-level anonymisation**: Choose low, medium, or high intensity
- **Smart fake replacements**: Names, dates, places, addresses, contacts, national IDs, financial, medical, geo-coordinates, and more
- **Locale-aware**: Faker covers all major world regions (Africa, EU, Americas, Asia, Middle East)
- **Deep custom regex anonymisation** for IDs, phone, financial, and more
- **Supports AI models**: GPT (OpenAI), Mistral/Falcon/Llama (Hugging Face)
- **Upload .txt, .docx, .pdf** or paste raw text
- **Modern authentication**: Register, login, dashboard, history, profile, password change
- **Download anonymised reports** as PDF, DOCX, TXT
- **View anonymisation history** for registered users
- **Animated, modern UI** (Bootstrap 5, Material 3 styles)
- **Easy deployment**: Run locally or on any Flask-compatible server

---

## How It Works

1. **User uploads or pastes text** (e.g., a lived experience narrative).
2. **Select anonymisation level** (low/medium/high) and model (spaCy, OpenAI, Hugging Face).
3. **App processes the text**:
   - spaCy NER and Faker: replaces real entities with globally plausible fakes
   - Regex for IDs, contacts, financial/medical info, etc.
   - Optional: uses LLMs for advanced, context-aware anonymisation
4. **User receives anonymised output**.
5. **Registered users** can save, download, or review past reports.

---

## Screenshots

![Anonymisation Reports Dashboard](docs/screenshot_dashboard.png)
![Text Upload and Output](docs/screenshot_anonymise.png)

---

## Setup & Installation

### Requirements

- Python 3.9+
- [pip](https://pip.pypa.io/en/stable/installation/)
- OS: Windows, macOS, or Linux

#### Python dependencies

- Flask
- Flask-Login
- Flask-SQLAlchemy
- spaCy (`en_core_web_sm`)
- Faker
- python-docx
- PyPDF2
- requests
- (Optional) OpenAI / Hugging Face API access

> All dependencies are in `requirements.txt`.

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/anonymisation-reports.git
   cd anonymisation-reports

2. **Create a virtual environment**
    ```bash 
    python -m venv .venv
    source .venv/bin/activate   # (Linux/Mac)
    .venv\Scripts\activate      # (Windows)

3. **Install dependencies**
    ```bash     
    pip install -r requirements.txt

4. **Download the spaCy model**
    ```bash
    python -m spacy download en_core_web_sm

5. **Configure environment variables (optional)**
   - SECRET_KEY: Flask secret key
   - DATABASE_URL: (optional) For custom DB setups

6. **Installation**
   - No extra build step required. The app runs out of the box.

## Running the Application
   ```bash
    flask run
```
By default, the app is available at http://127.0.0.1:5000/.

**Configuration**
API Keys
To use advanced anonymisation models:
- OpenAI: Set your OpenAI API key in your user profile after registration
- Hugging Face: Set your Hugging Face API key in your profile

Guest users can only use the spaCy model for privacy and safety.

**spaCy Model**
- Pre-download the model with python -m spacy download en_core_web_sm (required).

**Advanced Model Usage**
- For best anonymisation, use the spaCy + Faker model (covers most cases automatically).
- OpenAI/Hugging Face models are best for very subtle or context-heavy anonymisation.

### Usage 
**User Authentication**
- Register and log in to save, view, and download reports.
- API keys are stored per user (never shared).

**Anonymisation Levels**
- Low: Only names and main locations
- Medium: Names, locations, organisations, emails, some dates/phones
- High: All entities + deep regex anonymisation of numbers, IDs, medical, finance, geo, social, etc.

**Supported File Types**
- .txt (plain text)
- .docx (Microsoft Word)
- .pdf (requires PyPDF2)

**Viewing & Downloading Reports**
- Registered users see their history (dashboard)
- Download any report as PDF, DOCX, or TXT

**Data Security & Privacy**
- User data is stored securely in a local database (SQLite by default)
- Passwords are hashed (never stored as plain text)
- API keys are user-specific and never exposed to others
- Uploaded files are not saved on disk; only anonymised text and metadata are stored

**Extending & Customisation**
- Entity/regex patterns: Add more to anonymise.py as needed for your domain/country
- UI customisation: Edit templates in templates/ and static files in static/
- Database: Replace SQLite with PostgreSQL or MySQL by changing the SQLALCHEMY_DATABASE_URI
- Model integrations: Extend with more models or custom prompts

**Troubleshooting**
- Model not found: Ensure en_core_web_sm is downloaded (python -m spacy download en_core_web_sm)
- File upload fails: Check file size/type. PDFs require PyPDF2.
- API rate limit: If using OpenAI/HF, ensure you haven’t exceeded your quota.
- IntegrityError (register): Email or username already exists.
- Cannot save as guest: Only registered users can save/download history.

License
This project is released under the MIT License. See LICENSE for details.

## Disclaimer 
- This tool is designed for research, prototyping, and safe anonymisation. It makes best-effort replacements, but cannot guarantee 100% anonymity or privacy for all use cases.
- Do not use with extremely sensitive material without additional review.
- For compliance with GDPR or HIPAA, ensure anonymisation requirements are fully tested in your context.

## References
- spaCy Named Entity Recognition
- Faker documentation
- OpenAI API
- Hugging Face Inference API