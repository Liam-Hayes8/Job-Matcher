# Job Matcher

A full-stack Resume Parser + Job Matcher application deployed on Google Cloud Platform (GCP). This system uses AI-powered resume parsing and job matching to help job seekers find relevant opportunities.

## Architecture

- **Infrastructure**: Terraform manages GCP resources with state stored in Google Cloud Storage
- **Network**: Private VPC with Cloud SQL (PostgreSQL) and GKE Autopilot cluster in us-west2
- **Backend**: Python FastAPI application with ML-powered resume parsing and job matching
- **Frontend**: React SPA with Firebase Authentication
- **Functions**: Cloud Function for bursty PDF-to-JSON resume processing
- **Storage**: Artifact Registry for container images, Secret Manager for sensitive data
- **CI/CD**: GitHub Actions with OIDC authentication for automated deployments
- **Observability**: Cloud Logging/Monitoring with managed Prometheus

## Features

- 🔐 **Firebase Authentication** - Secure user authentication
- 📄 **Resume Parsing** - AI-powered extraction of skills, experience, and contact info
- 🎯 **Job Matching** - ML algorithms to match resumes with relevant job opportunities
- ⚡ **Serverless Processing** - Cloud Functions for scalable document processing
- 📊 **Monitoring** - Comprehensive observability with Prometheus metrics
- 🚀 **Auto-scaling** - Kubernetes HPA for dynamic scaling based on load
- 🔒 **Security** - Private networking, secret management, and RBAC

## Prerequisites

1. **GCP Project** with billing enabled
2. **Domain name** (optional, for custom domain)
3. **GitHub repository** for CI/CD
4. **Firebase project** for authentication

### Required GCP APIs

Enable the following APIs in your GCP project:

```bash
gcloud services enable \
  container.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  compute.googleapis.com \
  servicenetworking.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com
```

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/your-username/job-matcher.git
cd job-matcher
```

### 2. Configure Terraform Variables

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
project_id              = "your-gcp-project-id"
region                  = "us-west2"
zone                    = "us-west2-a"
terraform_state_bucket  = "your-terraform-state-bucket"
environment            = "prod"
app_name               = "job-matcher"
db_password            = "your-secure-database-password"
```

### 3. Create GCS Bucket for Terraform State

```bash
gsutil mb gs://your-terraform-state-bucket
gsutil versioning set on gs://your-terraform-state-bucket
```

### 4. Deploy Infrastructure

```bash
terraform init
terraform plan
terraform apply
```

### 5. Setup Secrets

```bash
# Run the setup script
./scripts/setup-secrets.sh your-project-id us-west2

# Add your Firebase config
gcloud secrets versions add job-matcher-firebase-config --data-file=path/to/firebase-config.json

# Set database password
echo 'your-secure-db-password' | gcloud secrets versions add job-matcher-db-password --data-file=-
```

### 6. Configure GitHub Actions

Add the following secrets to your GitHub repository:

- `GCP_PROJECT_ID`: Your GCP project ID
- `TERRAFORM_STATE_BUCKET`: Your Terraform state bucket name
- `DB_PASSWORD`: Your database password
- `WIF_PROVIDER`: Workload Identity Federation provider
- `WIF_SERVICE_ACCOUNT`: Service account email for GitHub Actions

### 7. Setup Workload Identity Federation

```bash
# Create a service account for GitHub Actions
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions"

# Grant necessary permissions
gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:github-actions@your-project-id.iam.gserviceaccount.com" \
    --role="roles/container.developer"

gcloud projects add-iam-policy-binding your-project-id \
    --member="serviceAccount:github-actions@your-project-id.iam.gserviceaccount.com" \
    --role="roles/cloudsql.admin"

# Setup Workload Identity Federation (follow GCP documentation)
```

### 8. Deploy Application

