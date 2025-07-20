from pathlib import Path
import uuid
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageSequence

UPLOAD = Path("upload")
UPLOAD.mkdir(exist_ok=True)

app = FastAPI(title="GIF Cropper")
app.mount("/static", StaticFiles(directory="static"), name="static")

def crop_gif(src: Path, dst: Path, left: int, top: int, width: int, height: int):
    frames = []
    with Image.open(src) as im:
        for frame in ImageSequence.Iterator(im):
            cropped = frame.convert("RGBA").crop(
                (left, top, left + width, top + height)
            ).convert("P", palette=Image.ADAPTIVE)
            frames.append(cropped)
        frames[0].save(
            dst,
            save_all=True,
            append_images=frames[1:],
            duration=im.info.get("duration", 100),
            loop=im.info.get("loop", 0),
            format="GIF",
        )

@app.post("/crop")
async def crop(
    left: int = Form(...),
    top: int = Form(...),
    width: int = Form(...),
    height: int = Form(...),
    file: UploadFile = File(...),
):
    if not file.content_type.startswith("image/gif"):
        raise HTTPException(400, "Envoyez un GIF")
    uid = uuid.uuid4().hex
    in_path = UPLOAD / f"{uid}.gif"
    out_path = UPLOAD / f"{uid}_crop.gif"
    with in_path.open("wb") as f:
        f.write(await file.read())
    crop_gif(in_path, out_path, left, top, width, height)
    return {"download_url": f"/download/{out_path.name}"}

@app.get("/download/{name}")
async def download(name: str):
    path = UPLOAD / name
    if not path.exists():
        raise HTTPException(404, "Fichier introuvable")
    return FileResponse(path, media_type="image/gif", filename="cropped.gif")

@app.get("/")
async def root():
    return FileResponse("static/index.html")