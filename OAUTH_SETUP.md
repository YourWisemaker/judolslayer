# OAuth2 Setup Guide for YouTube Comment Deletion

This guide explains how to set up OAuth2 authentication to enable comment deletion functionality.

## Prerequisites

- Google Cloud Console account
- YouTube channel (the authenticated user must own the videos to delete comments)

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID

## Step 2: Enable YouTube Data API v3

1. In Google Cloud Console, go to "APIs & Services" > "Library"
2. Search for "YouTube Data API v3"
3. Click on it and press "Enable"

## Step 3: Create OAuth2 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "+ CREATE CREDENTIALS" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in required fields (App name, User support email, Developer contact)
   - Add scopes: `https://www.googleapis.com/auth/youtube.force-ssl`
   - Add test users (your email) if in testing mode

4. For OAuth client ID:
   - Application type: "Web application"
   - Name: "YouTube Spam Detector"
   - Authorized redirect URIs: `http://localhost:5001/oauth/callback`

5. Download the JSON file and save it as `client_secrets.json` in the backend directory

## Step 4: Configure Environment Variables

1. Copy the template: `cp client_secrets_template.json client_secrets.json`
2. Replace the values in `client_secrets.json` with your actual credentials
3. Update `.env` file with your configuration:

```env
# OAuth2 Configuration
GOOGLE_CLIENT_SECRETS_FILE=client_secrets.json
OAUTH_REDIRECT_URI=http://localhost:5001/oauth/callback
FRONTEND_URL=http://localhost:3000
FLASK_SECRET_KEY=your-secure-random-key-here
```

## Step 5: Generate Secure Secret Key

Generate a secure secret key for Flask sessions:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Replace `your-secure-random-key-here` in `.env` with the generated key.

## Step 6: Test OAuth Flow

1. Start the backend server:
   ```bash
   cd backend
   python app_enhanced.py
   ```

2. Test authentication endpoints:
   - GET `/api/auth/status` - Check auth status
   - GET `/api/auth/login` - Get authorization URL
   - GET `/oauth/callback` - OAuth callback (handled automatically)
   - POST `/api/auth/logout` - Logout

## Step 7: Frontend Integration

The frontend needs to be updated to handle OAuth flow:

1. Add authentication UI components
2. Handle OAuth redirects
3. Store authentication state
4. Show/hide deletion features based on auth status

## Security Considerations

1. **Client Secrets**: Never commit `client_secrets.json` to version control
2. **Credentials Storage**: The app stores OAuth tokens in `credentials.json` (also excluded from git)
3. **HTTPS in Production**: Use HTTPS for OAuth redirects in production
4. **Scope Limitation**: Only request necessary scopes (`youtube.force-ssl`)
5. **Token Refresh**: The app automatically refreshes expired tokens

## Troubleshooting

### Common Issues

1. **"redirect_uri_mismatch" error**:
   - Ensure the redirect URI in Google Console exactly matches your `.env` configuration
   - Check for trailing slashes or protocol mismatches

2. **"invalid_client" error**:
   - Verify `client_secrets.json` contains correct credentials
   - Ensure the file path in `.env` is correct

3. **"access_denied" error**:
   - User denied permission during OAuth flow
   - Check OAuth consent screen configuration

4. **"insufficient_permissions" error**:
   - Ensure the authenticated user owns the YouTube channel
   - Verify the `youtube.force-ssl` scope is included

### Testing OAuth Flow

```bash
# Check auth status
curl http://localhost:5001/api/auth/status

# Get login URL
curl http://localhost:5001/api/auth/login

# Test comment deletion (requires authentication)
curl -X POST http://localhost:5001/api/delete-comment \
  -H "Content-Type: application/json" \
  -d '{"comment_id": "COMMENT_ID_HERE"}'
```

## API Endpoints

### Authentication Endpoints

- `GET /api/auth/status` - Check authentication status
- `GET /api/auth/login` - Get OAuth authorization URL
- `GET /oauth/callback` - OAuth callback handler
- `POST /api/auth/logout` - Logout and clear credentials

### Comment Management

- `POST /api/delete-comment` - Delete a specific comment (requires auth)
- `POST /api/process-video` - Process video with deletion (requires auth if dry_run=false)

## Production Deployment

For production deployment:

1. Update redirect URIs in Google Console to use your production domain
2. Use HTTPS for all OAuth redirects
3. Set `FLASK_ENV=production` in environment
4. Use a secure session secret key
5. Consider using a proper session store (Redis, database) instead of file-based storage

## Rate Limits

YouTube API has rate limits:
- Comment deletion: 1 request per second (implemented in the code)
- Daily quota limits apply (check Google Cloud Console)

## Support

If you encounter issues:
1. Check the backend logs for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure Google Cloud project has proper API access
4. Test with a simple OAuth flow first before full integration