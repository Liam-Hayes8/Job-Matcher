#!/bin/bash

set -e

PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"us-west2"}

echo "Setting up secrets for project: $PROJECT_ID"

echo "Creating Firebase config secret..."
gcloud secrets create job-matcher-firebase-config \
    --project=$PROJECT_ID \
    --replication-policy="automatic" || echo "Secret already exists"

echo "Creating JWT secret..."
gcloud secrets create job-matcher-jwt-secret \
    --project=$PROJECT_ID \
    --replication-policy="automatic" || echo "Secret already exists"

echo "Setting up database password secret..."
gcloud secrets create job-matcher-db-password \
    --project=$PROJECT_ID \
    --replication-policy="automatic" || echo "Secret already exists"

echo "Setting up service account permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:job-matcher-app@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" || echo "Permission already exists"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:job-matcher-function@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" || echo "Permission already exists"

echo "Secrets setup complete!"
echo ""
echo "Next steps:"
echo "1. Add your Firebase config JSON to the job-matcher-firebase-config secret"
echo "2. Set a secure database password in the job-matcher-db-password secret"
echo ""
echo "Example commands:"
echo "echo 'your-secure-db-password' | gcloud secrets versions add job-matcher-db-password --data-file=-"
echo "gcloud secrets versions add job-matcher-firebase-config --data-file=path/to/firebase-config.json"