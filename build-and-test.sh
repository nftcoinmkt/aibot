#!/bin/bash

# Build and test script for Flutter AI Bot
# This script helps you build the app locally before deploying via GitHub Actions

set -e

echo "🚀 Building Flutter AI Bot for Android..."

# Navigate to Flutter project
cd flutter_ai_bot

# Clean previous builds
echo "🧹 Cleaning previous builds..."
flutter clean
flutter pub get

# Build APK for testing
echo "📱 Building debug APK..."
flutter build apk --debug

# Build AAB for Play Store
echo "📦 Building release AAB..."
flutter build appbundle --release \
  --dart-define=API_BASE_URL=https://your-api-url.com \
  --dart-define=ENVIRONMENT=production

echo "✅ Build completed!"
echo ""
echo "📁 Files created:"
echo "  - Debug APK: build/app/outputs/flutter-apk/app-debug.apk"
echo "  - Release AAB: build/app/outputs/bundle/release/app-release.aab"
echo ""
echo "📋 Next steps:"
echo "1. Test the debug APK on your device"
echo "2. Upload the AAB to Google Play Console manually first"
echo "3. Once the app exists in Play Console, use GitHub Actions for automated deployment"
