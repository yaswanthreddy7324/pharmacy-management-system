"""
app.py — Smart Pharmacy Management System (Flask web app)

Routes are grouped by concern: auth, dashboard, medicines, patients,
prescriptions, billing, reports, and user management. Role-based access
is enforced with the @login_required and @role_required decorators.
"""

import functools
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_connection, initialize_database

app = Flask(__name__)
import os
app.secret_key = os.environ.get("SECRET_KEY")


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def role_required(*roles):
    def decorator(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if session.get("role") not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


@app.context_processor
def inject_user():
    return {
        "current_user": {
            "full_name": session.get("full_name"),
            "role": session.get("role"),
            "username": session.get("username"),
        } if "user_id" in session else None
    }


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ? AND is_active = 1", (username,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["user_id"]
            session["username"] = user["username"]
            session["full_name"] = user["full_name"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@app.route("/")
@login_required
def dashboard():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS c FROM medicines")
    medicine_count = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM medicines WHERE quantity <= reorder_level")
    low_stock_count = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM prescriptions WHERE status = 'Pending'")
    pending_count = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c, COALESCE(SUM(total_amount), 0) AS total FROM bills WHERE date(created_at) = date('now')")
    today_row = cur.fetchone()

    cur.execute(
        """SELECT b.bill_id, pt.name AS patient_name, b.total_amount, b.created_at
           FROM bills b JOIN patients pt ON pt.patient_id = b.patient_id
           ORDER BY b.created_at DESC LIMIT 5"""
    )
    recent_bills = cur.fetchall()
    conn.close()

    return render_template(
        "dashboard.html",
        medicine_count=medicine_count,
        low_stock_count=low_stock_count,
        pending_count=pending_count,
        today_bill_count=today_row["c"],
        today_revenue=today_row["total"],
        recent_bills=recent_bills,
    )


# ---------------------------------------------------------------------------
# Medicines
# ---------------------------------------------------------------------------

@app.route("/medicines")
@login_required
def medicines():
    conn = get_connection()
    cur = conn.cursor()
    q = request.args.get("q", "").strip()
    if q:
        cur.execute("SELECT * FROM medicines WHERE name LIKE ? ORDER BY name", (f"%{q}%",))
    else:
        cur.execute("SELECT * FROM medicines ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return render_template("medicines.html", medicines=rows, query=q)


@app.route("/medicines/add", methods=["GET", "POST"])
@role_required("Admin")
def add_medicine():
    if request.method == "POST":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO medicines (name, manufacturer, category, batch_no, expiry_date,
                                       quantity, unit_price, reorder_level)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                request.form["name"].strip(),
                request.form.get("manufacturer", "").strip(),
                request.form.get("category", "").strip(),
                request.form.get("batch_no", "").strip(),
                request.form.get("expiry_date") or None,
                int(request.form.get("quantity") or 0),
                float(request.form.get("unit_price") or 0),
                int(request.form.get("reorder_level") or 10),
            ),
        )
        conn.commit()
        conn.close()
        flash(f"Added \u201c{request.form['name'].strip()}\u201d to inventory.", "success")
        return redirect(url_for("medicines"))

    return render_template("medicine_form.html", medicine=None)


@app.route("/medicines/<int:medicine_id>/edit", methods=["GET", "POST"])
@role_required("Admin")
def edit_medicine(medicine_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM medicines WHERE medicine_id = ?", (medicine_id,))
    medicine = cur.fetchone()
    if not medicine:
        conn.close()
        abort(404)

    if request.method == "POST":
        cur.execute(
            """UPDATE medicines SET name=?, manufacturer=?, category=?, batch_no=?, expiry_date=?,
               quantity=?, unit_price=?, reorder_level=?, updated_at=datetime('now')
               WHERE medicine_id=?""",
            (
                request.form["name"].strip(),
                request.form.get("manufacturer", "").strip(),
                request.form.get("category", "").strip(),
                request.form.get("batch_no", "").strip(),
                request.form.get("expiry_date") or None,
                int(request.form.get("quantity") or 0),
                float(request.form.get("unit_price") or 0),
                int(request.form.get("reorder_level") or 10),
                medicine_id,
            ),
        )
        conn.commit()
        conn.close()
        flash("Medicine updated.", "success")
        return redirect(url_for("medicines"))

    conn.close()
    return render_template("medicine_form.html", medicine=medicine)


@app.route("/medicines/<int:medicine_id>/delete", methods=["POST"])
@role_required("Admin")
def delete_medicine(medicine_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM medicines WHERE medicine_id = ?", (medicine_id,))
    conn.commit()
    conn.close()
    flash("Medicine deleted.", "success")
    return redirect(url_for("medicines"))


# ---------------------------------------------------------------------------
# Patients
# ---------------------------------------------------------------------------

@app.route("/patients")
@login_required
def patients():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM patients ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return render_template("patients.html", patients=rows)


@app.route("/patients/add", methods=["GET", "POST"])
@login_required
def add_patient():
    if request.method == "POST":
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO patients (name, age, gender, phone) VALUES (?, ?, ?, ?)",
            (
                request.form["name"].strip(),
                int(request.form["age"]) if request.form.get("age") else None,
                request.form.get("gender", "").strip(),
                request.form.get("phone", "").strip(),
            ),
        )
        conn.commit()
        patient_id = cur.lastrowid
        conn.close()
        flash("Patient registered.", "success")

        next_action = request.form.get("next")
        if next_action == "prescribe":
            return redirect(url_for("add_prescription", patient_id=patient_id))
        return redirect(url_for("patients"))

    preselect_prescribe = request.args.get("prescribe") == "1"
    return render_template("patient_form.html", preselect_prescribe=preselect_prescribe)


# ---------------------------------------------------------------------------
# Prescriptions
# ---------------------------------------------------------------------------

@app.route("/prescriptions")
@login_required
def prescriptions():
    status_filter = request.args.get("status", "Pending")
    conn = get_connection()
    cur = conn.cursor()
    if status_filter == "All":
        cur.execute(
            """SELECT p.*, pt.name AS patient_name FROM prescriptions p
               JOIN patients pt ON pt.patient_id = p.patient_id
               ORDER BY p.created_at DESC"""
        )
    else:
        cur.execute(
            """SELECT p.*, pt.name AS patient_name FROM prescriptions p
               JOIN patients pt ON pt.patient_id = p.patient_id
               WHERE p.status = ? ORDER BY p.created_at DESC""",
            (status_filter,),
        )
    rows = cur.fetchall()
    conn.close()
    return render_template("prescriptions.html", prescriptions=rows, status_filter=status_filter)


@app.route("/prescriptions/add", methods=["GET", "POST"])
@login_required
def add_prescription():
    conn = get_connection()
    cur = conn.cursor()

    if request.method == "POST":
        patient_id = int(request.form["patient_id"])
        doctor_name = request.form.get("doctor_name", "").strip()

        cur.execute(
            "INSERT INTO prescriptions (patient_id, doctor_name, created_by) VALUES (?, ?, ?)",
            (patient_id, doctor_name, session["user_id"]),
        )
        prescription_id = cur.lastrowid

        medicine_ids = request.form.getlist("medicine_id[]")
        quantities = request.form.getlist("quantity[]")
        notes = request.form.getlist("dosage_note[]")

        items_added = 0
        for mid, qty, note in zip(medicine_ids, quantities, notes):
            if not mid or not qty:
                continue
            cur.execute(
                """INSERT INTO prescription_items (prescription_id, medicine_id, quantity, dosage_note)
                   VALUES (?, ?, ?, ?)""",
                (prescription_id, int(mid), int(qty), note.strip()),
            )
            items_added += 1

        conn.commit()
        conn.close()

        if items_added == 0:
            flash("Prescription created, but no medicines were added yet — add them from the prescription page.", "warning")
        else:
            flash(f"Prescription #{prescription_id} created with {items_added} item(s).", "success")
        return redirect(url_for("view_prescription", prescription_id=prescription_id))

    cur.execute("SELECT * FROM patients ORDER BY name")
    patient_list = cur.fetchall()
    cur.execute("SELECT * FROM medicines ORDER BY name")
    medicine_list = cur.fetchall()
    conn.close()

    preselect_patient = request.args.get("patient_id", type=int)
    return render_template("prescription_form.html", patients=patient_list, medicines=medicine_list, preselect_patient=preselect_patient)


@app.route("/prescriptions/<int:prescription_id>")
@login_required
def view_prescription(prescription_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT p.*, pt.name AS patient_name, pt.age, pt.gender, pt.phone
           FROM prescriptions p JOIN patients pt ON pt.patient_id = p.patient_id
           WHERE p.prescription_id = ?""",
        (prescription_id,),
    )
    presc = cur.fetchone()
    if not presc:
        conn.close()
        abort(404)

    cur.execute(
        """SELECT pi.*, m.name, m.unit_price, m.quantity AS stock_qty FROM prescription_items pi
           JOIN medicines m ON m.medicine_id = pi.medicine_id
           WHERE pi.prescription_id = ?""",
        (prescription_id,),
    )
    items = cur.fetchall()

    bill = None
    if presc["status"] == "Billed":
        cur.execute("SELECT * FROM bills WHERE prescription_id = ?", (prescription_id,))
        bill = cur.fetchone()

    conn.close()
    return render_template("prescription_detail.html", presc=presc, items=items, bill=bill)


# ---------------------------------------------------------------------------
# Billing
# ---------------------------------------------------------------------------

def calculate_totals(items, discount_percent=0.0, tax_percent=0.0):
    subtotal = sum(it["quantity"] * it["unit_price"] for it in items)
    discount_amount = subtotal * (discount_percent / 100)
    taxable_amount = subtotal - discount_amount
    tax_amount = taxable_amount * (tax_percent / 100)
    total = taxable_amount + tax_amount
    return {
        "subtotal": round(subtotal, 2),
        "discount_amount": round(discount_amount, 2),
        "taxable_amount": round(taxable_amount, 2),
        "tax_amount": round(tax_amount, 2),
        "total": round(total, 2),
    }


@app.route("/prescriptions/<int:prescription_id>/bill", methods=["GET", "POST"])
@login_required
def generate_bill(prescription_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT p.*, pt.name AS patient_name FROM prescriptions p
           JOIN patients pt ON pt.patient_id = p.patient_id WHERE p.prescription_id = ?""",
        (prescription_id,),
    )
    presc = cur.fetchone()
    if not presc:
        conn.close()
        abort(404)

    if presc["status"] != "Pending":
        conn.close()
        flash(f"This prescription is already \u2018{presc['status']}\u2019 and cannot be billed again.", "error")
        return redirect(url_for("view_prescription", prescription_id=prescription_id))

    cur.execute(
        """SELECT pi.*, m.name, m.unit_price, m.quantity AS stock_qty FROM prescription_items pi
           JOIN medicines m ON m.medicine_id = pi.medicine_id WHERE pi.prescription_id = ?""",
        (prescription_id,),
    )
    items = cur.fetchall()

    if not items:
        conn.close()
        flash("This prescription has no medicine items to bill.", "error")
        return redirect(url_for("view_prescription", prescription_id=prescription_id))

    if request.method == "POST":
        discount_percent = float(request.form.get("discount_percent") or 0)
        tax_percent = float(request.form.get("tax_percent") or 0)
        payment_method = request.form.get("payment_method", "Cash")

        for it in items:
            if it["stock_qty"] < it["quantity"]:
                conn.close()
                flash(f"Insufficient stock for {it['name']} (have {it['stock_qty']}, need {it['quantity']}).", "error")
                return redirect(url_for("view_prescription", prescription_id=prescription_id))

        totals = calculate_totals(items, discount_percent, tax_percent)

        cur.execute(
            """INSERT INTO bills (prescription_id, patient_id, generated_by, subtotal,
                                   discount_percent, tax_percent, total_amount, payment_method)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                prescription_id, presc["patient_id"], session["user_id"], totals["subtotal"],
                discount_percent, tax_percent, totals["total"], payment_method,
            ),
        )
        bill_id = cur.lastrowid

        for it in items:
            line_total = round(it["quantity"] * it["unit_price"], 2)
            cur.execute(
                """INSERT INTO bill_items (bill_id, medicine_id, medicine_name, quantity, unit_price, line_total)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (bill_id, it["medicine_id"], it["name"], it["quantity"], it["unit_price"], line_total),
            )
            cur.execute(
                "UPDATE medicines SET quantity = quantity - ?, updated_at=datetime('now') WHERE medicine_id = ?",
                (it["quantity"], it["medicine_id"]),
            )

        cur.execute("UPDATE prescriptions SET status = 'Billed' WHERE prescription_id = ?", (prescription_id,))
        conn.commit()
        conn.close()
        flash(f"Bill #{bill_id} generated.", "success")
        return redirect(url_for("view_bill", bill_id=bill_id))

    conn.close()
    totals_preview = calculate_totals(items)
    return render_template("billing_form.html", presc=presc, items=items, totals=totals_preview)


@app.route("/bills")
@login_required
def bills():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT b.bill_id, pt.name AS patient_name, b.total_amount, b.payment_method, b.created_at
           FROM bills b JOIN patients pt ON pt.patient_id = b.patient_id
           ORDER BY b.created_at DESC"""
    )
    rows = cur.fetchall()
    conn.close()
    return render_template("bills.html", bills=rows)


@app.route("/bills/<int:bill_id>")
@login_required
def view_bill(bill_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """SELECT b.*, pt.name AS patient_name, u.full_name AS staff_name
           FROM bills b
           JOIN patients pt ON pt.patient_id = b.patient_id
           JOIN users u ON u.user_id = b.generated_by
           WHERE b.bill_id = ?""",
        (bill_id,),
    )
    bill = cur.fetchone()
    if not bill:
        conn.close()
        abort(404)
    cur.execute("SELECT * FROM bill_items WHERE bill_id = ?", (bill_id,))
    items = cur.fetchall()
    conn.close()

    discount_amount = round(bill["subtotal"] * (bill["discount_percent"] / 100), 2)
    taxable_amount = bill["subtotal"] - discount_amount
    tax_amount = round(taxable_amount * (bill["tax_percent"] / 100), 2)

    return render_template(
        "bill_receipt.html", bill=bill, items=items,
        discount_amount=discount_amount, tax_amount=tax_amount,
    )


# ---------------------------------------------------------------------------
# Reports (Admin only)
# ---------------------------------------------------------------------------

@app.route("/reports")
@role_required("Admin")
def reports():
    start = request.args.get("start", "")
    end = request.args.get("end", "")

    query = "SELECT * FROM bills WHERE 1=1"
    params = []
    if start:
        query += " AND date(created_at) >= date(?)"
        params.append(start)
    if end:
        query += " AND date(created_at) <= date(?)"
        params.append(end)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    bill_rows = cur.fetchall()
    total_revenue = sum(b["total_amount"] for b in bill_rows)
    bill_count = len(bill_rows)
    avg_bill = total_revenue / bill_count if bill_count else 0

    top_query = """
        SELECT bi.medicine_name, SUM(bi.quantity) AS total_qty, SUM(bi.line_total) AS total_sales
        FROM bill_items bi JOIN bills b ON b.bill_id = bi.bill_id WHERE 1=1
    """
    if start:
        top_query += " AND date(b.created_at) >= date(?)"
    if end:
        top_query += " AND date(b.created_at) <= date(?)"
    top_query += " GROUP BY bi.medicine_name ORDER BY total_qty DESC LIMIT 5"
    cur.execute(top_query, params)
    top_medicines = cur.fetchall()

    cur.execute("SELECT payment_method, COUNT(*) AS cnt, SUM(total_amount) AS total FROM bills GROUP BY payment_method")
    by_payment = cur.fetchall()

    cur.execute("SELECT * FROM medicines WHERE quantity <= reorder_level ORDER BY quantity")
    low_stock = cur.fetchall()
    conn.close()

    return render_template(
        "reports.html", bill_count=bill_count, total_revenue=total_revenue, avg_bill=avg_bill,
        top_medicines=top_medicines, by_payment=by_payment, low_stock=low_stock,
        start=start, end=end,
    )


# ---------------------------------------------------------------------------
# User management (Admin only)
# ---------------------------------------------------------------------------

@app.route("/users")
@role_required("Admin")
def users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users ORDER BY user_id")
    rows = cur.fetchall()
    conn.close()
    return render_template("users.html", users=rows)


@app.route("/users/add", methods=["GET", "POST"])
@role_required("Admin")
def add_user():
    if request.method == "POST":
        username = request.form["username"].strip()
        full_name = request.form["full_name"].strip()
        role = request.form["role"]
        password = request.form["password"]

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
                (username, generate_password_hash(password), full_name, role),
            )
            conn.commit()
            flash(f"User \u201c{username}\u201d created with role {role}.", "success")
            return redirect(url_for("users"))
        except Exception:
            flash("Could not create user \u2014 username may already be taken.", "error")
        finally:
            conn.close()

    return render_template("user_form.html")


@app.route("/users/<int:user_id>/deactivate", methods=["POST"])
@role_required("Admin")
def deactivate_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_active = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash("User deactivated.", "success")
    return redirect(url_for("users"))


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(403)
def forbidden(e):
    return render_template("error.html", code=403, message="You don\u2019t have permission to view this page."), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="That page doesn\u2019t exist."), 404


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=5000, debug=True)
