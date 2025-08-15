# Job Finder Service

A microservice that provides live job matching by fetching real-time job postings from multiple Applicant Tracking System (ATS) APIs and using AI-powered embeddings for intelligent matching.

## Architecture

The Job Finder Service is designed as a stateless microservice that:

1. **Fetches Live Jobs**: Connects to multiple ATS APIs (Greenhouse, Lever, Ashby, SmartRecruiters, Adzuna) to get real-time job postings
2. **Generates Embeddings**: Uses Google Vertex AI to create semantic embeddings for resume text and job descriptions
3. **Intelligent Matching**: Calculates similarity scores using cosine similarity and skill matching
4. **Caches Results**: Stores job embeddings in PostgreSQL with pgvector for fast similarity search
5. **Validates URLs**: Ensures job apply URLs are still valid before returning results

## Features

- 🔄 **Real-time Job Fetching**: Live integration with major ATS platforms
- 🤖 **AI-Powered Matching**: Vertex AI embeddings for semantic similarity
- ⚡ **Fast Caching**: PostgreSQL with pgvector for efficient similarity search
- 🔗 **URL Validation**: Ensures job links are still active
- 📊 **Comprehensive Scoring**: Combines embedding similarity, skill matching, and experience level
- 🚀 **Auto-scaling**: Cloud Run with automatic scaling based on demand
- 🔒 **Secure**: IAM authentication and Secret Manager for API keys

## Supported ATS Platforms

- **Greenhouse**: Job Board API for public job postings
- **Lever**: Postings API for active job listings
- **Ashby**: Job Posting API for organization listings
- **SmartRecruiters**: Posting API for company job boards
- **Adzuna**: Job search aggregator for broader coverage

## API Endpoints

### POST /jobs/live
Find live job matches for a resume

**Request:**
```json
{
  "resume_text": "Experienced software engineer with Python and React skills...",
  "location": "US",
  "days": 7,
  "keywords": ["python", "react", "aws"],
  "limit": 20,
  "min_salary": 80000,
  "max_salary": 150000,
  "job_types": ["full_time", "remote"],
  "remote_only": false
}
```

**Response:**
```json
[
  {
    "id": "greenhouse_12345",
    "title": "Senior Software Engineer",
    "company": "Google",
    "description": "We're looking for a senior engineer...",
    "location": "San Francisco, CA",
    "apply_url": "https://careers.google.com/jobs/12345",
    "posted_at": "2024-01-15T10:00:00Z",
    "match_score": 0.85,
    "matching_skills": ["python", "react", "aws"],
    "salary_min": 120000,
    "salary_max": 180000,
    "job_type": "full_time",
    "remote": true,
    "ats_source": "greenhouse"
  }
]
```

### GET /jobs/cached
Get job matches from cached embeddings (faster but may be stale)

### POST /jobs/refresh
Refresh the job cache by fetching new postings (typically called by scheduler)

### GET /stats
Get service statistics and health information

### GET /health
Health check endpoint

## Setup Instructions

### 1. Prerequisites

- Google Cloud Project with billing enabled
- Required APIs enabled:
  - `aiplatform.googleapis.com` (Vertex AI)
  - `run.googleapis.com` (Cloud Run)
  - `cloudscheduler.googleapis.com` (Cloud Scheduler)
  - `vpcaccess.googleapis.com` (VPC Connector)
  - `secretmanager.googleapis.com` (Secret Manager)

### 2. Infrastructure Setup

```bash
# Run the setup script
./scripts/setup-job-finder.sh YOUR_PROJECT_ID us-west2

# Deploy infrastructure
cd infra
terraform init
terraform apply
```

### 3. Configure ATS API Keys

Create a JSON file with your ATS API keys:

```json
{
  "greenhouse": "your_greenhouse_api_key",
  "lever": "your_lever_api_key", 
  "ashby": "your_ashby_api_key",
  "smartrecruiters": "your_smartrecruiters_api_key",
  "adzuna_app_id": "your_adzuna_app_id",
  "adzuna_app_key": "your_adzuna_app_key"
}
```

Update the secret:
```bash
gcloud secrets versions add job-matcher-ats-api-keys \
  --data-file=your-keys.json \
  --project=YOUR_PROJECT_ID
```

### 4. Build and Deploy

```bash
# Build the Docker image
docker build -t gcr.io/YOUR_PROJECT_ID/job-finder:latest ./job-finder

# Push to Artifact Registry
docker push gcr.io/YOUR_PROJECT_ID/job-finder:latest

# Deploy to Cloud Run
gcloud run deploy job-finder \
  --image=gcr.io/YOUR_PROJECT_ID/job-finder:latest \
  --region=us-west2 \
  --platform=managed \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=1 \
  --max-instances=10 \
  --min-instances=1
```

### 5. Configure Scheduled Refresh

The service includes a Cloud Scheduler job that refreshes the job cache every hour. This is automatically configured by Terraform.

