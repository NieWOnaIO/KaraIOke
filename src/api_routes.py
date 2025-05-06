from fastapi import FastAPI
import json


app = FastAPI()

@app.post("/v1/songs")
async def _(link):
    """
    Receives link to a song and directs it to download

    Returns:
        json: unique song id based on youtube url
    """
    return {"song_id": ""}

@app.get("/v1/songinfo/{song_id}")
async def get_songinfo(song_id: str) -> dict:
    """
    Returns:
        json: whether song is ready to be downloaded from the server, expiry date...
    """
    song = json.load(f"downloads/{song_id}/metadata.json")
    return song

@app.get("/v1/songs/{song_id}")
async def _():
    """
    Returns:
        payload: processed song along with metadata
    """
    raise NotImplementedError()

@app.get("/v1/search/{query}")
async def _():
    """
    Returns:
        json: Search results from a query
    """

    
    raise NotImplementedError()
