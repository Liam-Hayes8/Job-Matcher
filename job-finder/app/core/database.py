import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncpg
from app.core.config import settings

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pool = None
        
    async def initialize(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                settings.database_url,
                min_size=5,
                max_size=20
            )
            
            # Create tables if they don't exist
            await self._create_tables()
            
            logger.info("Database manager initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            raise
    
    async def _create_tables(self):
        """Create database tables if they don't exist"""
        try:
            async with self.pool.acquire() as conn:
                # Enable pgvector extension
                await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                
                # Create cached jobs table
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS cached_jobs (
                        id VARCHAR(255) PRIMARY KEY,
                        title VARCHAR(500) NOT NULL,
                        company VARCHAR(255) NOT NULL,
                        description TEXT NOT NULL,
                        location VARCHAR(255),
                        apply_url TEXT NOT NULL,
                        posted_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        embedding vector(768),
                        salary_min INTEGER,
                        salary_max INTEGER,
                        job_type VARCHAR(50),
                        remote BOOLEAN DEFAULT FALSE,
                        ats_source VARCHAR(50) NOT NULL,
                        requirements TEXT,
                        benefits TEXT,
                        raw_data JSONB,
                        cached_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        last_verified TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                """)
                
                # Create index for vector similarity search
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_cached_jobs_embedding 
                    ON cached_jobs 
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100)
                """)
                
                # Create index for location and date filtering
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_cached_jobs_location_date 
                    ON cached_jobs (location, posted_at DESC)
                """)
                
                # Create index for ATS source
                await conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_cached_jobs_ats_source 
                    ON cached_jobs (ats_source)
                """)
                
                logger.info("Database tables created successfully")
                
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    async def store_job_embeddings(
        self, 
        jobs: List[Dict[str, Any]], 
        embeddings: List[List[float]]
    ):
        """Store jobs with their embeddings in the database"""
        try:
            if not jobs or not embeddings:
                return
            
            async with self.pool.acquire() as conn:
                # Prepare batch insert
                values = []
                for i, job in enumerate(jobs):
                    if i < len(embeddings):
                        values.append((
                            job.get("id"),
                            job.get("title", ""),
                            job.get("company", ""),
                            job.get("description", ""),
                            job.get("location", ""),
                            job.get("apply_url", ""),
                            job.get("posted_at"),
                            embeddings[i],
                            job.get("salary_min"),
                            job.get("salary_max"),
                            job.get("job_type"),
                            job.get("remote", False),
                            job.get("ats_source", ""),
                            job.get("requirements"),
                            job.get("benefits"),
                            json.dumps(job.get("raw_data", {}))
                        ))
                
                # Batch insert with upsert
                await conn.executemany("""
                    INSERT INTO cached_jobs (
                        id, title, company, description, location, apply_url, 
                        posted_at, embedding, salary_min, salary_max, job_type, 
                        remote, ats_source, requirements, benefits, raw_data
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
                    ON CONFLICT (id) DO UPDATE SET
                        title = EXCLUDED.title,
                        company = EXCLUDED.company,
                        description = EXCLUDED.description,
                        location = EXCLUDED.location,
                        apply_url = EXCLUDED.apply_url,
                        posted_at = EXCLUDED.posted_at,
                        embedding = EXCLUDED.embedding,
                        salary_min = EXCLUDED.salary_min,
                        salary_max = EXCLUDED.salary_max,
                        job_type = EXCLUDED.job_type,
                        remote = EXCLUDED.remote,
                        ats_source = EXCLUDED.ats_source,
                        requirements = EXCLUDED.requirements,
                        benefits = EXCLUDED.benefits,
                        raw_data = EXCLUDED.raw_data,
                        last_verified = NOW()
                """, values)
                
                logger.info(f"Stored {len(values)} job embeddings in database")
                
        except Exception as e:
            logger.error(f"Error storing job embeddings: {e}")
            raise
    
    async def get_cached_jobs(
        self, 
        location: str = "US", 
        limit: int = 100,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get cached jobs with embeddings"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, title, company, description, location, apply_url,
                           posted_at, embedding, salary_min, salary_max, job_type,
                           remote, ats_source, requirements, benefits, raw_data,
                           cached_at, last_verified
                    FROM cached_jobs
                    WHERE posted_at >= $1
                    AND (location ILIKE $2 OR $2 = 'US')
                    ORDER BY posted_at DESC
                    LIMIT $3
                """, cutoff_date, f"%{location}%", limit)
                
                jobs = []
                for row in rows:
                    job = dict(row)
                    # Convert embedding to list if it exists
                    if job.get("embedding"):
                        job["embedding"] = list(job["embedding"])
                    jobs.append(job)
                
                return jobs
                
        except Exception as e:
            logger.error(f"Error getting cached jobs: {e}")
            return []
    
    async def find_similar_jobs(
        self, 
        embedding: List[float], 
        limit: int = 20,
        threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Find similar jobs using vector similarity search"""
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT id, title, company, description, location, apply_url,
                           posted_at, embedding, salary_min, salary_max, job_type,
                           remote, ats_source, requirements, benefits, raw_data,
                           cached_at, last_verified,
                           1 - (embedding <=> $1) as similarity
                    FROM cached_jobs
                    WHERE 1 - (embedding <=> $1) > $2
                    ORDER BY embedding <=> $1
                    LIMIT $3
                """, embedding, threshold, limit)
                
                jobs = []
                for row in rows:
                    job = dict(row)
                    if job.get("embedding"):
                        job["embedding"] = list(job["embedding"])
                    jobs.append(job)
                
                return jobs
                
        except Exception as e:
            logger.error(f"Error finding similar jobs: {e}")
            return []
    
    async def cleanup_old_jobs(self, days: int = 30):
        """Remove old job entries from cache"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            async with self.pool.acquire() as conn:
                result = await conn.execute("""
                    DELETE FROM cached_jobs
                    WHERE posted_at < $1
                """, cutoff_date)
                
                logger.info(f"Cleaned up old jobs older than {days} days")
                
        except Exception as e:
            logger.error(f"Error cleaning up old jobs: {e}")
    
    async def update_job_verification(self, job_id: str):
        """Update the last verification time for a job"""
        try:
            async with self.pool.acquire() as conn:
                await conn.execute("""
                    UPDATE cached_jobs
                    SET last_verified = NOW()
                    WHERE id = $1
                """, job_id)
                
        except Exception as e:
            logger.error(f"Error updating job verification: {e}")
    
    async def get_job_stats(self) -> Dict[str, Any]:
        """Get statistics about cached jobs"""
        try:
            async with self.pool.acquire() as conn:
                # Total jobs
                total_count = await conn.fetchval("SELECT COUNT(*) FROM cached_jobs")
                
                # Jobs by source
                source_stats = await conn.fetch("""
                    SELECT ats_source, COUNT(*) as count
                    FROM cached_jobs
                    GROUP BY ats_source
                    ORDER BY count DESC
                """)
                
                # Recent jobs (last 7 days)
                recent_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM cached_jobs
                    WHERE posted_at >= NOW() - INTERVAL '7 days'
                """)
                
                # Average embedding similarity (if any)
                avg_similarity = await conn.fetchval("""
                    SELECT AVG(1 - (embedding <=> embedding)) 
                    FROM cached_jobs 
                    WHERE embedding IS NOT NULL
                """)
                
                return {
                    "total_jobs": total_count,
                    "recent_jobs": recent_count,
                    "sources": {row["ats_source"]: row["count"] for row in source_stats},
                    "avg_similarity": float(avg_similarity) if avg_similarity else 0.0
                }
                
        except Exception as e:
            logger.error(f"Error getting job stats: {e}")
            return {
                "total_jobs": 0,
                "recent_jobs": 0,
                "sources": {},
                "avg_similarity": 0.0
            }
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()

# Database dependency for FastAPI
async def get_db() -> DatabaseManager:
    """Get database manager instance"""
    db = DatabaseManager()
    await db.initialize()
    return db
