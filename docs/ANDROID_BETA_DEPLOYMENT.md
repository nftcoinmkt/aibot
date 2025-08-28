# Android Beta Deployment Guide

This guide explains how to set up and use the automated Android beta deployment workflow for the AI Bot Flutter app.

## 📱 Overview

The GitHub Actions workflow (`android-beta-deploy.yml`) automatically:
- Builds Flutter Android APK and AAB files
- Signs the app with your production keystore
- Uploads to Google Play Store beta track for open testing
- Creates GitHub releases with downloadable artifacts
- Handles versioning automatically

## 🚀 Quick Start

### 1. Prerequisites

- Google Play Console account with app registered
- Android keystore file for app signing
- Google Cloud service account with Play Console access

### 2. Setup GitHub Secrets

Go to your repository **Settings → Secrets and variables → Actions** and add:

#### Android Signing Secrets
```
ANDROID_KEYSTORE_BASE64     # Base64 encoded keystore file
ANDROID_KEYSTORE_PASSWORD   # Keystore password
ANDROID_KEY_PASSWORD        # Key password
ANDROID_KEY_ALIAS          # Key alias name
```

#### Google Play Store Secrets
```
GOOGLE_PLAY_SERVICE_ACCOUNT_JSON  # Service account JSON key
ANDROID_PACKAGE_NAME             # App package name (e.g., com.yourcompany.aibot)
```

#### App Configuration
```
API_BASE_URL  # Your backend API URL (e.g., https://your-api.com)
```

### 3. Run Deployment

**Manual Trigger:**
1. Go to **Actions** tab in GitHub
2. Select **"Android Beta Build and Deploy"**
3. Click **"Run workflow"**
4. Enter version name and code
5. Click **"Run workflow"**

**Automatic Trigger:**
- Push to `main` branch with changes in `flutter_ai_bot/` directory
- Create a version tag (e.g., `v1.0.0`)

## 🔧 Detailed Setup

### Creating Android Keystore

If you don't have a keystore file:

```bash
keytool -genkey -v -keystore upload-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias upload
```

**Important:** Save the passwords and alias name - you'll need them for GitHub Secrets.

### Converting Keystore to Base64

```bash
# Linux/macOS
base64 -w 0 upload-keystore.jks

# Windows (PowerShell)
[Convert]::ToBase64String([IO.File]::ReadAllBytes("upload-keystore.jks"))
```
keytool -genkey -v -keystore upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload


Copy the output to `ANDROID_KEYSTORE_BASE64` secret.

### Google Play Console Setup

1. **Create Service Account:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create new project or select existing
   - Enable Google Play Developer API
   - Create service account with "Service Account User" role
   - Download JSON key file

2. **Link to Play Console:**
   - Go to [Play Console](https://play.google.com/console/)
   - **Setup → API access**
   - Link the service account
   - Grant permissions: "Release to testing tracks"

3. **Add JSON to GitHub:**
   - Copy entire JSON file content
   - Paste into `GOOGLE_PLAY_SERVICE_ACCOUNT_JSON` secret

### App Package Name

Find your package name in `flutter_ai_bot/android/app/build.gradle`:

```gradle
android {
    namespace "com.example.flutter_ai_bot"  // This is your package name
    // ...
}
```

## 📋 Workflow Features

### Build Process
- ✅ Flutter stable channel
- ✅ Java 17 for Android builds
- ✅ Dependency caching for faster builds
- ✅ Automated testing (if tests exist)
- ✅ Production environment variables

### Signing & Security
- ✅ Secure keystore handling
- ✅ Automatic APK signing
- ✅ Keystore cleanup after build
- ✅ No sensitive data in logs

### Play Store Upload
- ✅ Beta track deployment
- ✅ 100% rollout to beta testers
- ✅ Automatic release notes
- ✅ Mapping file upload for crash reports

### Artifacts
- ✅ Signed APK for direct installation
- ✅ AAB file for Play Store
- ✅ GitHub release creation
- ✅ 30-day artifact retention

## 🔄 Versioning

### Manual Versioning
When running workflow manually, specify:
- **Version Name**: Semantic version (e.g., `1.2.0`)
- **Version Code**: Integer build number (e.g., `42`)

### Automatic Versioning
- **Version Code**: Uses GitHub run number
- **Version Name**: Extracted from git tag or defaults to `1.0.0`

### Version Format
Final version in `pubspec.yaml`: `version: 1.2.0+42`
- `1.2.0` = Version name (user-facing)
- `42` = Version code (internal build number)

## 📁 File Structure

```
.github/workflows/
├── android-beta-deploy.yml     # Main deployment workflow

metadata/android/
└── en-US/changelogs/
    └── default.txt            # Release notes for Play Store

flutter_ai_bot/
├── android/
│   ├── app/
│   │   └── upload-keystore.jks # Created during build (temporary)
│   └── key.properties         # Created during build (temporary)
└── pubspec.yaml              # Version updated during build
```

## 🐛 Troubleshooting

### Common Issues

**Build Fails - Dependencies**
```bash
# Solution: Update Flutter dependencies
flutter pub get
flutter pub upgrade
```

**Signing Fails - Keystore**
- Verify `ANDROID_KEYSTORE_BASE64` is correct
- Check keystore passwords match
- Ensure key alias exists in keystore

**Upload Fails - Play Console**
- Verify service account has correct permissions
- Check package name matches exactly
- Ensure app exists in Play Console

**Version Conflicts**
- Increment version code for each upload
- Version code must be higher than previous uploads

### Debug Steps

1. **Check workflow logs** in Actions tab
2. **Verify all secrets** are set correctly
3. **Test keystore locally:**
   ```bash
   keytool -list -v -keystore upload-keystore.jks
   ```
4. **Validate service account:**
   ```bash
   gcloud auth activate-service-account --key-file=service-account.json
   ```

## 📊 Monitoring

### Success Indicators
- ✅ Green checkmark in Actions tab
- ✅ New release in GitHub Releases
- ✅ APK/AAB artifacts available
- ✅ App appears in Play Console beta track

### Beta Testing
- Share beta link with testers
- Monitor crash reports in Play Console
- Collect feedback before production release

## 🔐 Security Best Practices

- ✅ Keystore passwords stored as GitHub Secrets
- ✅ Service account JSON encrypted
- ✅ Temporary files cleaned up after build
- ✅ No sensitive data in workflow logs
- ✅ Limited service account permissions

## 📞 Support

For issues with this deployment workflow:
1. Check the troubleshooting section above
2. Review workflow logs in GitHub Actions
3. Verify all prerequisites are met
4. Ensure all secrets are correctly configured

---

**Last Updated:** $(date)
**Workflow Version:** 1.0.0
keytool -genkey -v -keystore upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload
aibot@321
nextai
 base64 -w 0 upload-keystore.jks
ANDROID_KEY_ALIAS=upload
ANDROID_KEYSTORE_PASSWORD=aibot@321
ANDROID_KEY_PASSWORD=aibot@321