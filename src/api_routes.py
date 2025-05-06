from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi import HTTPException
import json
import asyncio
import os

from engine import Engine
from search import Search
from download import Download


app = FastAPI()
engine = Engine()

@app.post("/v1/songs")
async def process_song(link):
    """
    Receives link to a song and directs it to download

    Returns:
        json: unique song id based on youtube url
    """
    timeout_download = 60
    download = Download(link)

    success = False
    for _ in range(timeout_download):
        if download.is_ready():
            success = True
            break
        await asyncio.sleep(1)

    if not success:
        return {"status": "download timeout", "song_id": ""}
    
    try:
        song_id = download.get_name()
        engine.enqueue(f"downloads/{song_id}/audio.mp3")
    except Exception as e:
        return {"status": e, "song_id": ""}
    
    timeout_process = 180
    success = False

    for _ in range(timeout_process):
        if download.is_ready():
            success = True
            break
        await asyncio.sleep(1)
    
    if not success:
        return {"status": "processing timeout", "song_id": ""}
    
    return {"status": "success", "song_id": song_id}

@app.get("/v1/songinfo/{song_id}")
async def get_songinfo(song_id: str):
    """
    Returns:
        json: whether song is ready to be downloaded from the server, expiry date...
    """
    path = f"downloads/{song_id}/metadata.json"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Path does not exist")

    return json.load(path)

@app.get("/v1/songs/{song_id}")
async def get_songfile(song_id: str):
    """
    Returns:
        payload: processed song along with metadata
    """
    path = f"downloads/{song_id}/audio.mp3"
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Path does not exist")
    
    return FileResponse(
        path=f"downloads/{song_id}/audio.mp3",
        media_type="audio/mpeg",
        filename="audio.mp3"
    )

@app.get("/v1/search/{query}")
async def search_song(query: str):
    """
    Returns:
        json: Search results from a query
    """
    search = Search(query)
    # errors checking
    return search.serialize()
