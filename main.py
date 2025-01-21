import json
import random
import string
from typing import Annotated

import aiofiles
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import motor.motor_asyncio

app = FastAPI()
db_client = motor.motor_asyncio.AsyncIOMotorClient("localhost", 27017, username="root", password="example")
app_db = db_client["url_shortener"]
collection = app_db["urls"]
templates = Jinja2Templates(directory="templates")

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/")
async def root(request: Request, long_url: Annotated[str, Form()]):
    short_url = "".join(
        [random.choice(string.ascii_letters+string.digits) for _ in range(5)]
    )
    await collection.insert_one({"short_url": short_url, "long_url": long_url})
    return {"message": f"Shortened URL: {short_url}"}


@app.get("/{short_url}")
async def convert_url(short_url: str):
    collection_data = await collection.find_one({"short_url": short_url})
    redirect_url = collection_data.get("long_url") if collection_data else None
    collection_data = await collection.update_one({"short_url": short_url}, {"$inc": {"clicks": 1}})
    print(
        f"Short URL: {short_url} | Clicks: {collection_data.modified_count}"
    )
    if redirect_url is None:
        raise HTTPException(status_code=404, detail="URL not found")
    else:
        return RedirectResponse(redirect_url)

@app.get("/{short_url}/stats")
async def stats(request: Request, short_url: str):
    collection_data = await collection.find_one({"short_url": short_url})
    if collection_data is None:
        raise HTTPException(status_code=404, detail="URL not found")
    return templates.TemplateResponse(request=request, name="stats.html", context={"url_data": collection_data})

@app.post("/{short_url}/stats")
async def edit_stats(request: Request, short_url: str, long_url: Annotated[str, Form()]):
    await collection.update_one({"short_url": short_url}, {"$set": {"long_url": long_url}})
    collection_data = await collection.find_one({"short_url": short_url})
    return templates.TemplateResponse(request=request, name="stats.html", context={"url_data": collection_data})