# Quick Start Guide

Get up and running with the AI Job Seeker Agent in 5 minutes!

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

Or use a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Get API Keys

You'll need API keys from:

1. **Tavily AI**: Sign up at https://tavily.com/
2. **Hunter.io**: Sign up at https://hunter.io/
3. **OpenAI**: Get your API key from https://platform.openai.com/

## Step 3: Configure Environment

Create a `.env` file in the project root:

```bash
# Option 1: Use the setup script
./setup_env.sh

# Option 2: Create manually
cp .env.example .env  # If .env.example exists
# Or create .env and add:
```

Add your API keys to `.env`:

```env
TAVILY_API_KEY=your_key_here
HUNTER_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_FROM_NAME=Your Name
```

**For Gmail users**: You need an [App Password](https://support.google.com/accounts/answer/185833), not your regular password.

## Step 4: Test Run (Dry Run)

Always test first with `--dry-run`:

**LinkedIn Approach (Recommended - Faster):**
```bash
python main.py --goal "Software Engineer jobs" --linkedin --dry-run
```

**Company-Based Approach:**
```bash
python main.py --goal "Software Engineer jobs" --dry-run --max-companies 3
```

This will:
- Search for companies
- Find prospects
- Find emails
- Generate emails (but NOT send them)

## Step 5: Review Results

Check the generated results file:
- `job_agent_results_TIMESTAMP.json` - Contains all findings
- `job_agent_TIMESTAMP.log` - Detailed logs

## Step 6: Send Emails (When Ready)

Once you're satisfied with the results:

**LinkedIn Approach:**
```bash
python main.py --goal "Software Engineer jobs" --linkedin
```

**Company-Based Approach:**
```bash
python main.py --goal "Software Engineer jobs" --max-companies 10
```

(Remove `--dry-run` to actually send emails)

## Common Commands

```bash
# LinkedIn approach - small test run (recommended)
python main.py --goal "Data Scientist" --linkedin --max-linkedin-results 5 --dry-run

# LinkedIn approach - full run
python main.py --goal "React Developer internships" --linkedin

# Company-based approach - small test run
python main.py --goal "Product Manager" --max-companies 5 --max-prospects 3 --dry-run

# Full run with custom template
python main.py --goal "UX Designer" --linkedin --template templates/email_template.txt

# Export as CSV
python main.py --goal "Frontend Developer" --linkedin --export-format csv --dry-run
```

## Troubleshooting

**"ModuleNotFoundError"**: Install dependencies with `pip install -r requirements.txt`

**"Missing required environment variables"**: Check your `.env` file exists and has all keys

**"SMTP authentication failed"**: For Gmail, use an App Password, not your regular password

**"No companies found"**: Try a more specific search goal or check your Tavily API key

## Next Steps

- Customize the email template in `templates/email_template.txt`
- Adjust rate limits in `config.py` if needed
- Review the full README.md for advanced usage

Happy job hunting! 🚀
