from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import sqlite3
import os
import sys
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import json

# Add the parent directory to the path so we can import job_checker modules
sys.path.append(str(Path(__file__).parent.parent))

from job_checker.config import load_config
from job_checker.filtering import split_scope

app = FastAPI(title="Job Checker", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for the React frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

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

def get_db_connection():
    """Get database connection"""
    db_path = Path(__file__).parent.parent / "job_checker.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

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
    conn = get_db_connection()
    try:
        # Build the query
        query = "SELECT * FROM seen WHERE 1=1"
        params = []
        
        if company:
            query += " AND url LIKE ?"
            params.append(f"%{company}%")
        
        if source:
            query += " AND source = ?"
            params.append(source)
        
        if search:
            query += " AND (key LIKE ? OR url LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])
        
        # Get total count
        count_query = query.replace("SELECT *", "SELECT COUNT(*)")
        cursor = conn.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Add pagination
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to response format
        jobs = []
        for row in rows:
            # Parse the job data
            job_data = json.loads(row['key']) if row['key'] else {}
            
            # Determine scope
            scope_tag, is_stretch = split_scope(job_data, load_config())
            
            jobs.append(JobResponse(
                id=row['url'],
                title=job_data.get('title', 'Unknown'),
                company=job_data.get('company', 'Unknown'),
                location=job_data.get('location', 'Unknown'),
                url=row['url'],
                source=row['source'],
                scope=scope_tag or 'Unknown',
                is_stretch=is_stretch,
                created_at=row['created_at'],
                description=job_data.get('description', '')
            ))
        
        return SearchResponse(
            jobs=jobs,
            total=total,
            page=page,
            per_page=per_page
        )
    
    finally:
        conn.close()

@app.get("/api/jobs/today", response_model=List[JobResponse])
async def get_jobs_today():
    """Get all jobs from today"""
    conn = get_db_connection()
    try:
        query = """
        SELECT * FROM seen 
        WHERE DATE(created_at) = DATE('now') 
        ORDER BY created_at DESC
        """
        cursor = conn.execute(query)
        rows = cursor.fetchall()
        
        jobs = []
        for row in rows:
            job_data = json.loads(row['key']) if row['key'] else {}
            scope_tag, is_stretch = split_scope(job_data, load_config())
            
            jobs.append(JobResponse(
                id=row['url'],
                title=job_data.get('title', 'Unknown'),
                company=job_data.get('company', 'Unknown'),
                location=job_data.get('location', 'Unknown'),
                url=row['url'],
                source=row['source'],
                scope=scope_tag or 'Unknown',
                is_stretch=is_stretch,
                created_at=row['created_at'],
                description=job_data.get('description', '')
            ))
        
        return jobs
    
    finally:
        conn.close()

@app.get("/api/stats", response_model=JobStats)
async def get_stats():
    """Get job statistics"""
    conn = get_db_connection()
    try:
        # Total jobs
        cursor = conn.execute("SELECT COUNT(*) FROM seen")
        total_jobs = cursor.fetchone()[0]
        
        # Jobs today
        cursor = conn.execute("SELECT COUNT(*) FROM seen WHERE DATE(created_at) = DATE('now')")
        jobs_today = cursor.fetchone()[0]
        
        # Jobs by company (approximate)
        cursor = conn.execute("""
            SELECT 
                CASE 
                    WHEN url LIKE '%okta%' THEN 'Okta'
                    WHEN url LIKE '%roku%' THEN 'Roku'
                    WHEN url LIKE '%dropbox%' THEN 'Dropbox'
                    WHEN url LIKE '%twilio%' THEN 'Twilio'
                    WHEN url LIKE '%cloudflare%' THEN 'Cloudflare'
                    WHEN url LIKE '%datadog%' THEN 'Datadog'
                    WHEN url LIKE '%coinbase%' THEN 'Coinbase'
                    WHEN url LIKE '%airbnb%' THEN 'Airbnb'
                    WHEN url LIKE '%hashicorp%' THEN 'HashiCorp'
                    WHEN url LIKE '%databricks%' THEN 'Databricks'
                    WHEN url LIKE '%gitlab%' THEN 'GitLab'
                    WHEN url LIKE '%elastic%' THEN 'Elastic'
                    WHEN url LIKE '%stripe%' THEN 'Stripe'
                    WHEN url LIKE '%roblox%' THEN 'Roblox'
                    WHEN url LIKE '%hellofresh%' THEN 'HelloFresh'
                    ELSE 'Other'
                END as company,
                COUNT(*) as count
            FROM seen 
            GROUP BY company 
            ORDER BY count DESC
        """)
        jobs_by_company = {row['company']: row['count'] for row in cursor.fetchall()}
        
        # Jobs by scope (approximate)
        cursor = conn.execute("SELECT source, COUNT(*) as count FROM seen GROUP BY source ORDER BY count DESC")
        jobs_by_scope = {row['source']: row['count'] for row in cursor.fetchall()}
        
        return JobStats(
            total_jobs=total_jobs,
            jobs_today=jobs_today,
            jobs_by_company=jobs_by_company,
            jobs_by_scope=jobs_by_scope
        )
    
    finally:
        conn.close()

@app.post("/api/refresh")
async def refresh_jobs():
    """Manually trigger a job refresh"""
    try:
        # Import and run the main job checker
        from job_checker.main import main
        main(once=True)
        return {"message": "Jobs refreshed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
