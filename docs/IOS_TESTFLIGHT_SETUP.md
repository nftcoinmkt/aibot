# iOS TestFlight GitHub Actions Setup

This document outlines the setup required for the iOS TestFlight deployment workflow.

## Required GitHub Secrets

You need to configure the following secrets in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

### Apple Developer Account Secrets

1. **`APPLE_ID`**
   - Your Apple ID email address
   - Used for App Store Connect authentication

2. **`APPLE_APP_SPECIFIC_PASSWORD`**
   - Generate this in your Apple ID account settings
   - Go to https://appleid.apple.com > Sign-In and Security > App-Specific Passwords
   - Create a new password specifically for this CI/CD workflow

3. **`APPLE_TEAM_ID`**
   - Your Apple Developer Team ID
   - Find this in Apple Developer Portal > Membership tab
   - Format: `XXXXXXXXXX` (10 characters)

### Code Signing Secrets

4. **`BUILD_CERTIFICATE_BASE64`**
   - Base64 encoded iOS Distribution certificate (.p12 file)
   - Export your distribution certificate from Keychain Access
   - Convert to base64: `base64 -i certificate.p12 | pbcopy`

5. **`P12_PASSWORD`**
   - Password for the .p12 certificate file
   - Set when exporting the certificate from Keychain Access

6. **`BUILD_PROVISION_PROFILE_BASE64`**
   - Base64 encoded provisioning profile (.mobileprovision file)
   - Download from Apple Developer Portal
   - Convert to base64: `base64 -i profile.mobileprovision | pbcopy`

7. **`KEYCHAIN_PASSWORD`**
   - A secure password for the temporary keychain
   - Can be any strong password (generated randomly)

## iOS Project Configuration

### 1. Bundle Identifier
Ensure your iOS app has a unique bundle identifier configured in:
- `flutter_ai_bot/ios/Runner/Info.plist`
- Apple Developer Portal (App IDs)
- App Store Connect

### 2. Provisioning Profile
- Create an App Store distribution provisioning profile
- Include your distribution certificate
- Match the bundle identifier exactly

### 3. ExportOptions.plist
The workflow will create this automatically, but you can customize it by creating:
`flutter_ai_bot/ios/Runner/ExportOptions.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>app-store</string>
    <key>uploadBitcode</key>
    <false/>
    <key>uploadSymbols</key>
    <true/>
    <key>compileBitcode</key>
    <false/>
    <key>teamID</key>
    <string>YOUR_TEAM_ID</string>
</dict>
</plist>
```

## App Store Connect Setup

1. **Create App Record**
   - Log into App Store Connect
   - Create a new app with matching bundle identifier
   - Fill in required app information

2. **TestFlight Configuration**
   - Enable TestFlight for your app
   - Configure test information and compliance settings
   - Add internal testers if needed

## Workflow Triggers

The workflow can be triggered:

1. **Manual Dispatch**: Use the "Actions" tab in GitHub to run manually
2. **Push to Main**: Uncomment the push trigger in the workflow file
3. **Pull Request**: Uncomment the PR trigger for testing builds

## Build Number Management

- Build numbers auto-increment using GitHub run number
- Override with manual input when triggering workflow dispatch
- Version number is managed in `pubspec.yaml`

## Troubleshooting

### Common Issues

1. **Certificate/Profile Mismatch**
   - Ensure certificate and provisioning profile are for the same team
   - Verify bundle identifier matches exactly

2. **Keychain Issues**
   - Check that certificate is properly imported
   - Verify keychain password is correct

3. **Upload Failures**
   - Verify Apple ID credentials
   - Check that app record exists in App Store Connect
   - Ensure compliance settings are configured

### Debug Steps

1. Check workflow logs for specific error messages
2. Verify all secrets are properly set
3. Test certificate/profile locally in Xcode first
4. Ensure App Store Connect app is properly configured

## Security Notes

- Never commit certificates or provisioning profiles to version control
- Use strong passwords for keychain and certificate
- Regularly rotate app-specific passwords
- Review and audit access to GitHub secrets regularly


MIIMsQIBAzCCDHgGCSqGSIb3DQEHAaCCDGkEggxlMIIMYTCCBucGCSqGSIb3DQEHBqCCBtgwggbUAgEAMIIGzQYJKoZIhvcNAQcBMBwGCiqGSIb3DQEMAQYwDgQIYRzDVulOjIQCAggAgIIGoJdfHQpewJKfxR2xzpdjjzR6ZVVmXDI+VxZu7b8z7XdcZlr1d4Zgj2qM0EOvtH49YZdZ/K8oyB98WJfwvFMNGunzwBy1bfdmX+X4FGTQEpwld/q7TaHnVcj4ebnh5nz0I3RmdvuyELv5pSf5vHm4jXqK9JSt+POa8iWr0BZXirb1RLKbVvzshNUkZP1oclJowAF6Y5FGAWJzaDPRHwlYR4scJ7q+1h6o1ZaypsrlhIN0B5vQiY0Nr2b4TqKbX7QvouM+jAB6HhIQHpu3b/hPhDQQ7BKXuhvLXnZAJcK1eWJGdNSC3yLHGkwi0NENw160xBZ5qR4+sQ1hN76nVuO+7s6bwESo8YnaHe0Y
vzi-tkdh-nib