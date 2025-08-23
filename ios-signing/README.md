# iOS Signing Files Directory

This directory is used for temporarily uploading iOS signing files to generate base64 encodings for GitHub Secrets.

## Usage

1. **Upload your files here:**
   - `certificate.p12` - Your iOS Distribution certificate
   - `profile.mobileprovision` - Your App Store provisioning profile

2. **Run the workflow:**
   - Go to Actions tab in GitHub
   - Run "Generate Base64 Secrets for iOS Signing" workflow

3. **Copy the base64 strings:**
   - Copy the generated base64 strings from the workflow logs
   - Add them to your GitHub repository secrets

4. **🚨 IMPORTANT: Clean up**
   - Delete both files from this directory after use
   - Never commit certificates or provisioning profiles to version control

## Required GitHub Secrets

After running the workflow, you'll need these secrets in your repository:

- `BUILD_CERTIFICATE_BASE64` - Base64 encoded certificate
- `BUILD_PROVISION_PROFILE_BASE64` - Base64 encoded provisioning profile
- `P12_PASSWORD` - Password for your .p12 certificate
- `KEYCHAIN_PASSWORD` - Any secure password for temporary keychain
- `APPLE_ID` - Your Apple ID email
- `APPLE_APP_SPECIFIC_PASSWORD` - App-specific password from Apple ID
- `APPLE_TEAM_ID` - Your Apple Developer Team ID

## Security Notes

- Files in this directory should only exist temporarily
- Always delete sensitive files after generating base64 strings
- Use strong passwords for certificates and keychains
- Regularly rotate app-specific passwords
