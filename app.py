#!/usr/bin/env python3
"""
Registry Case Management System
Flask web application for managing case records.
Accessible to all devices on the same network.
"""
import os
import sqlite3
from flask import (
    Flask, render_template, request, redirect, url_for, flash, g
)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.jinja_env.globals['enumerate'] = enumerate

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "registry.db")

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query_db(sql, args=(), one=False):
    cur = get_db().execute(sql, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def distinct_values(column, table="records"):
    """Return sorted non-empty distinct values for a column."""
    rows = query_db(
        f"SELECT DISTINCT {column} FROM {table} "
        f"WHERE {column} IS NOT NULL AND {column} != '' "
        f"ORDER BY {column}"
    )
    return [r[0] for r in rows]


# ---------------------------------------------------------------------------
# Form field definitions (columns handled in the add/edit form)
# ---------------------------------------------------------------------------

FORM_FIELDS = [
    # identity
    "first_name", "father_name", "last_name", "mother_name",
    "gender", "national_id", "family_book_number",
    "birth_day", "birth_month", "birth_year", "blood_type",
    # contact
    "phone", "province", "address", "housing_type", "rent_amount",
    # case
    "status", "case_type", "cause_number", "record_status",
    "arrest_day", "arrest_month", "arrest_year",
    "arrest_place", "arrest_authority", "arrest_reason", "arrest_causer",
    # release / death
    "release_day", "release_month", "release_year",
    "death_day", "death_month", "death_year", "death_place",
    # family
    "marital", "spouse_name", "spouse_phone",
    "has_kids", "kids_count", "kids_under_18_count",
    "guardian_name", "guardian_relation", "guardian_phone",
    "breadwinner", "breadwinner_job",
    # education & employment
    "education", "edu_type", "edu_specialization", "edu_university",
    "employment", "profession", "employer",
    # health
    "chronic", "diseases", "has_hypertension", "has_diabetes",
    "other_diseases", "has_special_needs", "special_needs_details",
    # evidence
    "source_type", "collection_date", "collector_name",
    "verification_status", "evidence_level", "evidence_sources_count",
    "reporter_name", "reporter_relation", "reporter_phone", "reporter_id",
    "informant_consent",
    # notes
    "notes",
]

INT_FIELDS = {
    "birth_day", "birth_month", "birth_year",
    "arrest_day", "arrest_month", "arrest_year",
    "release_day", "release_month", "release_year",
    "death_day", "death_month", "death_year",
    "kids_count", "kids_under_18_count",
    "has_hypertension", "has_diabetes", "has_special_needs",
    "informant_consent", "evidence_sources_count",
}


def form_to_dict():
    """Extract form data into a dict, converting int fields."""
    data = {}
    for field in FORM_FIELDS:
        val = request.form.get(field, "").strip()
        if field in INT_FIELDS:
            data[field] = int(val) if val else None
        else:
            data[field] = val if val else None
    return data


def get_form_options():
    """Get dropdown options for the record form."""
    return dict(
        provinces=distinct_values("province"),
        housing_types=distinct_values("housing_type"),
        case_types=distinct_values("case_type"),
        maritals=distinct_values("marital"),
        educations=distinct_values("education"),
        verification_statuses=distinct_values("verification_status"),
        evidence_levels=distinct_values("evidence_level"),
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    stats = {
        "total": query_db("SELECT COUNT(*) c FROM records", one=True)["c"],
        "deceased": query_db(
            "SELECT COUNT(*) c FROM records WHERE status='deceased'", one=True
        )["c"],
        "enforced": query_db(
            "SELECT COUNT(*) c FROM records WHERE status='enforced'", one=True
        )["c"],
        "survivor": query_db(
            "SELECT COUNT(*) c FROM records WHERE status='survivor'", one=True
        )["c"],
        "verified": query_db(
            "SELECT COUNT(*) c FROM records WHERE verification_status IS NOT NULL "
            "AND verification_status != '' AND verification_status != 'Unverified'",
            one=True,
        )["c"],
        "unverified": query_db(
            "SELECT COUNT(*) c FROM records WHERE verification_status IS NULL "
            "OR verification_status = '' OR verification_status = 'Unverified'",
            one=True,
        )["c"],
        "draft": query_db(
            "SELECT COUNT(*) c FROM records WHERE record_status='draft'", one=True
        )["c"],
        "provinces": query_db(
            "SELECT COUNT(DISTINCT province) c FROM records "
            "WHERE province IS NOT NULL AND province != ''",
            one=True,
        )["c"],
    }

    by_province = query_db(
        "SELECT province AS name, COUNT(*) AS count FROM records "
        "GROUP BY province ORDER BY count DESC"
    )
    by_year = query_db(
        "SELECT arrest_year AS year, COUNT(*) AS count FROM records "
        "WHERE arrest_year IS NOT NULL AND arrest_year > 0 "
        "GROUP BY arrest_year ORDER BY arrest_year DESC"
    )

    recent = query_db(
        "SELECT id, first_name, last_name, status, created_at FROM records "
        "ORDER BY id DESC LIMIT 10"
    )

    return render_template(
        "dashboard.html", stats=stats, by_province=by_province,
        by_year=by_year, recent=recent,
    )


@app.route("/records")
def records_list():
    page = request.args.get("page", 1, type=int)
    per_page = 50

    # Collect active filters
    filter_keys = [
        "q", "status", "province", "gender", "verification_status",
        "arrest_year", "record_status", "evidence_level", "marital",
        "case_type", "education",
    ]
    filters = {k: request.args.get(k, "").strip() for k in filter_keys}

    # Build WHERE clause
    conditions = []
    params = []

    if filters["q"]:
        conditions.append(
            "(first_name || ' ' || father_name || ' ' || last_name LIKE ? "
            "OR national_id LIKE ? OR phone LIKE ?)"
        )
        q = f"%{filters['q']}%"
        params.extend([q, q, q])

    for col in [
        "status", "province", "gender", "verification_status",
        "record_status", "evidence_level", "marital", "case_type", "education",
    ]:
        if filters[col]:
            conditions.append(f"{col} = ?")
            params.append(filters[col])

    if filters["arrest_year"]:
        conditions.append("arrest_year = ?")
        params.append(int(filters["arrest_year"]))

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    total = query_db(f"SELECT COUNT(*) c FROM records {where}", params, one=True)["c"]
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, total_pages)
    offset = (page - 1) * per_page

    records = query_db(
        f"SELECT id, first_name, father_name, last_name, national_id, gender, "
        f"province, status, arrest_year, verification_status, record_status "
        f"FROM records {where} ORDER BY id DESC LIMIT ? OFFSET ?",
        params + [per_page, offset],
    )

    filter_options = {
        "statuses": distinct_values("status"),
        "provinces": distinct_values("province"),
        "genders": distinct_values("gender"),
        "verification_statuses": distinct_values("verification_status"),
        "record_statuses": distinct_values("record_status"),
        "evidence_levels": distinct_values("evidence_level"),
        "maritals": distinct_values("marital"),
        "case_types": distinct_values("case_type"),
        "educations": distinct_values("education"),
    }

    return render_template(
        "records.html",
        records=records,
        total=total,
        page=page,
        total_pages=total_pages,
        filters=filters,
        filter_options=filter_options,
    )


@app.route("/records/add", methods=["GET", "POST"])
def record_add():
    if request.method == "POST":
        data = form_to_dict()
        cols = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        try:
            db = get_db()
            db.execute(
                f"INSERT INTO records ({cols}) VALUES ({placeholders})",
                list(data.values()),
            )
            db.commit()
            flash("تم إضافة الحالة بنجاح", "success")
            return redirect(url_for("records_list"))
        except Exception as e:
            flash(f"خطأ: {e}", "danger")

    opts = get_form_options()
    return render_template("record_form.html", record=None, **opts)


@app.route("/records/<int:record_id>")
def record_view(record_id):
    record = query_db("SELECT * FROM records WHERE id = ?", [record_id], one=True)
    if not record:
        flash("السجل غير موجود", "warning")
        return redirect(url_for("records_list"))
    return render_template("record_view.html", record=record)


@app.route("/records/<int:record_id>/edit", methods=["GET", "POST"])
def record_edit(record_id):
    record = query_db("SELECT * FROM records WHERE id = ?", [record_id], one=True)
    if not record:
        flash("السجل غير موجود", "warning")
        return redirect(url_for("records_list"))

    if request.method == "POST":
        data = form_to_dict()
        set_clause = ", ".join(f"{k} = ?" for k in data.keys())
        try:
            db = get_db()
            db.execute(
                f"UPDATE records SET {set_clause} WHERE id = ?",
                list(data.values()) + [record_id],
            )
            db.commit()
            flash("تم تحديث السجل بنجاح", "success")
            return redirect(url_for("record_view", record_id=record_id))
        except Exception as e:
            flash(f"خطأ: {e}", "danger")
            record = query_db(
                "SELECT * FROM records WHERE id = ?", [record_id], one=True
            )

    opts = get_form_options()
    return render_template("record_form.html", record=record, **opts)


@app.route("/records/<int:record_id>/delete", methods=["POST"])
def record_delete(record_id):
    try:
        db = get_db()
        db.execute("DELETE FROM records WHERE id = ?", [record_id])
        db.commit()
        flash("تم حذف السجل", "success")
    except Exception as e:
        flash(f"خطأ: {e}", "danger")
    return redirect(url_for("records_list"))


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  سجل الحالات - Registry Case Management")
    print("=" * 50)
    print(f"  Database: {DB_PATH}")
    print(f"  Access from this device:    http://localhost:5000")
    print(f"  Access from other devices:  http://<this-ip>:5000")
    print("=" * 50 + "\n")

    app.run(host="0.0.0.0", port=5000, debug=True)
