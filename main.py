import os
import uuid
from typing import Disc ,Optional 
from fastapi import FastAPI, BackgroundTasks, HTTPException , status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel,HttpUrl

from services.extractor import MediaExtractor

app  = FastAPI(title='Media Pipeline API')
#Allow requests from frontend development servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods =["*"],
    allow_headers=["*"],
)

extractor = MediaExtractor(download_dir='downloads')
JOB_STORE:Disc[str,Disc]={}

class InspectRequest(BaseModel):
    url:HttpUrl
class DownloadRequest(BaseModel):
    url:HttpUrl
    format_id:Optional[str] = None

@app.post("/api/inspect")
def inspect_url(payload:InspectRequest):
    """Fetches video metadata sp the user can see title/ thumbnail and pick formate."""
    try:
        data = extractor.get_info(str(payload.url))
        return{
            "success":True,
            "data":data
            }
    except Exception as e:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            details=f"Metadata extraction failed:{str(e)}"
        )

def process_download_task(job_id:str,url:str,format_id:Optional[str]):
    """Backgrounf task running outside the synchronous request cycle"""
    try:
        JOB_STORE[job_id]['status'] = "processing"
        file_path = extractor.download_media(url ,job_id ,format_id)
        JOB_STORE[job_id]["status"] = "completed"
        JOB_STORE[job_id]["file_path"] =file_path
    except Exception as err:
        JOB_STORE[job_id]["status"] = "failed"
        JOB_STORE[job_id]['error']= str(err)