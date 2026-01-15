import time
import re
import json
from typing import List, Set
from tavily import TavilyClient
from openai import OpenAI
from config import Config
from models.prospect import Company, Prospect
from utils.logger import setup_logger
from utils.validators import extract_domain, parse_name

logger = setup_logger(__name__)

class TavilyAgent:
    """Agent for performing web searches using Tavily AI"""
    
    def __init__(self):
        # Validate API keys before initializing clients
        if not Config.TAVILY_API_KEY or Config.TAVILY_API_KEY == "your_tavily_api_key_here":
            raise ValueError("TAVILY_API_KEY is not set or is still a placeholder. Please set it in your .env file.")
        if not Config.OPENAI_API_KEY or Config.OPENAI_API_KEY == "your_openai_api_key_here":
            raise ValueError("OPENAI_API_KEY is not set or is still a placeholder. Please set it in your .env file.")
        
        self.client = TavilyClient(api_key=Config.TAVILY_API_KEY)
        self.openai_client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.last_request_time = 0
        self.min_request_interval = 1.0 / Config.TAVILY_RATE_LIMIT
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def search_companies(self, goal: str, max_results: int = 50) -> Set[Company]:
        """
        Search for companies hiring based on goal
        Returns a set of unique companies
        """
        logger.info(f"Searching for companies: {goal}")
        companies = set()
        
        try:
            self._rate_limit()
            query = f"{goal} companies hiring job openings"
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"
            )
            
            # Extract company names from results using GPT
            results_text = "\n".join([
                f"Title: {r.get('title', '')}\nContent: {r.get('content', '')[:500]}\nURL: {r.get('url', '')}\n"
                for r in response.get('results', [])
            ])
            
            if results_text:
                company_names = self._extract_companies_with_gpt(goal, results_text)
                for name in company_names:
                    if name and len(name.strip()) > 2:
                        company = Company(name=name.strip())
                        companies.add(company)
                        logger.info(f"Found company: {name.strip()}")
            
            logger.info(f"Found {len(companies)} unique companies")
            return companies
            
        except Exception as e:
            logger.error(f"Error searching companies: {str(e)}")
            raise
    
    def _extract_companies_with_gpt(self, goal: str, results_text: str) -> List[str]:
        """Use GPT to extract company names from search results"""
        try:
            prompt = f"""Extract company names from the following job search results related to "{goal}".
Return only the company names, one per line. Do not include explanations or other text.
Focus on companies that are actively hiring or have job openings.

Search Results:
{results_text[:3000]}

Company names:"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts company names from job search results. Return only company names, one per line."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            companies_text = response.choices[0].message.content.strip()
            companies = [c.strip() for c in companies_text.split("\n") if c.strip()]
            return companies[:20]  # Limit to top 20
            
        except Exception as e:
            logger.warning(f"GPT extraction failed, using fallback: {str(e)}")
            return []
    
    def search_prospects(self, company: Company, max_results: int = 10) -> List[Prospect]:
        """
        Search for hiring managers and prospects at a specific company
        Returns a list of prospects
        """
        logger.info(f"Searching for prospects at {company.name}")
        prospects = []
        
        try:
            self._rate_limit()
            query = f"hiring manager recruiter jobs at {company.name} LinkedIn"
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced"
            )
            
            # Extract prospect information using GPT
            results_text = "\n".join([
                f"Title: {r.get('title', '')}\nContent: {r.get('content', '')[:500]}\nURL: {r.get('url', '')}\n"
                for r in response.get('results', [])
            ])
            
            if results_text:
                prospect_data = self._extract_prospects_with_gpt(company.name, results_text)
                
                for data in prospect_data:
                    first_name, last_name = parse_name(data.get('name', ''))
                    if first_name:
                        prospect = Prospect(
                            first_name=first_name,
                            last_name=last_name,
                            company_name=company.name,
                            company_domain=company.domain,
                            linkedin_profile=data.get('linkedin', ''),
                            job_title=data.get('title', '')
                        )
                        prospects.append(prospect)
                        logger.info(f"Found prospect: {prospect.full_name()} at {company.name}")
            
            logger.info(f"Found {len(prospects)} prospects at {company.name}")
            return prospects
            
        except Exception as e:
            logger.error(f"Error searching prospects at {company.name}: {str(e)}")
            return []
    
    def _extract_prospects_with_gpt(self, company_name: str, results_text: str) -> List[dict]:
        """Use GPT to extract prospect information from search results"""
        try:
            prompt = f"""Extract hiring manager and recruiter information from the following search results for {company_name}.
For each person found, extract:
- Full name
- Job title (if mentioned)
- LinkedIn profile URL (if mentioned)

Return the results as a JSON array with keys: name, title, linkedin.
Example format:
[
  {{"name": "John Doe", "title": "Hiring Manager", "linkedin": "https://linkedin.com/in/johndoe"}},
  {{"name": "Jane Smith", "title": "Recruiter", "linkedin": ""}}
]

