# Deploying Audio Instruction to Google Cloud Run

This guide will walk you through deploying the Audio Instruction API to Google Cloud Run, a serverless platform that automatically scales your containerized applications.

## Prerequisites

1. A Google Cloud Platform (GCP) account
2. Google Cloud SDK installed locally (`gcloud` command-line tool)
3. Docker installed locally

## Step 1: Set Up Your Google Cloud Project

```bash
# Create a new project (or use an existing one)
gcloud projects create audio-instruction-app --name="Audio Instruction"

# Set the project as active
gcloud config set project audio-instruction-app

# Enable required services
gcloud services enable \
  containerregistry.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com
```

## Step 2: Build and Push the Docker Image

```bash
# Navigate to your audio-instruction repository
cd /path/to/audio-instruction

# Build the Docker image
docker build -t gcr.io/audio-instruction-app/audio-instruction:v1 .

# Authenticate to Google Container Registry
gcloud auth configure-docker

# Push the image to Google Container Registry
docker push gcr.io/audio-instruction-app/audio-instruction:v1
```

## Step 3: Deploy to Cloud Run

```bash
# Deploy the service
gcloud run deploy audio-instruction \
  --image gcr.io/audio-instruction-app/audio-instruction:v1 \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300s \
  --concurrency 80
```

This command:
- Names the service "audio-instruction"
- Uses your Docker image
- Deploys to the "us-central1" region
- Allows public access without authentication
- Allocates 1GB of memory and 1 CPU
- Sets a 5-minute timeout for requests
- Allows up to 80 concurrent requests per instance

## Step 4: Set Up a Custom Domain (Optional)

If you want to use a custom domain:

```bash
# Map your custom domain
gcloud beta run domain-mappings create \
  --service audio-instruction \
  --domain api.yourdomain.com \
  --region us-central1
```

Then follow the DNS verification steps provided by the command output.

## Step 5: Setting Up Cloud Storage for Caching (Optional)

For improved performance, you can use Cloud Storage to cache generated audio files:

```bash
# Create a bucket
gsutil mb -l us-central1 gs://audio-instruction-cache

# Grant access to the Cloud Run service account
gcloud run services describe audio-instruction \
  --region us-central1 \
  --format="value(status.serviceAccountName)" > service_account.txt

gsutil iam ch serviceAccount:$(cat service_account.txt):objectAdmin gs://audio-instruction-cache
```

Then update your deployment with environment variables:

```bash
gcloud run services update audio-instruction \
  --region us-central1 \
  --set-env-vars="CACHE_BUCKET=audio-instruction-cache,CACHE_ENABLED=true"
```

## Step 6: Setting Up Health Checks and Monitoring

Use Cloud Monitoring to set up health checks:

1. Go to the [Cloud Monitoring Console](https://console.cloud.google.com/monitoring)
2. Create an uptime check for your service's `/health` endpoint
3. Set up alerts for when the service becomes unhealthy

## Testing Your Deployment

Once deployed, you can test your API:

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe audio-instruction --region us-central1 --format="value(status.url)")

# Test with a simple curl request
curl -X POST "$SERVICE_URL/workout" \
  -H "Content-Type: application/json" \
  -d '{
    "instructions": [
      {"text": "Test exercise", "duration_seconds": 10}
    ],
    "language": "en"
  }' \
  --output test.mp3
```

## Continuous Deployment with Cloud Build (Optional)

Set up automatic deployments from your Git repository:

1. Connect your GitHub/GitLab/Bitbucket repository to Cloud Build
2. Create a `cloudbuild.yaml` file in your repository:

```yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/$PROJECT_ID/audio-instruction:$COMMIT_SHA', '.']
- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/$PROJECT_ID/audio-instruction:$COMMIT_SHA']
- name: 'gcr.io/cloud-builders/gcloud'
  args:
  - 'run'
  - 'deploy'
  - 'audio-instruction'
  - '--image'
  - 'gcr.io/$PROJECT_ID/audio-instruction:$COMMIT_SHA'
  - '--region'
  - 'us-central1'
  - '--platform'
  - 'managed'
images:
- 'gcr.io/$PROJECT_ID/audio-instruction:$COMMIT_SHA'
```

3. Set up a trigger in Cloud Build to run this configuration on new commits

## Cost Considerations

Cloud Run charges based on:
- Number of requests
- Resources allocated per instance
- Instance time

The service will scale down to zero when not in use, meaning you only pay when the service is processing requests.

## Troubleshooting

If you encounter issues:

1. Check Cloud Run logs in the Google Cloud Console
2. Ensure all required environment variables are set
3. Check that your service has the necessary permissions
4. Verify that FFmpeg and other dependencies are properly installed in the Docker image

## Next Steps

- Set up CI/CD pipelines for automated testing and deployment
- Implement caching strategies for frequently requested workout combinations
- Add authentication for production use
- Set up rate limiting to prevent abuse 