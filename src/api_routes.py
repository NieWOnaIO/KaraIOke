from fastapi import FastAPI

app = FastAPI()

@app.post("/v1/songs")
async def _():
    """
    Receives link to a song and directs it to download

    Returns:
        json: unique song id based on youtube url
    """
    raise NotImplementedError()

@app.get("/v1/songinfo/{song_id}")
async def _():
    """
    Returns:
        json: whether song is ready to be downloaded from the server, expiry date...
    """
    raise NotImplementedError()

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