## Configuration

### Environment Variables

- `JOB_FINDER_DATABASE_URL`: PostgreSQL connection string
- `JOB_FINDER_VERTEX_AI_PROJECT_ID`: Google Cloud project ID for Vertex AI
- `JOB_FINDER_VERTEX_AI_LOCATION`: Vertex AI region (default: us-central1)
- `JOB_FINDER_VERTEX_AI_MODEL`: Embedding model (default: textembedding-gecko@003)
- `JOB_FINDER_MIN_SIMILARITY_THRESHOLD`: Minimum similarity score (default: 0.3)
- `JOB_FINDER_MAX_JOBS_PER_REQUEST`: Max jobs per request (default: 50)
- `JOB_FINDER_CACHE_TTL_HOURS`: Cache TTL in hours (default: 24)

### Target Companies

The service maintains a curated list of target companies to fetch jobs from. This can be configured via Secret Manager:

```bash
gcloud secrets versions add job-matcher-target-companies \
  --data-file=target-companies.json \
  --project=YOUR_PROJECT_ID
```

## Database Schema

The service uses PostgreSQL with the pgvector extension for efficient similarity search:

```sql
CREATE TABLE cached_jobs (
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
    last_verified TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Matching Algorithm

The service uses a multi-factor scoring system:

1. **Embedding Similarity (60%)**: Cosine similarity between resume and job description embeddings
2. **Skill Matching (30%)**: Percentage of matching skills between resume and job
3. **Experience Level (10%)**: Alignment between job requirements and resume experience level

### Skill Extraction

The service extracts skills from multiple categories:
- Programming languages (Python, JavaScript, Java, etc.)
- Frameworks (React, Django, Spring, etc.)
- Databases (PostgreSQL, MongoDB, Redis, etc.)
- Cloud platforms (AWS, GCP, Azure, etc.)
- DevOps tools (Docker, Kubernetes, Terraform, etc.)
- ML/AI tools (TensorFlow, PyTorch, scikit-learn, etc.)
- Methodologies (Agile, Scrum, DevOps, etc.)

## Monitoring and Observability

### Metrics

- Total jobs cached
- Jobs by ATS source
- Average response time
- Cache hit rate
- Embedding model performance

### Logging

The service logs:
- Job fetching operations
- Embedding generation
- Matching calculations
- Error conditions
- Performance metrics

### Health Checks

- Database connectivity
- Vertex AI service availability
- ATS API connectivity
- Memory and CPU usage

## Integration with Main Application

The Job Finder Service integrates with the main Job Matcher application:

1. **Backend Integration**: The main backend calls the job finder service via HTTP
2. **Fallback Support**: Falls back to local job matching if the service is unavailable
3. **Caching**: Results are cached to improve performance
4. **Error Handling**: Graceful degradation when external services are down

## Cost Optimization

### Estimated Monthly Costs

- **Cloud Run**: $20-50 (based on usage)
- **Vertex AI**: $5-15 (embedding API calls)
- **Cloud SQL**: $25-40 (database hosting)
- **Cloud Scheduler**: $1-2 (scheduled jobs)
- **Secret Manager**: $1-3 (secret storage)

**Total**: ~$50-110/month for moderate usage

### Cost Reduction Tips

1. **Caching**: Use cached results when possible
2. **Batch Processing**: Process multiple requests together
3. **Rate Limiting**: Implement rate limiting for ATS APIs
4. **Resource Limits**: Set appropriate CPU/memory limits
5. **Scheduled Refresh**: Use Cloud Scheduler instead of continuous polling

## Troubleshooting

### Common Issues

1. **ATS API Errors**
   ```bash
   # Check API key configuration
   gcloud secrets versions access latest --secret=job-matcher-ats-api-keys
   ```

2. **Vertex AI Errors**
   ```bash
   # Verify Vertex AI is enabled
   gcloud services enable aiplatform.googleapis.com
   ```

3. **Database Connection Issues**
   ```bash
   # Check Cloud SQL connectivity
   gcloud sql instances describe job-matcher-postgres
   ```

4. **High Latency**
   - Check embedding generation time
   - Verify database query performance
   - Monitor ATS API response times

### Debug Commands

```bash
# Check service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=job-finder"

# Test the service
curl -X POST https://job-finder-xxxxx-uc.a.run.app/jobs/live \
  -H 'Content-Type: application/json' \
  -d '{"resume_text":"test","location":"US"}'

# Check service stats
curl https://job-finder-xxxxx-uc.a.run.app/stats
```

## Security Considerations

1. **API Key Management**: All ATS API keys stored in Secret Manager
2. **IAM Authentication**: Service uses least-privilege IAM roles
3. **Network Security**: VPC connector for private database access
4. **Input Validation**: All inputs validated and sanitized
5. **Rate Limiting**: Implemented to prevent abuse

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
