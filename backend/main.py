from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import sqlite3
import shutil
import os

from database import init_db, DB_PATH, BASE_DIR
from nlp import rank_found_reports
from qr import generate_code, generate_qr_image


# =========================================================
# APP SETUP
# =========================================================

app = FastAPI(title="LostLink")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# =========================================================
# DATABASE + DIRECTORIES
# =========================================================

init_db()

DATA_DIR = os.path.join(BASE_DIR, "data")
PHOTO_DIR = os.path.join(DATA_DIR, "photos")
QR_DIR = os.path.join(DATA_DIR, "qr_codes")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PHOTO_DIR, exist_ok=True)
os.makedirs(QR_DIR, exist_ok=True)


# =========================================================
# FRONTEND
# =========================================================

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app.mount(
    "/data",
    StaticFiles(directory=DATA_DIR),
    name="data"
)


# =========================================================
# MAIN WEBSITE / PAGES
# =========================================================

@app.get("/")
async def home():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "dashboard.html")
    )


@app.get("/app.js")
async def javascript():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "app.js"),
        media_type="application/javascript"
    )


@app.get("/reports-page")
async def reports_page():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "reports.html")
    )


@app.get("/matches-page")
async def matches_page():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "matches.html")
    )


@app.get("/register-item")
async def register_item_page():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "register-item.html")
    )


@app.get("/registered-items")
async def registered_items_page():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "registered-items.html")
    )


# =========================================================
# REGISTERED ITEMS DATA
# =========================================================

@app.get("/registered-items-data")
async def get_registered_items():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    c.execute("""
        SELECT
            id,
            code,
            name,
            category,
            color,
            brand,
            status
        FROM items
        ORDER BY id DESC
    """)

    rows = [dict(row) for row in c.fetchall()]

    conn.close()

    return rows


# =========================================================
# REPORT - CREATE
# =========================================================

@app.post("/report")
async def create_report(
    report_type: str = Form(...),
    reporter_name: str = Form(""),
    reporter_role: str = Form(...),
    category: str = Form(""),
    color: str = Form(""),
    brand: str = Form(""),
    description: str = Form(""),
    location: str = Form(...),
    latitude: float = Form(None),
    longitude: float = Form(None),
    date_time: str = Form(...),
    photo: UploadFile = File(None)
):

    photo_path = None

    if photo and photo.filename:

        filename = os.path.basename(photo.filename)

        full_photo_path = os.path.join(
            PHOTO_DIR,
            filename
        )

        with open(full_photo_path, "wb") as f:
            shutil.copyfileobj(
                photo.file,
                f
            )

        photo_path = f"data/photos/{filename}"


    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        INSERT INTO reports (
            report_type,
            reporter_name,
            reporter_role,
            category,
            color,
            brand,
            description,
            location,
            latitude,
            longitude,
            date_time,
            photo_path
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_type,
        reporter_name,
        reporter_role,
        category,
        color,
        brand,
        description,
        location,
        latitude,
        longitude,
        date_time,
        photo_path
    ))

    conn.commit()

    report_id = c.lastrowid

    conn.close()

    return {
        "status": "success",
        "report_id": report_id
    }


# =========================================================
# GET ALL REPORTS
# =========================================================

@app.get("/reports")
async def get_reports():

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    c.execute("""
        SELECT *
        FROM reports
    """)

    rows = [
        dict(row)
        for row in c.fetchall()
    ]

    conn.close()

    return rows


# =========================================================
# MATCHES
# =========================================================

@app.get("/matches/{report_id}")
async def get_matches(report_id: int):

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    c = conn.cursor()

    c.execute("""
        SELECT *
        FROM reports
        WHERE id = ?
        AND report_type = 'LOST'
    """, (report_id,))

    lost_report = c.fetchone()

    if not lost_report:

        conn.close()

        return {
            "status": "error",
            "message": "LOST report not found"
        }


    c.execute("""
        SELECT *
        FROM reports
        WHERE report_type = 'FOUND'
    """)

    found_reports = c.fetchall()

    conn.close()


    lost_report = dict(lost_report)

    found_reports = [
        dict(report)
        for report in found_reports
    ]


    matches = rank_found_reports(
        lost_report,
        found_reports
    )


    return {
        "status": "success",
        "lost_report": lost_report,
        "matches": matches
    }


# =========================================================
# REGISTER ITEM
# =========================================================

@app.post("/register-item")
async def register_item(

    name: str = Form(...),

    category: str = Form(""),

    color: str = Form(""),

    brand: str = Form(""),

    private_detail: str = Form("")
):

    conn = sqlite3.connect(DB_PATH)

    c = conn.cursor()


    # -----------------------------------------------------
    # GENERATE UNIQUE LOSTLINK CODE
    # -----------------------------------------------------

    while True:

        code = generate_code()

        c.execute(
            "SELECT id FROM items WHERE code = ?",
            (code,)
        )

        existing = c.fetchone()

        if not existing:
            break


    # -----------------------------------------------------
    # SAVE ITEM
    # -----------------------------------------------------

    c.execute("""
        INSERT INTO items (
            code,
            name,
            category,
            color,
            brand,
            private_detail,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        code,
        name,
        category,
        color,
        brand,
        private_detail,
        "REGISTERED"
    ))


    conn.commit()

    conn.close()


    # -----------------------------------------------------
    # GENERATE QR CODE
    # -----------------------------------------------------

    qr_path = generate_qr_image(code)

    qr_filename = os.path.basename(qr_path)

    qr_url = f"/data/qr_codes/{qr_filename}"


    return {
        "status": "success",
        "message": "Item registered successfully",
        "code": code,
        "qr_url": qr_url
    }


# =========================================================
# SCAN / VIEW ITEM
# =========================================================

@app.get("/item/{code}")
async def get_item(code: str):

    conn = sqlite3.connect(DB_PATH)

    conn.row_factory = sqlite3.Row

    c = conn.cursor()


    c.execute("""
        SELECT
            code,
            name,
            category,
            color,
            brand,
            status
        FROM items
        WHERE code = ?
    """, (code,))


    item = c.fetchone()

    conn.close()


    if not item:

        return {
            "status": "error",
            "message": "Item not found"
        }


    return {
        "status": "success",
        "item": dict(item)
    }


# =========================================================
# NOTIFY OWNER
# =========================================================

@app.post("/item/{code}/notify")
async def notify_owner(code: str):

    conn = sqlite3.connect(DB_PATH)

    c = conn.cursor()


    c.execute("""
        UPDATE items
        SET status = 'NOTIFIED'
        WHERE code = ?
    """, (code,))


    if c.rowcount == 0:

        conn.close()

        return {
            "status": "error",
            "message": "Item not found"
        }


    conn.commit()

    conn.close()


    return {
        "status": "success",
        "message": "Owner has been notified",
        "code": code,
        "new_status": "NOTIFIED"
    }