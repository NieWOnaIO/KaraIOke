from fastapi import FastAPI

app = FastAPI()

@app.get("/songs/{song_id}")
async def getStatus():
  if isReady(dsg):
    return {"message": "ready"}
  raise NotImplementedError