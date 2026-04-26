from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from sniffer import sniffer_instance

app = FastAPI(title="Local Agent UI")

# Setup templates directory
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "status": "Running" if sniffer_instance.is_running else "Stopped",
        "buffer_size": len(sniffer_instance.flow_cache.cache)
    })

@app.post("/start")
async def start_sniffing():
    success = sniffer_instance.start()
    return {"status": "started" if success else "already running"}

@app.post("/stop")
async def stop_sniffing():
    sniffer_instance.stop()
    return {"status": "stopped"}

if __name__ == "__main__":
    import uvicorn
    from dotenv import load_dotenv
    load_dotenv()
    print("Starting agent...")
    # Optionally start automatically if API key is provided
    if os.getenv("AGENT_API_KEY"):
        print("API Key found, automatically starting sniffer...")
        sniffer_instance.start()
    else:
        print("Waiting for manual start via Local Agent UI (http://127.0.0.1:8001)...")
    
    uvicorn.run("main:app", host="127.0.0.1", port=8001, log_level="info")
