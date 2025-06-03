import json
import os
from threading import Thread

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from download import DOWNLOADS_PATH, Download
from engine import Engine
from lyrics import Lyrics
from search import Search


def wait_for_engine_end_and_get_lyrics(path: str):
    engine.wait_for(path)
    try:
        with open(f"{path}/metadata.json") as file:
            txt = file.read()
            j = json.loads(txt)
            title = j["title"]
            lyrics = Lyrics("", title, path)
            lyrics.is_done()
    except Exception as e:
        print(f"internal error while queueing song {e}")


def wait_for_download_end(downloader: Download):
    downloader.wait_for()
    try:
        engine.enqueue(f"{DOWNLOADS_PATH}/{downloader.get_name()}")
    except Exception as e:
        print(f"internal error while queueing song {e}")
    
    wait_for_engine_end_and_get_lyrics(f"{DOWNLOADS_PATH}/{downloader.get_name()}")
        
app = FastAPI()
engine = Engine()


@app.post("/v1/process_song")
async def process_song(link):
    """
    Receives link to a song and directs it to download and process

    Returns:
        json: unique song id based on youtube url
    """
    download = Download(link)
    engine.enqueue(download)

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
    path = Download.get_download_dir(song_id)

    if not engine.is_done(path):
        return {"ready": False}

    with open(os.path.join(path, "metadata.json")) as file:
        metadata = json.load(file)

    metadata["ready"] = True
    return metadata


@app.get("/v1/song_vocals/{song_id}")
async def get_song_vocals(song_id: str):
    """
    Returns:
        payload: processed song along with metadata
    """
    path = os.path.join(
        DOWNLOADS_PATH, song_id, "htdemucs", "audio", "vocals.mp3"
    )
    if not os.path.exists(path):
        raise HTTPException(
            status_code=404, detail="Path does not exist"
        )

    return FileResponse(
        path=path, filename="audio.mp3", media_type="application/mp3"
    )


@app.get("/v1/song_no_vocals/{song_id}")
async def get_song_no_vocals(song_id: str):
    """
    Returns:
        payload: processed song along with metadata
    """
    path = os.path.join(
        DOWNLOADS_PATH, song_id, "htdemucs", "audio", "no_vocals.mp3"
    )
    if not os.path.exists(path):
        raise HTTPException(
            status_code=404, detail="Path does not exist"
        )

    return FileResponse(
        path=path, filename="audio.mp3", media_type="application/mp3"
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
