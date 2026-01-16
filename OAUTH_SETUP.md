# Gmail OAuth2 Setup Guide

This application now uses Gmail OAuth2 instead of SMTP for sending emails. This provides better security and doesn't require app passwords.

## Setup Steps

### 1. Get Google OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Gmail API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"

4. Create OAuth2 Credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, configure OAuth consent screen first:
     - User Type: External (for testing) or Internal (for organization)
     - App name: "AI Job Seeker Agent"
     - User support email: Your email
     - Developer contact: Your email
     - Click "Save and Continue"
     - Scopes: Add `https://www.googleapis.com/auth/gmail.send`
     - Click "Save and Continue"
     - Add test users (your email) if using External
     - Click "Save and Continue"
   
5. Create OAuth Client ID:
   - Application type: **Desktop app**
   - Name: "Job Seeker Agent"
   - Click "Create"
   - Download the JSON file

### 2. Place Credentials File

1. Rename the downloaded JSON file to `credentials.json`
2. Place it in the project root directory (`/Users/consultadd/Desktop/Popcon/`)
3. The file should look like:
   ```json
   {
     "installed": {
       "client_id": "...",
       "project_id": "...",
       "auth_uri": "...",
       "token_uri": "...",
       "client_secret": "...",
       "redirect_uris": ["http://localhost"]
     }
   }
   ```

### 3. Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

This will install:
- `google-auth`
- `google-auth-oauthlib`
- `google-auth-httplib2`
- `google-api-python-client`

### 4. Usage

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **In the web interface**:
   - Enter your email address in the "Your Email" field
   - Click "🔐 Authenticate Gmail" button
   - A browser window will open asking for Gmail access
   - Grant permission to send emails on your behalf
   - The token will be saved automatically

3. **Token Storage**:
   - Tokens are stored in `tokens/` directory
   - Each user's token is stored separately: `token_<email>.json`
   - Tokens are automatically refreshed when expired

## How It Works

1. **First Time**: User clicks "Authenticate Gmail" → Browser opens → User grants permission → Token saved
2. **Subsequent Uses**: Token is automatically loaded and refreshed if needed
3. **Email Sending**: Uses Gmail API instead of SMTP, more secure and reliable

## Security Notes

- ✅ Tokens are stored locally in `tokens/` directory
- ✅ Tokens are user-specific (one per email)
- ✅ Tokens automatically refresh when expired
- ✅ Only Gmail send permission is requested (not read/delete)
- ✅ `tokens/` and `credentials.json` are in `.gitignore`

## Troubleshooting

### "OAuth credentials file not found"
- Make sure `credentials.json` is in the project root
- Check the file name is exactly `credentials.json`

### "Access blocked: This app's request is invalid"
- Make sure you added your email as a test user in OAuth consent screen
- For production, you need to verify your app with Google

### "Token expired"
- Tokens automatically refresh, but if refresh fails:
  - Delete the token file: `tokens/token_<your_email>.json`
  - Re-authenticate by clicking "Authenticate Gmail" again

### Browser doesn't open
- Make sure the Flask app is running
- Check firewall settings
- Try running from terminal (not background)

## Environment Variables

You no longer need these SMTP variables:
- ❌ `SMTP_HOST`
- ❌ `SMTP_PORT`
- ❌ `SMTP_USERNAME`
- ❌ `SMTP_PASSWORD`

The following are still required:
- ✅ `TAVILY_API_KEY`
- ✅ `HUNTER_API_KEY`
- ✅ `OPENAI_API_KEY`

Optional:
- `GOOGLE_CREDENTIALS_FILE` - Path to credentials.json (default: `credentials.json`)
