#!/usr/bin/env python3
"""
AI Job Seeker Agent - Main Entry Point
Orchestrates the complete flow: job search, prospect finding, email discovery, and outreach
"""

import argparse
import json
import csv
import sys
from typing import List, Set
from datetime import datetime

from config import Config
from models.prospect import Company, Prospect
from agents.tavily_agent import TavilyAgent
from agents.hunter_agent import HunterAgent
from agents.email_agent import EmailAgent
from utils.logger import setup_logger

logger = setup_logger("job_agent")

class JobSeekerAgent:
    """Main orchestrator for the job seeker agent"""
    
    def __init__(self, dry_run: bool = False, days_filter: int = 45):
        self.dry_run = dry_run
        self.days_filter = days_filter
        self.prospect_db = ProspectDatabase()  # Initialize database for caching
        self.tavily_agent = TavilyAgent(days_filter=days_filter)  # Pass days filter
        self.hunter_agent = HunterAgent(prospect_db=self.prospect_db)  # Pass database to hunter
        self.email_agent = EmailAgent()
        self.companies: Set[Company] = set()
        self.prospects: List[Prospect] = []
        self.results = {
            'companies_found': 0,
            'prospects_found': 0,
            'emails_found': 0,
            'emails_sent': 0,
            'emails_failed': 0,
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }
    
    def step1_search_companies(self, goal: str, max_companies: int = None) -> Set[Company]:
        """Step 1: Search for companies hiring"""
        logger.info("=" * 60)
        logger.info("STEP 1: Initial Job Search")
        logger.info("=" * 60)
        
        try:
            companies = self.tavily_agent.search_companies(goal, max_results=max_companies or 50)
            self.companies = companies
            self.results['companies_found'] = len(companies)
            logger.info(f"✓ Found {len(companies)} companies")
            return companies
        except Exception as e:
            logger.error(f"✗ Step 1 failed: {str(e)}")
            raise
    
    def step2_search_prospects(self, max_prospects_per_company: int = 5) -> List[Prospect]:
        """Step 2: Search for prospects at each company"""
        logger.info("=" * 60)
        logger.info("STEP 2: Company-Specific Job Search")
        logger.info("=" * 60)
        
        all_prospects = []
        total_companies = len(self.companies)
        
        for idx, company in enumerate(self.companies, 1):
            logger.info(f"Processing company {idx}/{total_companies}: {company.name}")
            try:
                prospects = self.tavily_agent.search_prospects(company, max_results=max_prospects_per_company)
                all_prospects.extend(prospects)
                logger.info(f"✓ Found {len(prospects)} prospects at {company.name}")
            except Exception as e:
                logger.warning(f"✗ Failed to find prospects at {company.name}: {str(e)}")
                continue
        
        # Deduplicate prospects
        unique_prospects = list({p: p for p in all_prospects}.values())
        self.prospects = unique_prospects
        self.results['prospects_found'] = len(unique_prospects)
        logger.info(f"✓ Total unique prospects found: {len(unique_prospects)}")
        return unique_prospects
    
    def step3_find_emails(self) -> List[Prospect]:
        """Step 3: Find email addresses for prospects"""
        logger.info("=" * 60)
        logger.info("STEP 3: Email Discovery")
        logger.info("=" * 60)
        
        prospects_with_emails = []
        total_prospects = len(self.prospects)
        
        for idx, prospect in enumerate(self.prospects, 1):
            logger.info(f"Finding email {idx}/{total_prospects}: {prospect.full_name()}")
            try:
                email = self.hunter_agent.find_email(prospect)
                if email:
                    prospect.email = email
                    prospects_with_emails.append(prospect)
                    self.results['emails_found'] += 1
                    logger.info(f"✓ Found email for {prospect.full_name()}")
                else:
                    logger.warning(f"✗ No email found for {prospect.full_name()}")
            except Exception as e:
                logger.warning(f"✗ Error finding email for {prospect.full_name()}: {str(e)}")
                continue
        
        logger.info(f"✓ Found emails for {len(prospects_with_emails)} prospects")
        return prospects_with_emails
    
    def step4_send_emails(self, template_path: str = None) -> None:
        """Step 4: Generate and send emails using bulk sending with delays"""
        logger.info("=" * 60)
        logger.info("STEP 4: Email Generation & Sending")
        logger.info("=" * 60)
        
        prospects_with_emails = [p for p in self.prospects if p.email]
        total = len(prospects_with_emails)
        
        if not prospects_with_emails:
            logger.warning("No prospects with emails to send to")
            return
        
        if self.dry_run:
            logger.info(f"[DRY RUN MODE] Would send {total} emails")
            # In dry-run, send individually to show what would be sent
            for prospect in prospects_with_emails:
                self.email_agent.generate_and_send(
                    prospect,
                    template_path=template_path,
                    dry_run=True
                )
            self.results['emails_sent'] = total
            return
        
        # Use bulk sending with human-like delays
        logger.info(f"Sending {total} emails with human-like delays (5-15s between each)...")
        bulk_results = self.email_agent.send_bulk_emails(
            prospects_with_emails,
            template_path=template_path,
            dry_run=False
        )
        
        self.results['emails_sent'] = bulk_results['sent']
        self.results['emails_failed'] = bulk_results['failed']
        
        logger.info(f"✓ Sent {self.results['emails_sent']} emails")
        if self.results['emails_failed'] > 0:
            logger.warning(f"✗ Failed to send {self.results['emails_failed']} emails")
    
    def export_results(self, format: str = 'json', filename: str = None) -> str:
        """Export results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"job_agent_results_{timestamp}.{format}"
        
        if format == 'json':
            data = {
                'summary': self.results,
                'companies': [{'name': c.name, 'domain': c.domain} for c in self.companies],
                'prospects': [p.to_dict() for p in self.prospects]
            }
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
        
        elif format == 'csv':
            with open(filename, 'w', newline='') as f:
                if self.prospects:
                    writer = csv.DictWriter(f, fieldnames=self.prospects[0].to_dict().keys())
                    writer.writeheader()
                    writer.writerows([p.to_dict() for p in self.prospects])
        
        logger.info(f"Results exported to {filename}")
        return filename
    
    def run_linkedin_approach(self, goal: str, max_results: int = 5,
                              template_path: str = None, export_format: str = 'json') -> None:
        """
        Run the LinkedIn-focused approach (direct LinkedIn profile search)
        This is the more direct method that searches LinkedIn profiles directly
        """
        try:
            logger.info("Starting AI Job Seeker Agent (LinkedIn Approach)")
            logger.info(f"Goal: {goal}")
            logger.info(f"Dry Run: {self.dry_run}")
            
            # Step 1: Search LinkedIn profiles directly
            logger.info("=" * 60)
            logger.info("STEP 1: LinkedIn Profile Search")
            logger.info("=" * 60)
            
            prospects = self.tavily_agent.search_linkedin_profiles(goal, max_results=max_results)
            
            if not prospects:
                logger.warning("No prospects found. Exiting.")
                return
            
            # Deduplicate prospects
            unique_prospects = list({p: p for p in prospects}.values())
            self.prospects = unique_prospects
            self.results['prospects_found'] = len(unique_prospects)
            logger.info(f"✓ Found {len(unique_prospects)} unique prospects")
            
            # Step 2: Find emails via Hunter.io
            self.step3_find_emails()
            
            prospects_with_emails = [p for p in self.prospects if p.email]
            if not prospects_with_emails:
                logger.warning("No emails found. Exiting.")
                return
            
            # Step 3: Send emails
            self.step4_send_emails(template_path)
            
            # Export results
            self.results['end_time'] = datetime.now().isoformat()
            self.export_results(export_format)
            
            # Print summary
            logger.info("=" * 60)
            logger.info("SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Prospects found: {self.results['prospects_found']}")
            logger.info(f"Emails found: {self.results['emails_found']}")
            logger.info(f"Emails sent: {self.results['emails_sent']}")
            logger.info(f"Emails failed: {self.results['emails_failed']}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Fatal error: {str(e)}")
            raise
    
    def run(self, goal: str, max_companies: int = None, max_prospects_per_company: int = 5,
            template_path: str = None, export_format: str = 'json') -> None:
        """Run the complete flow (company-based approach)"""
        try:
            logger.info("Starting AI Job Seeker Agent")
            logger.info(f"Goal: {goal}")
            logger.info(f"Dry Run: {self.dry_run}")
            
            # Step 1: Search for companies
            self.step1_search_companies(goal, max_companies)
            
            if not self.companies:
                logger.warning("No companies found. Exiting.")
                return
            
            # Step 2: Search for prospects
            self.step2_search_prospects(max_prospects_per_company)
            
            if not self.prospects:
                logger.warning("No prospects found. Exiting.")
                return
            
            # Step 3: Find emails
            self.step3_find_emails()
            
            prospects_with_emails = [p for p in self.prospects if p.email]
            if not prospects_with_emails:
                logger.warning("No emails found. Exiting.")
                return
            
            # Step 4: Send emails
            self.step4_send_emails(template_path)
            
            # Export results
            self.results['end_time'] = datetime.now().isoformat()
            self.export_results(export_format)
            
            # Print summary
            logger.info("=" * 60)
            logger.info("SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Companies found: {self.results['companies_found']}")
            logger.info(f"Prospects found: {self.results['prospects_found']}")
            logger.info(f"Emails found: {self.results['emails_found']}")
            logger.info(f"Emails sent: {self.results['emails_sent']}")
            logger.info(f"Emails failed: {self.results['emails_failed']}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"Fatal error: {str(e)}")
            raise


def main():
    """Main entry point with CLI"""
    parser = argparse.ArgumentParser(
        description="AI Job Seeker Agent - Automate job discovery and outreach",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--goal',
        type=str,
        required=True,
        help='Job search goal (e.g., "Software Engineer jobs")'
    )
    
    parser.add_argument(
        '--max-companies',
        type=int,
        default=None,
        help='Maximum number of companies to search (default: 50)'
    )
    
    parser.add_argument(
        '--max-prospects',
        type=int,
        default=5,
        help='Maximum prospects per company (default: 5)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Generate emails without sending (recommended for testing)'
    )
    
    parser.add_argument(
        '--template',
        type=str,
        default='templates/email_template.txt',
        help='Path to email template file (default: templates/email_template.txt)'
    )
    
    parser.add_argument(
        '--export-format',
        type=str,
        choices=['json', 'csv'],
        default='json',
        help='Export format for results (default: json)'
    )
    
    parser.add_argument(
        '--linkedin',
        action='store_true',
        help='Use LinkedIn-focused approach (searches LinkedIn profiles directly, faster and more direct)'
    )
    
    parser.add_argument(
        '--max-linkedin-results',
        type=int,
        default=5,
        help='Maximum LinkedIn results to process (only used with --linkedin, default: 5)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=45,
        help='Filter results to last N days (default: 45 days)'
    )
    
    args = parser.parse_args()
    
    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        logger.error("Please check your .env file and ensure all required API keys are set.")
        sys.exit(1)
    
    # Run the agent with days filter
    agent = JobSeekerAgent(dry_run=args.dry_run, days_filter=args.days)
    logger.info(f"Filtering results to last {args.days} days")
    
    try:
        if args.linkedin:
            # Use LinkedIn-focused approach
            agent.run_linkedin_approach(
                goal=args.goal,
                max_results=args.max_linkedin_results,
                template_path=args.template,
                export_format=args.export_format
            )
        else:
            # Use company-based approach
            agent.run(
                goal=args.goal,
                max_companies=args.max_companies,
                max_prospects_per_company=args.max_prospects,
                template_path=args.template,
                export_format=args.export_format
            )
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
