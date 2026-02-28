import os
import shutil
import secrets
import time
import sqlite3
from pathlib import Path
from contextlib import closing
from fastapi import FastAPI, UploadFile, File, Request, BackgroundTasks, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import qrcode

app = FastAPI(title="Dropit 🔥")

# Use absolute paths for Windows compatibility
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "temp_uploads"
STATIC_DIR = BASE_DIR / "static"
ROOM_EXPIRY = 600  # 10 minutes
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB limit

# Create required folders
UPLOAD_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Templates & Static
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# -------------------------
# DATABASE SETUP
# -------------------------

def get_db():
    db_path = str(BASE_DIR / "dropit.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

with closing(get_db()) as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            room_id TEXT PRIMARY KEY,
            filename TEXT,
            text TEXT,
            expiry REAL
        )
    """)
    conn.commit()


# -------------------------
# HELPER FUNCTIONS
# -------------------------

def delete_room(room_id: str):
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT filename FROM rooms WHERE room_id=?", (room_id,))
        row = cursor.fetchone()

        if row and row["filename"]:
            file_path = UPLOAD_DIR / row["filename"]
            if file_path.exists():
                file_path.unlink()

        cursor.execute("DELETE FROM rooms WHERE room_id=?", (room_id,))
        conn.commit()


def is_expired(expiry):
    return expiry and time.time() > expiry


def clean_expired_rooms():
    with closing(get_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT room_id, expiry FROM rooms")
        rows = cursor.fetchall()

        for row in rows:
            if is_expired(row["expiry"]):
                delete_room(row["room_id"])


# -------------------------
# ROUTES
# -------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    clean_expired_rooms()
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/create-room")
async def create_room():
    room_id = secrets.token_urlsafe(6)

    with closing(get_db()) as conn:
        conn.execute(
            "INSERT INTO rooms (room_id, expiry) VALUES (?, ?)",
            (room_id, time.time() + ROOM_EXPIRY)
        )
        conn.commit()

    return RedirectResponse(f"/room/{room_id}", status_code=302)


@app.get("/room/{room_id}", response_class=HTMLResponse)
async def room_page(request: Request, room_id: str):

    with closing(get_db()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT filename, text, expiry FROM rooms WHERE room_id=?",
            (room_id,)
        )
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Room not found")

    if is_expired(row["expiry"]):
        delete_room(room_id)
        raise HTTPException(status_code=404, detail="Room expired")

    # Generate QR
    url = str(request.base_url) + f"room/{room_id}"
    qr_path = STATIC_DIR / f"{room_id}.png"

    if not qr_path.exists():
        img = qrcode.make(url)
        img.save(str(qr_path))

    return templates.TemplateResponse(
        "room.html",
        {
            "request": request,
            "room_id": room_id,
            "qr_image": f"/static/{room_id}.png",
            "text_content": row["text"],
            "has_file": row["filename"] is not None
        }
    )


@app.post("/upload/{room_id}")
async def upload_file(room_id: str, file: UploadFile = File(...)):

    with closing(get_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT expiry FROM rooms WHERE room_id=?", (room_id,))
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Room not found")

    if is_expired(row["expiry"]):
        delete_room(room_id)
        raise HTTPException(status_code=404, detail="Room expired")

    # File size protection
    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)

    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 20MB)")

    safe_name = secrets.token_hex(8)
    extension = Path(file.filename).suffix if file.filename else ""
    unique_name = f"{safe_name}{extension}"

    file_path = UPLOAD_DIR / unique_name

    try:
        with open(str(file_path), "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    with closing(get_db()) as conn:
        conn.execute(
            "UPDATE rooms SET filename=? WHERE room_id=?",
            (unique_name, room_id)
        )
        conn.commit()

    return RedirectResponse(f"/room/{room_id}", status_code=302)


@app.post("/send-text/{room_id}")
async def send_text(room_id: str, text: str = Form(...)):

    with closing(get_db()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT expiry FROM rooms WHERE room_id=?", (room_id,))
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Room not found")

    if is_expired(row["expiry"]):
        delete_room(room_id)
        raise HTTPException(status_code=404, detail="Room expired")

    with closing(get_db()) as conn:
        conn.execute(
            "UPDATE rooms SET text=? WHERE room_id=?",
            (text, room_id)
        )
        conn.commit()

    return RedirectResponse(f"/room/{room_id}", status_code=302)


@app.get("/download/{room_id}")
async def download_file(room_id: str, background_tasks: BackgroundTasks):

    with closing(get_db()) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT filename, expiry FROM rooms WHERE room_id=?",
            (room_id,)
        )
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Room not found")

    if is_expired(row["expiry"]):
        delete_room(room_id)
        raise HTTPException(status_code=404, detail="Room expired")

    filename = row["filename"]

    if not filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    file_path = UPLOAD_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    background_tasks.add_task(delete_room, room_id)

    return FileResponse(str(file_path), filename=filename)