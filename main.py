import os
import shutil
import secrets
import time
from fastapi import FastAPI, UploadFile, File, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import qrcode

app = FastAPI()

UPLOAD_DIR = "temp_uploads"
ROOM_EXPIRY = 600  # 10 minutes

# Create upload folder if not exists
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

templates = Jinja2Templates(directory="templates")

# Mount static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

rooms = {}  # room_id -> {filename, expiry}


def delete_room(room_id):
    if room_id in rooms:
        file_path = os.path.join(UPLOAD_DIR, rooms[room_id]["filename"])
        if os.path.exists(file_path):
            os.remove(file_path)
        del rooms[room_id]


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/create-room")
async def create_room():
    room_id = secrets.token_urlsafe(6)
    rooms[room_id] = {}
    return RedirectResponse(f"/room/{room_id}", status_code=302)


@app.get("/room/{room_id}", response_class=HTMLResponse)
async def room_page(request: Request, room_id: str):
    if room_id not in rooms:
        return HTMLResponse("Room not found", status_code=404)

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
            "qr_image": f"/{qr_path}"
        }
    )


@app.post("/upload/{room_id}")
async def upload_file(room_id: str, file: UploadFile = File(...)):
    if room_id not in rooms:
        return {"error": "Room not found"}

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    rooms[room_id] = {
        "filename": file.filename,
        "expiry": time.time() + ROOM_EXPIRY
    }

    return RedirectResponse(f"/room/{room_id}", status_code=302)


@app.get("/download/{room_id}")
async def download_file(room_id: str, background_tasks: BackgroundTasks):
    if room_id not in rooms:
        return {"error": "Room expired"}

    file_path = os.path.join(UPLOAD_DIR, rooms[room_id]["filename"])

    if not os.path.exists(file_path):
        return {"error": "File not found"}

    background_tasks.add_task(delete_room, room_id)

    return FileResponse(file_path, filename=rooms[room_id]["filename"])