from fastapi import FastAPI
from fastapi.responses import FileResponse
import json
from search import Search

from engine import Engine

app = FastAPI()
engine = Engine()

@app.post("/v1/songs")
async def _(link):
    """
    Receives link to a song and directs it to download

    Returns:
        json: unique song id based on youtube url
    """

    return {"song_id": ""}

@app.get("/v1/songinfo/{song_id}")
async def get_songinfo(song_id: str):
    """
    Returns:
        json: whether song is ready to be downloaded from the server, expiry date...
    """
    song = json.load(f"downloads/{song_id}/metadata.json")
    return song

@app.get("/v1/songs/{song_id}")
async def get_songfile(song_id: str):
    """
    Returns:
        payload: processed song along with metadata
    """
    return FileResponse(
        path=f"downloads/{song_id}/raw_song.mp3",
        media_type="audio/mpeg",
        filename="raw_song.mp3"
    )

@app.get("/v1/search/{query}")
async def search_song(query: str):
    """
    Returns:
        json: Search results from a query
    """
    search = Search(query)
    search.search_query()
    return search.serialize()
