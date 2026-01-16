# Web Application - AI Job Seeker Agent

A modern web interface for the AI Job Seeker Agent with real-time prospect discovery and email sending.

## Features

- 🎯 **User Input Form**: Enter your name, email, skills, and job search goal
- 🔍 **Prospect Discovery**: Search LinkedIn profiles and find hiring managers
- 📧 **Email Finding**: Automatically discover email addresses via Hunter.io
- 📋 **Prospect List**: View all found prospects in a clean, organized list
- 👁️ **Detail View**: Click any prospect to see full details (LinkedIn, email, company)
- ✉️ **Bulk Email Sending**: Send personalized emails to all prospects with one click
- 📊 **Real-time Status**: Track emails found and emails sent in real-time

## Installation

1. **Install dependencies** (if not already done):
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Ensure your `.env` file is configured** with all API keys:
   - `TAVILY_API_KEY`
   - `HUNTER_API_KEY`
   - `OPENAI_API_KEY`
   - SMTP settings for email sending

## Running the Web App

1. **Start the Flask server**:
   ```bash
   source venv/bin/activate
   python app.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

## Usage

### Step 1: Enter Your Information
- **Name**: Your full name (will be used in email signature)
- **Email**: Your email address
- **Skills**: Your skills (e.g., "React, JavaScript, Node.js")
- **Goal**: Your job search goal (e.g., "I am looking for React developer opportunities")

### Step 2: Search for Prospects
- Click "Search Prospects"
- The system will:
  - Search LinkedIn profiles related to your goal
  - Extract prospect names, companies, and LinkedIn URLs
  - Find email addresses via Hunter.io
  - Display results in a list

### Step 3: View Prospect Details
- Click on any prospect in the list
- A modal will show:
  - Full name
  - Company name
  - Company domain
  - Email address (if found)
  - LinkedIn profile link
  - Job title (if available)

### Step 4: Send Emails
- Click "Send Emails to All" button
- Confirm the action
- Emails will be sent in the background with:
  - Personalized content using your name and skills
  - 5-15 second delays between emails (anti-spam)
  - Real-time status updates

## API Endpoints

### POST `/api/search`
Search for prospects based on user input.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "skills": "React, JavaScript",
  "goal": "I am looking for React developer opportunities"
}
```

**Response:**
```json
{
  "success": true,
  "prospects": [...],
  "status": {
    "total_prospects": 5,
    "emails_found": 4,
    "emails_sent": 0,
    "is_processing": false
  }
}
```

### GET `/api/prospect/<id>`
Get detailed information about a specific prospect.

### POST `/api/send-emails`
Send emails to all prospects with valid email addresses.

**Request Body:**
```json
{
  "dry_run": false
}
```

### GET `/api/status`
Get current processing status.

## Status Display

The status card shows:
- **Total Prospects**: Number of prospects found
- **Emails Found**: Number of prospects with valid email addresses
- **Emails Sent**: Number of emails successfully sent

## Email Personalization

Emails are automatically personalized with:
- Your name (in signature)
- Your skills (mentioned in the email body)
- Your goal (referenced in the email)
- Prospect's name and company

## Technical Details

- **Backend**: Flask (Python)
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Real-time Updates**: Status polling (optional)
- **Email Sending**: Bulk sending with human-like delays
- **Error Handling**: Comprehensive error messages and logging

## Troubleshooting

### "Configuration error"
- Check your `.env` file has all required API keys
- Ensure API keys are valid and not placeholders

### "No prospects found"
- Try a more specific search goal
- Check your Tavily API key and quota

### "Failed to send emails"
- Verify SMTP settings in `.env`
- For Gmail, use an App Password (not regular password)
- Check SMTP port (465 for SSL)

### Port already in use
- Change the port in `app.py`: `app.run(port=5001)`
- Or kill the process using port 5000

## Development

To modify the frontend:
- HTML: `static/index.html`
- CSS: `static/style.css`
- JavaScript: `static/script.js`

To modify the backend:
- Flask app: `app.py`
- API endpoints: See routes in `app.py`

## Notes

- The web app uses session-based storage (in-memory)
- For production, consider using a database for session persistence
- Email sending happens synchronously (may take time for many prospects)
- Consider adding WebSocket support for real-time updates in production
