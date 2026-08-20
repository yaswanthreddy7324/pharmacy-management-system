# 💊 Meridian Pharmacy – Smart Pharmacy Management System

<p align="center">
  <strong>A full-stack web-based pharmacy management system built with Python Flask and SQLite.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-Web%20Framework-black?logo=flask" alt="Flask">
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white" alt="HTML5">
  <img src="https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white" alt="CSS3">
  <img src="https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black" alt="JavaScript">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

---

## 📌 Project Overview

**Meridian Pharmacy** is a web-based Pharmacy Management System designed to simplify and digitize common pharmacy operations.

The application provides a centralized platform for managing medicines, patients, prescriptions, billing, users, and reports through an easy-to-use web interface.

The system is built using **Python Flask** for the backend, **SQLite** for data storage, and **HTML/CSS/JavaScript** for the frontend.

---

## ✨ Features

### 🔐 Authentication & User Management
- Secure user login
- User management
- Session-based authentication
- Role-based access functionality

### 💊 Medicine Management
- Add medicines
- Update medicine information
- Delete medicines
- Search medicines
- Track medicine stock
- Manage medicine details

### 👨‍⚕️ Patient Management
- Add patient records
- Update patient information
- View patient details
- Search patients
- Maintain patient history

### 📋 Prescription Management
- Create prescriptions
- View prescriptions
- Manage prescription details
- Connect prescriptions with patients and medicines

### 🧾 Billing System
- Create customer bills
- Add medicines to bills
- Calculate billing totals
- Generate bill receipts
- Maintain billing records

### 📊 Reports & Dashboard
- Pharmacy dashboard
- Medicine inventory overview
- Patient statistics
- Billing information
- Pharmacy reports

### ⚠️ Error Handling
- Custom error pages
- Form validation
- User-friendly error messages

---

## 🛠️ Technology Stack

| Technology | Purpose |
|------------|---------|
| 🐍 Python | Backend programming |
| 🌐 Flask | Web application framework |
| 🗄️ SQLite | Database |
| 🧱 HTML5 | Page structure |
| 🎨 CSS3 | Styling |
| ⚡ JavaScript | Client-side functionality |
| 🔧 Git | Version control |
| 🐙 GitHub | Source code hosting |

---

## 🏗️ Project Architecture

```text
pharmacy-management-system/
│
├── app.py                  # Flask application
├── database.py             # Database operations
├── requirements.txt        # Python dependencies
├── pharmacy.db             # Local SQLite database
├── README.md               # Project documentation
├── .gitignore              # Git ignored files
│
├── static/
│   └── style.css           # Application styles
│
└── templates/
    ├── base.html
    ├── login.html
    ├── dashboard.html
    ├── medicines.html
    ├── medicine_form.html
    ├── patients.html
    ├── patient_form.html
    ├── prescriptions.html
    ├── prescription_form.html
    ├── prescription_detail.html
    ├── bills.html
    ├── billing_form.html
    ├── bill_receipt.html
    ├── users.html
    ├── user_form.html
    ├── reports.html
    └── error.html