## Local Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Set environment variables
export PROJECT_ID=your-project-id
export DATABASE_URL=postgresql://user:pass@localhost:5432/job_matcher
export FIREBASE_PROJECT_ID=your-firebase-project

uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install

# Create .env file with your Firebase config
cp .env.example .env

npm start
```

### Running with Docker Compose (Local)

```bash
# Create a local docker-compose.yml for development
docker-compose up -d
```

## API Documentation

Once deployed, access the API documentation at:
- **Swagger UI**: `https://your-domain/docs`
- **ReDoc**: `https://your-domain/redoc`

### Key Endpoints

- `POST /api/v1/resumes/upload` - Upload resume file
- `POST /api/v1/resumes/{id}/parse` - Parse uploaded resume
- `POST /api/v1/matches/{resume_id}` - Find job matches
- `GET /api/v1/jobs/` - List job opportunities
- `GET /metrics` - Prometheus metrics

## Monitoring and Observability

### Accessing Metrics

- **Prometheus**: Available through managed Prometheus in GKE
- **Grafana**: Deploy using Helm or use Google Cloud Monitoring
- **Logs**: Google Cloud Logging console

### Key Metrics

- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency
- `resume_parsing_duration_seconds` - Resume parsing time
- `job_matching_duration_seconds` - Job matching time

### Alerts

Pre-configured alerts for:
- High error rates (>10%)
- High latency (>500ms P95)
- Pod crash loops
- Database connection failures

## Scaling and Performance

### Horizontal Pod Autoscaling

The application automatically scales based on:
- CPU utilization (target: 70%)
- Memory utilization (target: 80%)

### Database Scaling

- Cloud SQL automatic storage scaling
- Read replicas can be added for read-heavy workloads
- Connection pooling configured in the application

### Function Scaling

Cloud Functions automatically scale based on incoming requests with:
- Max instances: 10
- Concurrency: 1 (for PDF processing)

## Security

### Network Security

- Private GKE cluster with authorized networks
- Cloud SQL with private IP only
- VPC with custom subnets and firewall rules

### Authentication & Authorization

- Firebase Authentication for users
- Workload Identity for GKE pods
- Service accounts with least privilege access

### Secrets Management

- All secrets stored in Google Secret Manager
- Automatic secret rotation supported
- No secrets in code or configuration files

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   ```bash
   kubectl logs -n job-matcher deployment/job-matcher-backend
   ```

2. **Resume Parsing Errors**
   ```bash
   gcloud functions logs read resume-parser --region=us-west2
   ```

3. **Frontend Not Loading**
   ```bash
   kubectl describe ingress job-matcher-ingress -n job-matcher
   ```

### Debugging Commands

```bash
# Check pod status
kubectl get pods -n job-matcher

# View logs
kubectl logs -f deployment/job-matcher-backend -n job-matcher

# Check service endpoints
kubectl get endpoints -n job-matcher

# Verify secrets
kubectl get secrets -n job-matcher
```

## Cost Optimization

### Estimated Monthly Costs

- **GKE Autopilot**: $20-50 (based on usage)
- **Cloud SQL**: $25-40 (db-f1-micro)
- **Cloud Functions**: $1-5 (based on invocations)
- **Storage**: $1-3 (Artifact Registry + GCS)
- **Networking**: $5-10 (NAT Gateway + Load Balancer)

**Total**: ~$50-100/month for moderate usage

### Cost Reduction Tips

1. Use preemptible nodes for non-production environments
2. Implement lifecycle policies for Artifact Registry
3. Use Cloud SQL scheduled backups instead of continuous
4. Monitor and set up billing alerts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 for Python code
- Use ESLint configuration for TypeScript/React
- Write meaningful commit messages
- Update documentation for new features

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
1. Check the [troubleshooting section](#troubleshooting)
2. Review [GitHub Issues](https://github.com/your-username/job-matcher/issues)
3. Create a new issue with detailed information

---

**Built with ❤️ using Google Cloud Platform**
