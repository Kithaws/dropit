import os
import shutil
import secrets
import time
import sqlite3
from fastapi import FastAPI, UploadFile, File, Request, BackgroundTasks, Form
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import qrcode

app = FastAPI()

UPLOAD_DIR = "temp_uploads"
ROOM_EXPIRY = 600  # 10 minutes

# Create upload folder
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs("static", exist_ok=True)

# Templates & Static
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------
# DATABASE SETUP
# -------------------------
conn = sqlite3.connect("dropit.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
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

def delete_room(room_id):
    cursor.execute("SELECT filename FROM rooms WHERE room_id=?", (room_id,))
    row = cursor.fetchone()

    if row and row[0]:
        file_path = os.path.join(UPLOAD_DIR, row[0])
        if os.path.exists(file_path):
            os.remove(file_path)

    cursor.execute("DELETE FROM rooms WHERE room_id=?", (room_id,))
    conn.commit()


def is_expired(expiry):
    if expiry is None:
        return False
    return time.time() > expiry


# -------------------------
# ROUTES
# -------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/create-room")
async def create_room():
    room_id = secrets.token_urlsafe(6)

    cursor.execute(
        "INSERT INTO rooms (room_id, expiry) VALUES (?, ?)",
        (room_id, time.time() + ROOM_EXPIRY)
    )
    conn.commit()

    return RedirectResponse(f"/room/{room_id}", status_code=302)


@app.get("/room/{room_id}", response_class=HTMLResponse)
async def room_page(request: Request, room_id: str):

    cursor.execute(
        "SELECT filename, text, expiry FROM rooms WHERE room_id=?",
        (room_id,)
    )
    row = cursor.fetchone()

    if not row:
        return HTMLResponse("Room not found", status_code=404)

    filename, text_content, expiry = row

    if is_expired(expiry):
        delete_room(room_id)
        return HTMLResponse("Room expired", status_code=404)

    # Generate QR
    url = str(request.base_url) + f"room/{room_id}"
    qr_path = f"static/{room_id}.png"

    img = qrcode.make(url)
    img.save(qr_path)

    return templates.TemplateResponse(
        "room.html",
        {
            "request": request,
            "room_id": room_id,
            "qr_image": f"/{qr_path}",
            "text_content": text_content,
            "has_file": filename is not None
        }
    )


@app.post("/upload/{room_id}")
async def upload_file(room_id: str, file: UploadFile = File(...)):

    cursor.execute("SELECT expiry FROM rooms WHERE room_id=?", (room_id,))
    row = cursor.fetchone()

    if not row:
        return {"error": "Room not found"}

    if is_expired(row[0]):
        delete_room(room_id)
        return {"error": "Room expired"}

    unique_name = secrets.token_hex(8) + "_" + file.filename
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    cursor.execute(
        "UPDATE rooms SET filename=? WHERE room_id=?",
        (unique_name, room_id)
    )
    conn.commit()

    return RedirectResponse(f"/room/{room_id}", status_code=302)


@app.post("/send-text/{room_id}")
async def send_text(room_id: str, text: str = Form(...)):

    cursor.execute("SELECT expiry FROM rooms WHERE room_id=?", (room_id,))
    row = cursor.fetchone()

    if not row:
        return {"error": "Room not found"}

    if is_expired(row[0]):
        delete_room(room_id)
        return {"error": "Room expired"}

    cursor.execute(
        "UPDATE rooms SET text=? WHERE room_id=?",
        (text, room_id)
    )
    conn.commit()

    return RedirectResponse(f"/room/{room_id}", status_code=302)


@app.get("/download/{room_id}")
async def download_file(room_id: str, background_tasks: BackgroundTasks):

    cursor.execute(
        "SELECT filename, expiry FROM rooms WHERE room_id=?",
        (room_id,)
    )
    row = cursor.fetchone()

    if not row:
        return {"error": "Room not found"}

    filename, expiry = row

    if is_expired(expiry):
        delete_room(room_id)
        return {"error": "Room expired"}

    if not filename:
        return {"error": "No file uploaded"}

    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        return {"error": "File not found"}

    background_tasks.add_task(delete_room, room_id)

    return FileResponse(file_path, filename=filename)