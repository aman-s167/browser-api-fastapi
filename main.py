from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from pyppeteer import launch
import asyncio
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager  # Import asynccontextmanager

load_dotenv()  # Load environment variables

# Configure browser launch options
BROWSER_OPTIONS = {
    "headless": "new",
    "args": ["--no-sandbox", "--disable-setuid-sandbox"],
    "executablePath": os.getenv("PUPPETEER_EXECUTABLE_PATH")
}

# Global browser instance
browser = None

async def get_browser():
    global browser
    if browser is None:
        browser = await launch(**BROWSER_OPTIONS)
    return browser

async def close_browser():
    global browser
    if browser:
        await browser.close()
        browser = None

# --- Lifespan Event Handler ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic (nothing to do here in this case, as get_browser handles it)
    yield
    # Shutdown logic
    await close_browser()

app = FastAPI(lifespan=lifespan) # Use lifespan event handler

# --- Request Models ---
class ScreenshotRequest(BaseModel):
    url: str

class ExtractRequest(BaseModel):
    url: str
    selector: str

class EvaluateRequest(BaseModel):
    url: str
    expression: str

# --- API Endpoints ---

@app.post("/screenshot")
async def take_screenshot(request: ScreenshotRequest):
    try:
        browser_instance = await get_browser()
        page = await browser_instance.newPage()
        await page.goto(request.url, {'waitUntil': 'networkidle0'})
        screenshot_buffer = await page.screenshot()
        await page.close()
        return Response(content=screenshot_buffer, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/extract")
async def extract_text(request: ExtractRequest):
    try:
        browser_instance = await get_browser()
        page = await browser_instance.newPage()
        await page.goto(request.url, {'waitUntil': 'networkidle0'})
        text = await page.querySelectorEval(request.selector, 'element => element.textContent')
        await page.close()
        return {"text": text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evaluate")
async def evaluate_javascript(request: EvaluateRequest):
    try:
        browser_instance = await get_browser()
        page = await browser_instance.newPage()
        await page.goto(request.url, {'waitUntil': 'networkidle0'})
        result = await page.evaluate(request.expression)
        await page.close()
        return {"result":result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
