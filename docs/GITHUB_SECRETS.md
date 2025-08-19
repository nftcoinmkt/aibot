# GitHub Secrets Configuration

This document lists all the GitHub secrets required for the CI/CD pipeline and data seeding.

## 🔐 Required Secrets

### **GCP Authentication**
- `GCP_PROJECT_ID` - Your Google Cloud Project ID
- `GCP_SA_KEY` - Service Account JSON key for GitHub Actions

### **Production Configuration**
- `ADMIN_PASSWORD` - Secure password for production admin user
- `SECRET_KEY` - JWT secret key for authentication
- `GEMINI_API_KEY` - Google Gemini API key for AI features
- `GROQ_API_KEY` - Groq API key for AI features

## 🛠️ Setting Up Secrets

### **1. In GitHub Repository:**
1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with its value

### **2. GCP Service Account Setup:**
```bash
# Create service account
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions"

# Grant necessary roles
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:github-actions@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:github-actions@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:github-actions@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
    --iam-account=github-actions@PROJECT_ID.iam.gserviceaccount.com

# Copy the contents of github-actions-key.json to GCP_SA_KEY secret
```

### **3. Generate Secure Passwords:**
```bash
# Generate admin password
openssl rand -base64 32

# Generate JWT secret key
openssl rand -base64 64
```

## 🌱 Data Seeding Secrets

The following secrets are used specifically for data seeding:

- `ADMIN_PASSWORD` - Production admin password (required for production seeding)
- `GCP_PROJECT_ID` - Used to determine Cloud Run service URL
- `GCP_SA_KEY` - Used to authenticate with GCP services

## 🔄 Workflow Triggers

### **Automatic Seeding:**
- Triggers after successful deployment to main branch
- Only seeds if no existing data is found

### **Manual Seeding:**
- Can be triggered manually from GitHub Actions tab
- Allows choosing environment (staging/production)
- Has option to force reseed (recreate all data)

## 🚨 Security Notes

1. **Never commit secrets** to the repository
2. **Rotate secrets regularly** especially for production
3. **Use least privilege** for service account permissions
4. **Monitor secret usage** in GitHub Actions logs
5. **Change default passwords** after first deployment

## 📋 Secret Validation

Use this checklist to ensure all secrets are properly configured:

- [ ] `GCP_PROJECT_ID` - Valid GCP project ID
- [ ] `GCP_SA_KEY` - Valid JSON service account key
- [ ] `ADMIN_PASSWORD` - Strong password (min 12 characters)
- [ ] `SECRET_KEY` - Random 64-character base64 string
- [ ] `GEMINI_API_KEY` - Valid Google AI API key
- [ ] `GROQ_API_KEY` - Valid Groq API key

## 🔍 Troubleshooting

### **Common Issues:**

1. **Invalid GCP_SA_KEY:**
   - Ensure JSON is properly formatted
   - Check service account has required permissions

2. **Missing ADMIN_PASSWORD:**
   - Required for production seeding
   - Must be set as GitHub secret

3. **Wrong GCP_PROJECT_ID:**
   - Must match your actual GCP project
   - Check project ID in GCP console

4. **API Key Issues:**
   - Ensure API keys are valid and active
   - Check quota limits for AI services
