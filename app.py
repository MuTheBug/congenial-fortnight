#!/usr/bin/env python3
"""
Registry Case Management System
Flask web application for managing case records.
Accessible to all devices on the same network.
"""
import os
import uuid
import sqlite3
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, g, send_from_directory, abort,
)
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.jinja_env.globals['enumerate'] = enumerate

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DB_PATH     = os.path.join(BASE_DIR, "registry.db")
UPLOAD_DIR  = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXT = {"jpg", "jpeg", "png", "gif", "webp", "pdf"}
MAX_MB      = 20

app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024

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
    rows = query_db(
        f"SELECT DISTINCT {column} FROM {table} "
        f"WHERE {column} IS NOT NULL AND {column} != '' "
        f"ORDER BY {column}"
    )
    return [r[0] for r in rows]


# ---------------------------------------------------------------------------
# File upload helpers
# ---------------------------------------------------------------------------

def allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def record_upload_dir(record_id):
    d = os.path.join(UPLOAD_DIR, "records", str(record_id))
    os.makedirs(d, exist_ok=True)
    return d


def save_single_file(file_obj, record_id, slot):
    """Save one file for a slot ('photo' or 'document'). Returns relative path."""
    if not file_obj or not file_obj.filename:
        return None
    if not allowed(file_obj.filename):
        raise ValueError(f"نوع الملف غير مسموح به: {file_obj.filename}")
    ext  = file_obj.filename.rsplit(".", 1)[1].lower()
    name = f"{slot}.{ext}"
    d    = record_upload_dir(record_id)
    file_obj.save(os.path.join(d, name))
    return f"records/{record_id}/{name}"


def save_evidence_files(files, record_id):
    """Save multiple evidence files. Returns list of (filename, original_name)."""
    saved = []
    for f in files:
        if not f or not f.filename:
            continue
        if not allowed(f.filename):
            raise ValueError(f"نوع الملف غير مسموح به: {f.filename}")
        ext      = f.filename.rsplit(".", 1)[1].lower()
        uid_name = f"{uuid.uuid4().hex}.{ext}"
        d        = record_upload_dir(record_id)
        f.save(os.path.join(d, uid_name))
        saved.append((f"records/{record_id}/{uid_name}", secure_filename(f.filename)))
    return saved


def delete_upload(relative_path):
    if not relative_path:
        return
    full = os.path.join(UPLOAD_DIR, relative_path)
    if os.path.isfile(full):
        os.remove(full)


# ---------------------------------------------------------------------------
# Form field definitions
# ---------------------------------------------------------------------------

