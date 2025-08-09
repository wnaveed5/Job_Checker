from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import json
from pathlib import Path

app = FastAPI(title="Job Checker", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for the React frontend (only if directory exists)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Pydantic models for API responses
class JobResponse(BaseModel):
    id: str
    title: str
    company: str
    location: str
    url: str
    source: str
    scope: str
    is_stretch: bool
    created_at: str
    description: Optional[str] = None

class JobStats(BaseModel):
    total_jobs: int
    jobs_today: int
    jobs_by_company: dict
    jobs_by_scope: dict

class SearchResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    page: int
    per_page: int

# Mock data for demonstration
MOCK_JOBS = [
    {
        "id": "1",
        "title": "Senior Software Engineer",
        "company": "Tech Corp",
        "location": "San Francisco, CA",
        "url": "https://example.com/job1",
        "source": "Greenhouse",
        "scope": "Core",
        "is_stretch": False,
        "created_at": "2024-01-15T10:00:00Z",
        "description": "Join our team building amazing software!"
    },
    {
        "id": "2",
        "title": "Full Stack Developer",
        "company": "Startup Inc",
        "location": "Remote",
        "url": "https://example.com/job2",
        "source": "Remotive",
        "scope": "Stretch",
        "is_stretch": True,
        "created_at": "2024-01-15T09:00:00Z",
        "description": "Exciting opportunity at a fast-growing startup!"
    }
]

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        with open(html_path, "r") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Job Checker API</h1><p>Frontend not built yet. Use /api endpoints.</p>")

@app.get("/api/jobs", response_model=SearchResponse)
async def get_jobs(
    page: int = 1,
    per_page: int = 20,
    company: Optional[str] = None,
    scope: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None
):
    """Get paginated job listings with optional filters"""
    try:
        # Filter jobs based on parameters
        filtered_jobs = MOCK_JOBS.copy()
        
        if company:
            filtered_jobs = [job for job in filtered_jobs if company.lower() in job["company"].lower()]
        
        if source:
            filtered_jobs = [job for job in filtered_jobs if job["source"] == source]
        
        if scope:
            filtered_jobs = [job for job in filtered_jobs if job["scope"] == scope]
        
        if search:
            search_lower = search.lower()
            filtered_jobs = [
                job for job in filtered_jobs 
                if search_lower in job["title"].lower() or search_lower in job["company"].lower()
            ]
        
        total = len(filtered_jobs)
        
        # Apply pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_jobs = filtered_jobs[start_idx:end_idx]
        
        # Convert to response format
        jobs = []
        for job in paginated_jobs:
            jobs.append(JobResponse(**job))
        
        return SearchResponse(
            jobs=jobs,
            total=total,
            page=page,
            per_page=per_page
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")

@app.get("/api/jobs/today", response_model=List[JobResponse])
async def get_jobs_today():
    """Get jobs posted today"""
    try:
        today = datetime.now().date()
        today_jobs = []
        
        for job in MOCK_JOBS:
            job_date = datetime.fromisoformat(job["created_at"].replace("Z", "+00:00")).date()
            if job_date == today:
                today_jobs.append(JobResponse(**job))
        
        return today_jobs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching today's jobs: {str(e)}")

@app.get("/api/stats", response_model=JobStats)
async def get_stats():
    """Get job statistics"""
    try:
        total_jobs = len(MOCK_JOBS)
        
        # Count jobs by company
        jobs_by_company = {}
        for job in MOCK_JOBS:
            company = job["company"]
            jobs_by_company[company] = jobs_by_company.get(company, 0) + 1
        
        # Count jobs by scope
        jobs_by_scope = {}
        for job in MOCK_JOBS:
            scope = job["scope"]
            jobs_by_scope[scope] = jobs_by_scope.get(scope, 0) + 1
        
        # Count today's jobs
        today = datetime.now().date()
        jobs_today = 0
        for job in MOCK_JOBS:
            job_date = datetime.fromisoformat(job["created_at"].replace("Z", "+00:00")).date()
            if job_date == today:
                jobs_today += 1
        
        return JobStats(
            total_jobs=total_jobs,
            jobs_today=jobs_today,
            jobs_by_company=jobs_by_company,
            jobs_by_scope=jobs_by_scope
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@app.post("/api/refresh")
async def refresh_jobs():
    """Refresh job listings (mock implementation)"""
    try:
        return {"message": "Job refresh initiated", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing jobs: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
