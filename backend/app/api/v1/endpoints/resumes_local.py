from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List
import aiofiles
import os
from app.core.database import get_db
from app.models.resume import Resume
from app.schemas.resume import Resume as ResumeSchema, ResumeCreate, ResumeParseResponse
from app.services.resume_service import resume_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload", response_model=ResumeSchema)
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user_id = getattr(request.state, 'user_id', 'local-user-123')
    
    if not file.filename.lower().endswith(('.pdf', '.txt', '.docx')):
        raise HTTPException(status_code=400, detail="Only PDF, TXT, and DOCX files are supported")
    
    try:
        content = await file.read()
        
        # Store locally for development
        upload_dir = f"/tmp/uploads/{user_id}"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = f"{upload_dir}/{file.filename}"
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        # Extract text content for immediate processing
        if file.filename.lower().endswith('.txt'):
            content_str = content.decode('utf-8')
        else:
            content_str = "Sample resume content for local development"
        
        resume_data = ResumeCreate(
            user_id=user_id,
            filename=file.filename,
            content=content_str
        )
        
        db_resume = Resume(
            user_id=resume_data.user_id,
            filename=resume_data.filename,
            file_path=file_path,
            content=content_str
        )
        
        db.add(db_resume)
        db.commit()
        db.refresh(db_resume)
        
        return db_resume
        
    except Exception as e:
        logger.error(f"Failed to upload resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload resume")

@router.get("/", response_model=List[ResumeSchema])
async def get_resumes(
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = getattr(request.state, 'user_id', 'local-user-123')
    resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
    return resumes

@router.get("/{resume_id}", response_model=ResumeSchema)
async def get_resume(
    resume_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = getattr(request.state, 'user_id', 'local-user-123')
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return resume

@router.post("/{resume_id}/parse", response_model=ResumeParseResponse)
async def parse_resume(
    resume_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = getattr(request.state, 'user_id', 'local-user-123')
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    try:
        if not resume.content:
            raise HTTPException(status_code=400, detail="Resume content not available for parsing")
        
        parsed_data = resume_service.parse_resume_content(resume.content)
        
        resume.parsed_data = parsed_data
        db.commit()
        
        return ResumeParseResponse(
            skills=parsed_data.get("skills", []),
            experience=parsed_data.get("experience", []),
            contact_info=parsed_data.get("contact_info", {})
        )
        
    except Exception as e:
        logger.error(f"Failed to parse resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse resume")

@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    user_id = getattr(request.state, 'user_id', 'local-user-123')
    resume = db.query(Resume).filter(
        Resume.id == resume_id,
        Resume.user_id == user_id
    ).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    try:
        if os.path.exists(resume.file_path):
            os.remove(resume.file_path)
        
        db.delete(resume)
        db.commit()
        
        return {"message": "Resume deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete resume: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete resume")