FORM_FIELDS = [
    "first_name", "father_name", "last_name", "mother_name",
    "gender", "national_id", "family_book_number",
    "birth_day", "birth_month", "birth_year", "blood_type",
    "phone", "province", "address", "housing_type", "rent_amount",
    "status", "case_type", "cause_number", "record_status",
    "arrest_day", "arrest_month", "arrest_year",
    "arrest_place", "arrest_authority", "arrest_reason", "arrest_causer",
    "release_day", "release_month", "release_year",
    "death_day", "death_month", "death_year", "death_place",
    "marital", "spouse_name", "spouse_phone",
    "has_kids", "kids_count", "kids_under_18_count",
    "guardian_name", "guardian_relation", "guardian_phone",
    "breadwinner", "breadwinner_job",
    "education", "edu_type", "edu_specialization", "edu_university",
    "employment", "profession", "employer",
    "chronic", "diseases", "has_hypertension", "has_diabetes",
    "other_diseases", "has_special_needs", "special_needs_details",
    "source_type", "collection_date", "collector_name",
    "verification_status", "evidence_level", "evidence_sources_count",
    "reporter_name", "reporter_relation", "reporter_phone", "reporter_id",
    "informant_consent",
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
    data = {}
    for field in FORM_FIELDS:
        val = request.form.get(field, "").strip()
        if field in INT_FIELDS:
            data[field] = int(val) if val else None
        else:
            data[field] = val if val else None
    return data


def get_form_options():
    return dict(
        provinces=distinct_values("province"),
        housing_types=distinct_values("housing_type"),
        case_types=distinct_values("case_type"),
        maritals=distinct_values("marital"),
        educations=distinct_values("education"),
        verification_statuses=distinct_values("verification_status"),
        evidence_levels=distinct_values("evidence_level"),
    )


def handle_photo_uploads(record_id, record=None):
    """Process photo/document/evidence file uploads for a record."""
    db = get_db()
    errors = []

    # ---- Personal photo ----
    personal = request.files.get("photo_file")
    if personal and personal.filename:
        try:
            rel = save_single_file(personal, record_id, "photo")
            if rel:
                if record and record["photo_path"]:
                    delete_upload(record["photo_path"])
                db.execute("UPDATE records SET photo_path=? WHERE id=?", [rel, record_id])
        except ValueError as e:
            errors.append(str(e))

    # ---- ID document photo ----
    doc = request.files.get("document_file")
    if doc and doc.filename:
        try:
            rel = save_single_file(doc, record_id, "document")
            if rel:
                if record and record["document_path"]:
                    delete_upload(record["document_path"])
                db.execute("UPDATE records SET document_path=? WHERE id=?", [rel, record_id])
        except ValueError as e:
            errors.append(str(e))

    # ---- Evidence photos (multiple) ----
    evidence_files = request.files.getlist("evidence_files")
    if evidence_files:
        try:
            saved = save_evidence_files(evidence_files, record_id)
            for rel_path, orig_name in saved:
                caption = ""
                db.execute(
                    "INSERT INTO record_photos (record_id, photo_type, filename, original_name, caption) "
                    "VALUES (?, 'evidence', ?, ?, ?)",
                    [record_id, rel_path, orig_name, caption],
                )
        except ValueError as e:
            errors.append(str(e))

    if errors:
        for e in errors:
            flash(e, "warning")


# ---------------------------------------------------------------------------
# Routes — file serving
# ---------------------------------------------------------------------------

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    """Serve uploaded files securely."""
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.isfile(filepath):
        abort(404)
    return send_from_directory(UPLOAD_DIR, filename)


# ---------------------------------------------------------------------------
# Routes — records
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    stats = {
        "total":      query_db("SELECT COUNT(*) c FROM records", one=True)["c"],
        "deceased":   query_db("SELECT COUNT(*) c FROM records WHERE status='deceased'", one=True)["c"],
        "enforced":   query_db("SELECT COUNT(*) c FROM records WHERE status='enforced'", one=True)["c"],
        "survivor":   query_db("SELECT COUNT(*) c FROM records WHERE status='survivor'", one=True)["c"],
        "verified":   query_db(
            "SELECT COUNT(*) c FROM records WHERE verification_status IS NOT NULL "
            "AND verification_status != '' AND verification_status != 'Unverified'", one=True)["c"],
        "unverified": query_db(
            "SELECT COUNT(*) c FROM records WHERE verification_status IS NULL "
            "OR verification_status = '' OR verification_status = 'Unverified'", one=True)["c"],
        "draft":      query_db("SELECT COUNT(*) c FROM records WHERE record_status='draft'", one=True)["c"],
        "provinces":  query_db(
            "SELECT COUNT(DISTINCT province) c FROM records "
            "WHERE province IS NOT NULL AND province != ''", one=True)["c"],
    }
    by_province = query_db(
        "SELECT province AS name, COUNT(*) AS count FROM records GROUP BY province ORDER BY count DESC"
    )
    by_year = query_db(
        "SELECT arrest_year AS year, COUNT(*) AS count FROM records "
        "WHERE arrest_year IS NOT NULL AND arrest_year > 0 "
        "GROUP BY arrest_year ORDER BY arrest_year DESC"
    )
    recent = query_db(
        "SELECT id, first_name, last_name, status, created_at FROM records ORDER BY id DESC LIMIT 10"
    )
    return render_template(
        "dashboard.html", stats=stats, by_province=by_province,
        by_year=by_year, recent=recent,
    )


@app.route("/records")
def records_list():
    page     = request.args.get("page", 1, type=int)
    per_page = 50

    filter_keys = [
        "q", "status", "province", "gender", "verification_status",
        "arrest_year", "record_status", "evidence_level", "marital",
        "case_type", "education",
    ]
    filters    = {k: request.args.get(k, "").strip() for k in filter_keys}
    conditions = []
    params     = []

    if filters["q"]:
        conditions.append(
            "(first_name || ' ' || father_name || ' ' || last_name LIKE ? "
            "OR national_id LIKE ? OR phone LIKE ?)"
        )
        q = f"%{filters['q']}%"
        params.extend([q, q, q])

    for col in ["status", "province", "gender", "verification_status",
                "record_status", "evidence_level", "marital", "case_type", "education"]:
        if filters[col]:
            conditions.append(f"{col} = ?")
            params.append(filters[col])

    if filters["arrest_year"]:
        conditions.append("arrest_year = ?")
        params.append(int(filters["arrest_year"]))

    where       = "WHERE " + " AND ".join(conditions) if conditions else ""
    total       = query_db(f"SELECT COUNT(*) c FROM records {where}", params, one=True)["c"]
    total_pages = max(1, (total + per_page - 1) // per_page)
    page        = min(page, total_pages)
    offset      = (page - 1) * per_page

    records = query_db(
        f"SELECT id, first_name, father_name, last_name, national_id, gender, "
        f"province, status, arrest_year, verification_status, record_status, photo_path "
        f"FROM records {where} ORDER BY id DESC LIMIT ? OFFSET ?",
        params + [per_page, offset],
    )

    filter_options = {
        "statuses":              distinct_values("status"),
        "provinces":             distinct_values("province"),
        "genders":               distinct_values("gender"),
        "verification_statuses": distinct_values("verification_status"),
        "record_statuses":       distinct_values("record_status"),
        "evidence_levels":       distinct_values("evidence_level"),
        "maritals":              distinct_values("marital"),
        "case_types":            distinct_values("case_type"),
        "educations":            distinct_values("education"),
    }

    return render_template(
        "records.html", records=records, total=total,
        page=page, total_pages=total_pages,
        filters=filters, filter_options=filter_options,
    )


@app.route("/records/add", methods=["GET", "POST"])
def record_add():
    if request.method == "POST":
        data = form_to_dict()
        cols         = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        try:
            db  = get_db()
            cur = db.execute(
                f"INSERT INTO records ({cols}) VALUES ({placeholders})",
                list(data.values()),
            )
            record_id = cur.lastrowid
            db.commit()
            handle_photo_uploads(record_id)
            db.commit()
            flash("تم إضافة الحالة بنجاح", "success")
            return redirect(url_for("record_view", record_id=record_id))
        except Exception as e:
            flash(f"خطأ: {e}", "danger")

    opts = get_form_options()
    return render_template("record_form.html", record=None, photos=[], **opts)


@app.route("/records/<int:record_id>")
def record_view(record_id):
    record = query_db("SELECT * FROM records WHERE id = ?", [record_id], one=True)
    if not record:
        flash("السجل غير موجود", "warning")
        return redirect(url_for("records_list"))
    photos = query_db(
        "SELECT * FROM record_photos WHERE record_id=? AND photo_type='evidence' ORDER BY id",
        [record_id],
    )
    return render_template("record_view.html", record=record, photos=photos)


@app.route("/records/<int:record_id>/edit", methods=["GET", "POST"])
def record_edit(record_id):
    record = query_db("SELECT * FROM records WHERE id = ?", [record_id], one=True)
    if not record:
        flash("السجل غير موجود", "warning")
        return redirect(url_for("records_list"))

    if request.method == "POST":
        data       = form_to_dict()
        set_clause = ", ".join(f"{k} = ?" for k in data.keys())
        try:
            db = get_db()
            db.execute(
                f"UPDATE records SET {set_clause} WHERE id = ?",
                list(data.values()) + [record_id],
            )
            db.commit()
            handle_photo_uploads(record_id, record)
            db.commit()
            flash("تم تحديث السجل بنجاح", "success")
            return redirect(url_for("record_view", record_id=record_id))
        except Exception as e:
            flash(f"خطأ: {e}", "danger")
            record = query_db("SELECT * FROM records WHERE id = ?", [record_id], one=True)

    photos = query_db(
        "SELECT * FROM record_photos WHERE record_id=? AND photo_type='evidence' ORDER BY id",
        [record_id],
    )
    opts = get_form_options()
    return render_template("record_form.html", record=record, photos=photos, **opts)


@app.route("/records/<int:record_id>/photos/<int:photo_id>/delete", methods=["POST"])
def photo_delete(record_id, photo_id):
    photo = query_db(
        "SELECT * FROM record_photos WHERE id=? AND record_id=?", [photo_id, record_id], one=True
    )
    if photo:
        delete_upload(photo["filename"])
        get_db().execute("DELETE FROM record_photos WHERE id=?", [photo_id])
        get_db().commit()
        flash("تم حذف الصورة", "success")
    return redirect(url_for("record_edit", record_id=record_id) + "#photos")


@app.route("/records/<int:record_id>/photo/delete/<slot>", methods=["POST"])
def single_photo_delete(record_id, slot):
    """Delete personal photo or ID document."""
    if slot not in ("photo", "document"):
        abort(400)
    col    = "photo_path" if slot == "photo" else "document_path"
    record = query_db(f"SELECT {col} FROM records WHERE id=?", [record_id], one=True)
    if record and record[col]:
        delete_upload(record[col])
        get_db().execute(f"UPDATE records SET {col}=NULL WHERE id=?", [record_id])
        get_db().commit()
        flash("تم حذف الصورة", "success")
    return redirect(url_for("record_edit", record_id=record_id) + "#photos")


@app.route("/records/<int:record_id>/delete", methods=["POST"])
def record_delete(record_id):
    record = query_db("SELECT photo_path, document_path FROM records WHERE id=?", [record_id], one=True)
    photos = query_db("SELECT filename FROM record_photos WHERE record_id=?", [record_id])
    try:
        db = get_db()
        db.execute("DELETE FROM records WHERE id = ?", [record_id])
        db.commit()
        # Clean up files after successful delete
        if record:
            delete_upload(record["photo_path"])
            delete_upload(record["document_path"])
        for p in photos:
            delete_upload(p["filename"])
        flash("تم حذف السجل", "success")
    except Exception as e:
        flash(f"خطأ: {e}", "danger")
    return redirect(url_for("records_list"))


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    print("\n" + "=" * 50)
    print("  سجل الحالات - Registry Case Management")
    print("=" * 50)
    print(f"  Database : {DB_PATH}")
    print(f"  Uploads  : {UPLOAD_DIR}")
    print(f"  Local    : http://localhost:5000")
    print(f"  Network  : http://<this-ip>:5000")
    print("=" * 50 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
