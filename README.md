# Meridian Pharmacy — Smart Pharmacy Management System (Web Edition)

A full website (not just CLI) built with **Python (Flask)** and **SQLite**, covering
medicine inventory, patient records, prescriptions, and billing — with a login
screen and role-based access control (Admin / Pharmacist).

## Run it

```bash
pip install -r requirements.txt
python3 app.py
```

Then open **http://127.0.0.1:5000** in your browser.

Default login (created automatically on first run):
```
username: admin
password: admin123
```
Use the Admin account to create Pharmacist accounts under **Staff Accounts**.

## Architecture

| File / folder        | Responsibility |
|-----------------------|----------------|
| `app.py`               | Flask routes, session-based auth, RBAC decorators, billing math |
| `database.py`          | SQLite schema, connection helper, seed admin account |
| `templates/`           | Jinja2 HTML templates (one per page) |
| `static/style.css`     | The full design system — one stylesheet, no framework |
| `requirements.txt`     | Python dependencies |

The app follows Flask's standard MVC-ish split: `database.py` is the data layer,
route functions in `app.py` are the controllers, and `templates/*.html` are the views.
Business logic (bill totals: subtotal → discount → tax → total) lives in
`calculate_totals()` in `app.py`.

## Roles & permissions

- **Admin** — everything, plus: add/edit medicines, manage staff accounts, view reports.
- **Pharmacist** — register patients, write prescriptions, generate bills, view inventory (read-only).

Every sensitive route is wrapped in `@role_required("Admin")` or `@login_required`
in `app.py`, so permissions are enforced on the server regardless of what the UI shows.

## Pages

- `/login` — sign in
- `/` — dashboard with live stats (inventory count, low-stock alerts, pending prescriptions, today's revenue)
- `/medicines` — inventory list + search; `/medicines/add`, `/medicines/<id>/edit` (Admin only)
- `/patients` — patient list; `/patients/add`
- `/prescriptions` — pending/billed/all queue; `/prescriptions/add` (dynamic multi-medicine form); `/prescriptions/<id>` detail
- `/prescriptions/<id>/bill` — generate a bill with live discount/tax preview, checks stock, deducts inventory
- `/bills`, `/bills/<id>` — bill history and a printable receipt
- `/reports` — sales summary, top-selling medicines, revenue by payment method, low-stock report (Admin only)
- `/users` — staff account management (Admin only)

## Notes

- `pharmacy.db` is created automatically on first run in the project folder. Delete it to reset all data.
- Passwords are hashed with Werkzeug's `generate_password_hash` (PBKDF2) — safe for real use, unlike a plain SHA-256 demo hash.
- The Flask dev server (`app.run(debug=True)`) is fine for local testing. For real deployment, run behind a production WSGI server (e.g. `gunicorn app:app`) and set a proper `app.secret_key` via an environment variable instead of the hardcoded dev value in `app.py`.
