# AI Job Seeker Agent

An intelligent Python-based agent that automates job discovery, prospect finding, and email outreach for job seekers, freelancers, and students.

## Features

- 🔍 **Automated Job Search**: Uses Tavily AI to find companies actively hiring
- 👥 **Prospect Discovery**: Identifies hiring managers and recruiters at target companies
- 📧 **Email Finding**: Uses Hunter.io to find corporate email addresses
- ✉️ **AI-Powered Outreach**: Generates personalized emails using OpenAI GPT
- 📊 **Results Export**: Export findings to JSON or CSV
- 🧪 **Dry-Run Mode**: Test the flow without sending emails
- 📝 **Comprehensive Logging**: Track progress and debug issues

## Project Structure

```
job-agent/
├── main.py                 # Entry point, orchestrates the flow
├── config.py              # Configuration and API keys
├── requirements.txt       # Dependencies
├── .env.example          # Example environment variables
├── agents/
│   ├── __init__.py
│   ├── tavily_agent.py   # Tavily search logic
│   ├── hunter_agent.py   # Hunter.io email finding
│   └── email_agent.py    # Email generation and sending
├── models/
│   ├── __init__.py
│   └── prospect.py       # Data models (Prospect, Company)
├── templates/
│   └── email_template.txt # Email template
└── utils/
    ├── __init__.py
    ├── logger.py         # Logging utilities
    └── validators.py     # Input validation
```

## Prerequisites