Search Results:
{results_text[:3000]}

JSON array:"""
            
            import json
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts hiring manager and recruiter information. Return a JSON object with a 'prospects' key containing an array of prospect objects."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content.strip()
            # Try to parse as JSON object or array
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'prospects' in data:
                    return data['prospects']
                elif isinstance(data, dict):
                    # If it's a single object, wrap it in a list
                    return [data]
            except json.JSONDecodeError:
                # Fallback: try to extract from text
                logger.warning("Failed to parse GPT response as JSON, using fallback")
                return []
            
            return []
            
        except Exception as e:
            logger.warning(f"GPT extraction failed: {str(e)}")
            return []
    
    def search_linkedin_profiles(self, goal_query: str, max_results: int = 5) -> List[Prospect]:
        """
        Search specifically for LinkedIn profiles related to the goal
        This is a more direct approach that searches LinkedIn directly
        Returns a list of prospects with LinkedIn URLs and company domains
        """
        logger.info(f"Searching LinkedIn profiles for: {goal_query}")
        prospects = []
        
        try:
            # Check if API key is valid before making request
            if not Config.TAVILY_API_KEY:
                raise ValueError("TAVILY_API_KEY is missing from configuration")
            
            self._rate_limit()
            # Search specifically for LinkedIn profiles
            search_query = f"{goal_query} linkedin profiles"
            logger.debug(f"Making Tavily API request with query: {search_query}")
            response = self.client.search(
                query=search_query,
                search_depth="advanced",
                max_results=max_results,
                include_domains=["linkedin.com"]
            )
            
            # Build raw context from search results
            raw_context = ""
            for r in response.get('results', []):
                raw_context += f"URL: {r.get('url', '')}\nContent: {r.get('content', '')}\n---\n"
            
            if not raw_context:
                logger.warning("No LinkedIn results found")
                return prospects
            
            # Extract leads using GPT with the user's format
            logger.info("Extracting names, domains, and LinkedIn URLs...")
            leads = self._extract_leads_from_linkedin_search(goal_query, raw_context)
            
            # Convert leads to Prospect objects
            for lead in leads:
                first_name = lead.get('first_name', '').strip()
                last_name = lead.get('last_name', '').strip()
                domain = lead.get('domain', '').strip()
                linkedin_url = lead.get('linkedin_url', '').strip()
                
                if first_name:  # At least first name is required
                    # Extract company name from domain if possible
                    company_name = domain.replace('.com', '').replace('.io', '').replace('.co', '').title()
                    if not company_name:
                        company_name = "Unknown Company"
                    
                    prospect = Prospect(
                        first_name=first_name,
                        last_name=last_name,
                        company_name=company_name,
                        company_domain=domain if domain else None,
                        linkedin_profile=linkedin_url if linkedin_url else None
                    )
                    prospects.append(prospect)
                    logger.info(f"Found lead: {prospect.full_name()} at {domain}")
            
            logger.info(f"Found {len(prospects)} prospects from LinkedIn search")
            return prospects
            
        except ValueError as e:
            logger.error(f"Configuration error: {str(e)}")
            logger.error("Please check your .env file and ensure TAVILY_API_KEY is set correctly.")
            raise
        except Exception as e:
            error_msg = str(e)
            if "Unauthorized" in error_msg or "invalid API key" in error_msg or "missing" in error_msg.lower():
                logger.error(f"Tavily API authentication failed: {error_msg}")
                logger.error("Please check your TAVILY_API_KEY in the .env file.")
                logger.error(f"Current API key status: {'Set' if Config.TAVILY_API_KEY else 'NOT SET'} (length: {len(Config.TAVILY_API_KEY) if Config.TAVILY_API_KEY else 0})")
            else:
                logger.error(f"Error searching LinkedIn profiles: {error_msg}")
            return []
    
    def _extract_leads_from_linkedin_search(self, goal_query: str, raw_context: str) -> List[dict]:
        """Extract leads from LinkedIn search results using GPT"""
        try:
            extract_prompt = f"""
You are a lead generation expert. Extract a list of people and their LinkedIn URLs from the text below.
Format as a JSON object with a key 'leads'.
Guess the company domain (e.g., 'consultadd.com') if not explicitly mentioned.

TEXT:
{raw_context[:5000]}

OUTPUT FORMAT:
{{
  "leads": [
    {{
      "first_name": "...", 
      "last_name": "...", 
      "domain": "...", 
      "linkedin_url": "..."
    }}
  ]
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a lead generation expert. Extract people's information from LinkedIn search results. Return only valid JSON."},
                    {"role": "user", "content": extract_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            data = json.loads(content)
            leads = data.get("leads", [])
            
            return leads
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse GPT response as JSON: {str(e)}")
            return []
        except Exception as e:
            logger.warning(f"GPT extraction failed: {str(e)}")
            return []