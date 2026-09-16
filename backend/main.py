from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import sqlite3
import shutil
import os

from database import init_db, DB_PATH, BASE_DIR
from nlp import rank_found_reports


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


init_db()


DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

PHOTO_DIR = os.path.join(
    DATA_DIR,
    "photos"
)


os.makedirs(
    DATA_DIR,
    exist_ok=True
)

os.makedirs(
    PHOTO_DIR,
    exist_ok=True
)


FRONTEND_DIR = os.path.join(
    BASE_DIR,
    "frontend"
)


app.mount(
    "/data",
    StaticFiles(directory=DATA_DIR),
    name="data"
)


@app.get("/")
async def home():

    return FileResponse(
        os.path.join(
            FRONTEND_DIR,
            "report.html"
        )
    )


@app.get("/app.js")
async def javascript():

    return FileResponse(
        os.path.join(
            FRONTEND_DIR,
            "app.js"
        ),
        media_type="application/javascript"
    )


@app.get("/reports-page")
async def reports_page():

    return FileResponse(
        os.path.join(
            FRONTEND_DIR,
            "reports.html"
        )
    )


@app.get("/matches-page")
async def matches_page():

    return FileResponse(
        os.path.join(
            FRONTEND_DIR,
            "matches.html"
        )
    )


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


    # Save uploaded photo
    if photo and photo.filename:

        filename = os.path.basename(
            photo.filename
        )

        full_photo_path = os.path.join(
            PHOTO_DIR,
            filename
        )

        with open(
            full_photo_path,
            "wb"
        ) as f:

            shutil.copyfileobj(
                photo.file,
                f
            )

        photo_path = (
            f"data/photos/{filename}"
        )


    # Save report in database
    conn = sqlite3.connect(
        DB_PATH
    )

    c = conn.cursor()


    c.execute(
        """
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
        """,

        (
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
    )


    conn.commit()

    report_id = c.lastrowid

    conn.close()


    return {
        "status": "success",
        "report_id": report_id
    }


@app.get("/reports")
async def get_reports():

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    c = conn.cursor()


    c.execute(
        "SELECT * FROM reports"
    )


    rows = [
        dict(row)
        for row in c.fetchall()
    ]


    conn.close()


    return rows


@app.get("/matches/{report_id}")
async def get_matches(
    report_id: int
):

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    c = conn.cursor()


    # Find LOST report
    c.execute(
        """
        SELECT *
        FROM reports
        WHERE id = ?
        AND report_type = 'LOST'
        """,

        (report_id,)
    )


    lost_report = c.fetchone()


    if not lost_report:

        conn.close()

        return {
            "status": "error",
            "message": "LOST report not found"
        }


    # Find all FOUND reports
    c.execute(
        """
        SELECT *
        FROM reports
        WHERE report_type = 'FOUND'
        """
    )


    found_reports = c.fetchall()

    conn.close()


    lost_report = dict(
        lost_report
    )


    found_reports = [
        dict(report)
        for report in found_reports
    ]


    # Calculate matching scores
    matches = rank_found_reports(
        lost_report,
        found_reports
    )


    return {
        "status": "success",
        "lost_report": lost_report,
        "matches": matches
    }