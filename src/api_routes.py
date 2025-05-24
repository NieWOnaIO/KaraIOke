import json
import os
from time import sleep

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from download import Download
from engine import Engine
from search import Search


def wait_for_download_end(downloader: Download):
    while not downloader.is_ready():
        sleep(1)

    try:
        engine.enqueue(f"downloads/{downloader.get_name()}")
    except Exception as e:
        print(f"internal error while queueing song {e}")


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
        "downloads", song_id, "htdemucs", "audio", "vocals.mp3"
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
        "downloads", song_id, "htdemucs", "audio", "no_vocals.mp3"
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
    return search.results