- Python 3.9 or higher
- API keys for:
  - [Tavily AI](https://tavily.com/) - For web search
  - [Hunter.io](https://hunter.io/) - For email finding
  - [OpenAI](https://openai.com/) - For email generation
- SMTP credentials for sending emails (Gmail, Outlook, etc.)

## Installation

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```env
   TAVILY_API_KEY=your_tavily_api_key_here
   HUNTER_API_KEY=your_hunter_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_app_password_here
   SMTP_FROM_EMAIL=your_email@gmail.com
   SMTP_FROM_NAME=Your Name
   ```

   **Note for Gmail users**: You'll need to generate an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password.

## Usage

### Basic Usage

**LinkedIn-Focused Approach (Recommended - Faster & More Direct):**
```bash
# Search LinkedIn profiles directly (dry-run mode - recommended for first run)
python main.py --goal "Software Engineer jobs" --linkedin --dry-run

# With custom result limit
python main.py --goal "React developer internships" --linkedin --max-linkedin-results 10 --dry-run

# Actually send emails (remove --dry-run)
python main.py --goal "Data Scientist positions" --linkedin
```

**Company-Based Approach (Traditional):**
```bash
# Search for job opportunities (dry-run mode - recommended for first run)
python main.py --goal "Software Engineer jobs" --dry-run

# Search with custom limits
python main.py --goal "Marketing internships" --max-companies 10 --max-prospects 3

# Actually send emails (remove --dry-run)
python main.py --goal "Data Scientist positions" --max-companies 5
```

### Command-Line Options

- `--goal` (required): Your job search goal (e.g., "Software Engineer jobs")
- `--linkedin`: Use LinkedIn-focused approach (searches LinkedIn profiles directly, faster)
- `--max-linkedin-results`: Maximum LinkedIn results to process (only with --linkedin, default: 5)
- `--max-companies`: Maximum number of companies to search (default: 50, company-based approach only)
- `--max-prospects`: Maximum prospects per company (default: 5, company-based approach only)
- `--dry-run`: Generate emails without sending (highly recommended for testing)
- `--template`: Path to email template file (default: templates/email_template.txt)
- `--export-format`: Export format - 'json' or 'csv' (default: json)

### Examples

```bash
# LinkedIn approach - test run (recommended)
python main.py --goal "Frontend Developer" --linkedin --dry-run

# LinkedIn approach - full run
python main.py --goal "React Developer internships" --linkedin --max-linkedin-results 10

# Company-based approach - test run
python main.py --goal "Product Manager" --max-companies 5 --dry-run

# Full run with custom template
python main.py --goal "UX Designer" --linkedin --template my_template.txt

# Export results as CSV
python main.py --goal "Data Scientist" --linkedin --export-format csv --dry-run
```

## How It Works

### LinkedIn-Focused Approach (--linkedin flag)

**Step 1: LinkedIn Profile Search**
- Uses Tavily AI to search specifically for LinkedIn profiles related to your goal
- Searches only within linkedin.com domain for more targeted results
- Extracts names, company domains, and LinkedIn URLs in one step using GPT

**Step 2: Email Discovery**
- For each prospect, uses Hunter.io to find corporate email addresses
- Uses the extracted domain and name information
- Validates email format and confidence scores

**Step 3: Email Generation & Sending**
- Generates personalized emails using OpenAI GPT
- Customizes content with prospect and company information
- Sends emails via SMTP (or logs in dry-run mode)

### Company-Based Approach (default)

**Step 1: Initial Job Search**
- Uses Tavily AI to search for companies hiring based on your goal
- Extracts company names using AI-powered extraction
- Stores unique companies in a set

**Step 2: Company-Specific Job Search**
- For each company, searches for hiring managers and recruiters
- Extracts names, LinkedIn profiles, and job titles
- Uses GPT to parse and structure the information

**Step 3: Email Discovery**
- For each prospect, uses Hunter.io to find corporate email addresses
- Validates email format and confidence scores
- Falls back to domain search if direct lookup fails

**Step 4: Email Generation & Sending**
- Generates personalized emails using OpenAI GPT
- Customizes content with prospect and company information
- Sends emails via SMTP (or logs in dry-run mode)

## Output

The agent generates:

1. **Console Logs**: Real-time progress and results
2. **Log File**: Detailed logs saved to `job_agent_YYYYMMDD.log`
3. **Results File**: Exported to `job_agent_results_TIMESTAMP.json` or `.csv`

### Results File Structure (JSON)

```json
{
  "summary": {
    "companies_found": 15,
    "prospects_found": 42,
    "emails_found": 28,
    "emails_sent": 25,
    "emails_failed": 3,
    "start_time": "2024-01-15T10:30:00",
    "end_time": "2024-01-15T10:45:00"
  },
  "companies": [...],
  "prospects": [...]
}
```

## Error Handling

The agent includes:
- Retry logic for API failures
- Rate limiting to respect API limits
- Graceful error handling at each step
- Comprehensive logging for debugging

## Rate Limiting

The agent automatically implements rate limiting:
- Tavily: 5 requests per second
- Hunter.io: 10 requests per second

Adjust these in `config.py` if needed.

## Customization

### Email Template

Edit `templates/email_template.txt` to customize the email style. The AI will use this as a guide when generating emails.

### Configuration

Modify `config.py` to adjust:
- Rate limits
- Retry settings
- Default SMTP settings

## Best Practices

1. **Always test with `--dry-run` first** to see what emails will be sent
2. **Start with small limits** (`--max-companies 5`) to test the flow
3. **Review generated emails** before sending in production
4. **Respect rate limits** - don't run multiple instances simultaneously
5. **Monitor your API usage** to avoid unexpected costs

## Troubleshooting

### "Missing required environment variables"
- Ensure your `.env` file exists and contains all required keys
- Check that variable names match exactly (case-sensitive)

### "SMTP authentication failed"
- For Gmail: Use an App Password, not your regular password
- Check that SMTP settings are correct for your email provider

### "No companies/prospects found"
- Try a more specific search goal
- Check your Tavily API key and quota
- Review logs for detailed error messages

### Rate limit errors
- The agent includes rate limiting, but if you see errors:
  - Reduce `--max-companies` or `--max-prospects`
  - Wait between runs
  - Check your API quotas

## License

This project is provided as-is for educational and personal use.

## Disclaimer

- Always comply with email marketing laws (CAN-SPAM, GDPR, etc.)
- Use responsibly and ethically
- Respect recipients' privacy and preferences
- This tool is for legitimate job seeking purposes only

## Support

For issues or questions:
1. Check the logs in `job_agent_YYYYMMDD.log`
2. Review error messages in the console
3. Verify all API keys are correct and have sufficient quota

---

**Happy job hunting! 🚀**
