#!/bin/bash

# Setup script for Job Finder Service
# This script configures the necessary secrets and environment variables

set -e

PROJECT_ID=${1:-$(gcloud config get-value project)}
REGION=${2:-us-west2}

if [ -z "$PROJECT_ID" ]; then
    echo "Error: PROJECT_ID is required"
    echo "Usage: $0 <PROJECT_ID> [REGION]"
    exit 1
fi

echo "Setting up Job Finder Service for project: $PROJECT_ID in region: $REGION"

# Create ATS API keys secret
echo "Creating ATS API keys secret..."
cat > /tmp/ats-api-keys.json << EOF
{
    "greenhouse": "",
    "lever": "",
    "ashby": "",
    "smartrecruiters": "",
    "adzuna_app_id": "",
    "adzuna_app_key": ""
}
EOF

gcloud secrets versions add job-matcher-ats-api-keys \
    --data-file=/tmp/ats-api-keys.json \
    --project=$PROJECT_ID

# Create Vertex AI key secret (project ID)
echo "Creating Vertex AI key secret..."
echo "$PROJECT_ID" | gcloud secrets versions add job-matcher-vertex-ai-key \
    --data-file=- \
    --project=$PROJECT_ID

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable \
    aiplatform.googleapis.com \
    run.googleapis.com \
    cloudscheduler.googleapis.com \
    vpcaccess.googleapis.com \
    --project=$PROJECT_ID

# Grant necessary IAM roles to the service account
echo "Granting IAM roles..."
SERVICE_ACCOUNT="job-matcher-app@$PROJECT_ID.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/run.invoker"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor"

# Create Cloud Scheduler service account
echo "Creating Cloud Scheduler service account..."
gcloud iam service-accounts create job-matcher-scheduler \
    --display-name="Job Matcher Scheduler" \
    --project=$PROJECT_ID

SCHEDULER_SA="job-matcher-scheduler@$PROJECT_ID.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SCHEDULER_SA" \
    --role="roles/run.invoker"

# Update the target companies list
echo "Updating target companies configuration..."
cat > /tmp/target-companies.json << EOF
[
    "google", "microsoft", "amazon", "meta", "apple", "netflix", "airbnb",
    "uber", "lyft", "stripe", "square", "plaid", "robinhood", "coinbase",
    "databricks", "snowflake", "mongodb", "elastic", "confluent", "hashicorp",
    "github", "gitlab", "atlassian", "slack", "zoom", "salesforce", "adobe",
    "intel", "nvidia", "amd", "qualcomm", "broadcom", "cisco", "oracle",
    "vmware", "redhat", "canonical", "docker", "hashicorp", "paloaltonetworks"
]
EOF

gcloud secrets create job-matcher-target-companies \
    --data-file=/tmp/target-companies.json \
    --project=$PROJECT_ID

gcloud secrets add-iam-policy-binding job-matcher-target-companies \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$PROJECT_ID

# Clean up temporary files
rm -f /tmp/ats-api-keys.json /tmp/target-companies.json

echo "Job Finder Service setup complete!"
echo ""
echo "Next steps:"
echo "1. Update the ATS API keys in Secret Manager:"
echo "   gcloud secrets versions add job-matcher-ats-api-keys --data-file=your-keys.json"
echo ""
echo "2. Deploy the infrastructure:"
echo "   cd infra && terraform apply"
echo ""
echo "3. Build and deploy the job finder service:"
echo "   docker build -t gcr.io/$PROJECT_ID/job-finder:latest ./job-finder"
echo "   docker push gcr.io/$PROJECT_ID/job-finder:latest"
echo ""
echo "4. Deploy to Cloud Run:"
echo "   gcloud run deploy job-finder --image=gcr.io/$PROJECT_ID/job-finder:latest --region=$REGION"
echo ""
echo "5. Test the service:"
echo "   curl -X POST https://job-finder-xxxxx-uc.a.run.app/jobs/live -H 'Content-Type: application/json' -d '{\"resume_text\":\"test\",\"location\":\"US\"}'"
