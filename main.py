import os
import uuid
from typing import Dict ,Optional 
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
JOB_STORE:Dict[str,Dict]={}

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
            detail=f"Metadata extraction failed:{str(e)}"
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



@app.post("/api/jobs")
def create_job(payload:DownloadRequest , background_tasks:BackgroundTasks):
    """Creates a download task and returns a job_id immediately."""
    job_id = str(uuid.uuid4())
    JOB_STORE[job_id]={
        "id":job_id,
        "status":"queued",
        "file_path":None,
        "error":None
    }
    background_tasks.add_task(process_download_task,job_id,str(payload.url),payload.format_id)
    return {
        "job_id":job_id ,
        "status":"queued",
          }

@app.get("/api/jobs/{job_id}")
def get_jov_status(job_id:str):
    """Frontend polls this route to monitor progress."""
    job = JOB_STORE.get(job_id)
    if not job:
        raise HTTPException(
                status_code=404,
                detail="job_not found"
             )
    return job


@app.get("/api/download/{job_id}")
def retrieve_file(job_id:str):
    """Triggers browser file download once the status is completed."""
    job = JOB_STORE.get(job_id) 
    if not job or job.get("status") != "completed":
        raise HTTPException(
            status_code = 404 ,
            detail = "File is not ready or failed"
        )

    return FileResponse(
        path =job['file_path'],
        filename=f"video_{job_id[:8]}.mp4",
        media_type="video/mp4"
    )
