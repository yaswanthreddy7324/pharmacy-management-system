"""
database.py — SQLite schema, connection helper, and seed data.
"""

import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).parent / "pharmacy.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name     TEXT NOT NULL,
            role          TEXT NOT NULL CHECK(role IN ('Admin', 'Pharmacist')),
            is_active     INTEGER NOT NULL DEFAULT 1,
            created_at    TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS medicines (
            medicine_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            manufacturer  TEXT,
            category      TEXT,
            batch_no      TEXT,
            expiry_date   TEXT,
            quantity      INTEGER NOT NULL DEFAULT 0,
            unit_price    REAL NOT NULL DEFAULT 0.0,
            reorder_level INTEGER NOT NULL DEFAULT 10,
            created_at    TEXT DEFAULT (datetime('now')),
            updated_at    TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS patients (
            patient_id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL,
            age          INTEGER,
            gender       TEXT,
            phone        TEXT,
            created_at   TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS prescriptions (
            prescription_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id      INTEGER NOT NULL,
            doctor_name     TEXT,
            created_by      INTEGER NOT NULL,
            status          TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','Billed','Cancelled')),
            created_at      TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS prescription_items (
            item_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id  INTEGER NOT NULL,
            medicine_id      INTEGER NOT NULL,
            quantity         INTEGER NOT NULL,
            dosage_note      TEXT,
            FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id),
            FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id)
        );

        CREATE TABLE IF NOT EXISTS bills (
            bill_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            prescription_id  INTEGER,
            patient_id       INTEGER NOT NULL,
            generated_by     INTEGER NOT NULL,
            subtotal         REAL NOT NULL,
            discount_percent REAL NOT NULL DEFAULT 0,
            tax_percent      REAL NOT NULL DEFAULT 0,
            total_amount     REAL NOT NULL,
            payment_method   TEXT DEFAULT 'Cash',
            created_at       TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (prescription_id) REFERENCES prescriptions(prescription_id),
            FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
            FOREIGN KEY (generated_by) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS bill_items (
            bill_item_id  INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_id       INTEGER NOT NULL,
            medicine_id   INTEGER NOT NULL,
            medicine_name TEXT NOT NULL,
            quantity      INTEGER NOT NULL,
            unit_price    REAL NOT NULL,
            line_total    REAL NOT NULL,
            FOREIGN KEY (bill_id) REFERENCES bills(bill_id),
            FOREIGN KEY (medicine_id) REFERENCES medicines(medicine_id)
        );
        """
    )

    cur.execute("SELECT COUNT(*) AS c FROM users")
    if cur.fetchone()["c"] == 0:
        cur.execute(
            "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            ("admin", generate_password_hash("admin123"), "System Administrator", "Admin"),
        )

    conn.commit()
    conn.close()
