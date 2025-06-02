from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi import HTTPException
import json
import zipfile
import os

from engine import Engine
from lyrics import Lyrics
from search import Search
from download import Download

from threading import Thread
from time import sleep

def wait_for_download_end(downloader: Download):
    while not downloader.is_ready():
        sleep(1)

    try:
        engine.enqueue(f"downloads/{downloader.get_name()}")
        wait_for_engine_end_and_get_lyrics(f"downloads/{downloader.get_name()}")
    except Exception as e:
        print(f"internal error while queueing song {e}")

def wait_for_engine_end_and_get_lyrics(path: str):
    while not engine.is_done(path):
        sleep(1)
    
    try:
        with open(f"{path}/metadata.json", mode="r") as file:
            txt = file.read()
            j = json.loads(txt)
            title = j["title"]
            lyrics = Lyrics("", title, path)
            lyrics.is_done()
    except Exception as e:
        print(f"internal error while queueing song {e}")

app = FastAPI()
engine = Engine()

@app.post("/v1/songs")
async def process_song(link):
    """
    Receives link to a song and directs it to download and process

    Returns:
        json: unique song id based on youtube url
    """
    download = Download(link)
    
    try:
        song_id = download.get_name()
    except Exception as e:
        return HTTPException(status_code=502, detail=e)

    Thread(target = wait_for_download_end, args=(download, )).start()
    
    return {"song_id": song_id}

@app.get("/v1/songinfo/{song_id}")
async def get_songinfo(song_id: str):
    """
    Returns:
        json: whether song is ready to be downloaded from the server, expiry date...
    """
    path = f"downloads/{song_id}"

    if not engine.is_done(path):
        return {"ready": False}
    
    file = open(f"{path}/metadata.json", "r")
    metadata = json.load(file)
    file.close()

    metadata["ready"] = True

    return metadata

@app.get("/v1/songs/{song_id}")
async def get_songfile(song_id: str):
    """
    Returns:
        payload: processed song along with metadata
    """
    base_path = os.path.join("downloads", song_id, "htdemucs", "audio")
    if not os.path.exists(os.path.join(base_path, "vocals.mp3")) or\
        not os.path.exists(os.path.join(base_path, "no_vocals.mp3")):
        raise HTTPException(status_code=404, detail="Path does not exist")
    
    zip_path = f"downloads/{song_id}"
    zipf = zipfile.ZipFile(os.path.join(zip_path, "package.zip"), "w")
    zipf.write(os.path.join(base_path, "vocals.mp3"), arcname="vocals.mp3")
    zipf.write(os.path.join(base_path, "no_vocals.mp3"), arcname="no_vocals.mp3")
    zipf.write(os.path.join(zip_path, "metadata.json"), arcname="metadata.json")
    zipf.close()

    return FileResponse(
        path=os.path.join(zip_path, "package.zip"),
        filename="package.zip",
        media_type="application/zip"
    )

@app.get("/v1/search/{query}")
async def search_song(query: str):
    """
    Returns:
        json: Search results from a query
    """
    search = Search(query)
    # error handling
    return search.serialize()