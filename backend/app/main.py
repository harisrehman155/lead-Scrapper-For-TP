from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from .scraper import scraper_instance
import threading
import os
import json

app = FastAPI()

class StartRequest(BaseModel):
    visual_mode: bool = False

# Background task wrapper
def run_scraper():
    scraper_instance.run()

@app.post("/start")
def start_scraper(request: StartRequest, background_tasks: BackgroundTasks):
    if scraper_instance.is_running:
        return {"message": "Scraper is already running"}
    
    # Set mode
    scraper_instance.toggle_mode(request.visual_mode)
    
    # We use threading instead of background_tasks for long running process 
    # to avoid blocking if we want to query status
    t = threading.Thread(target=run_scraper)
    t.start()
    
    return {"message": f"Scraper started in {'Visual' if request.visual_mode else 'Fast'} mode"}

@app.post("/mode")
def set_mode(request: StartRequest):
    scraper_instance.toggle_mode(request.visual_mode)
    return {"message": f"Switched to {'Visual' if request.visual_mode else 'Fast'} mode"}

@app.post("/stop")
def stop_scraper():
    scraper_instance.stop()
    return {"message": "Stopping scraper..."}

@app.get("/status")
def get_status():
    return {
        "is_running": scraper_instance.is_running,
        "current_id": scraper_instance.current_id,
        "total_records": scraper_instance.total_records,
        "blank_count": scraper_instance.blank_count,
        "visual_mode": scraper_instance.visual_mode
    }

@app.get("/download")
def download_data():
    if os.path.exists(scraper_instance.json_file):
        try:
            # Convert JSON to Excel on demand
            import pandas as pd
            with open(scraper_instance.json_file, 'r') as f:
                data = json.load(f)
            
            df = pd.DataFrame(data)
            df.to_excel(scraper_instance.data_file, index=False)
            
            return FileResponse(scraper_instance.data_file, filename="invoices.xlsx", media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        except Exception as e:
            return {"error": f"Error generating Excel: {str(e)}"}
            
    return {"error": "No data found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
