#!/usr/bin/env python3
"""
Flask Web Application for AI Job Seeker Agent
Provides REST API and serves the frontend
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os
from datetime import datetime
from typing import Dict, List

from config import Config
from models.prospect import Prospect
from agents.tavily_agent import TavilyAgent
from agents.hunter_agent import HunterAgent
from agents.email_agent import EmailAgent
from utils.logger import setup_logger

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)  # Enable CORS for frontend

logger = setup_logger("job_agent_web")

# Global state for current session
session_data: Dict = {
    'user_info': None,
    'prospects': [],
    'status': {
        'emails_found': 0,
        'emails_sent': 0,
        'total_prospects': 0,
        'is_processing': False,
        'current_step': None
    }
}

# Initialize agents
tavily_agent = None
hunter_agent = None
email_agent = None

def init_agents():
    """Initialize agents (lazy loading)"""
    global tavily_agent, hunter_agent, email_agent
    if tavily_agent is None:
        tavily_agent = TavilyAgent()
        hunter_agent = HunterAgent()
        email_agent = EmailAgent()
    return tavily_agent, hunter_agent, email_agent

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('static', 'index.html')

@app.route('/api/search', methods=['POST'])
def search_prospects():
    """Search for prospects based on user input"""
    try:
        data = request.json
        user_name = data.get('name', '').strip()
        user_email = data.get('email', '').strip()
        user_skills = data.get('skills', '').strip()
        goal = data.get('goal', '').strip()
        
        if not goal:
            return jsonify({'error': 'Goal is required'}), 400
        
        # Store user info
        session_data['user_info'] = {
            'name': user_name,
            'email': user_email,
            'skills': user_skills,
            'goal': goal
        }
        
        # Update status
        session_data['status']['is_processing'] = True
        session_data['status']['current_step'] = 'Searching LinkedIn profiles...'
        session_data['prospects'] = []
        session_data['status']['emails_found'] = 0
        session_data['status']['emails_sent'] = 0
        
        # Initialize agents
        tavily, hunter, email = init_agents()
        
        # Step 1: Search LinkedIn profiles
        logger.info(f"Starting search for: {goal}")
        prospects = tavily.search_linkedin_profiles(goal, max_results=10)
        
        if not prospects:
            session_data['status']['is_processing'] = False
            session_data['status']['current_step'] = 'No prospects found'
            return jsonify({
                'success': False,
                'message': 'No prospects found. Try a different search query.',
                'prospects': [],
                'status': session_data['status']
            })
        
        # Deduplicate
        unique_prospects = list({p: p for p in prospects}.values())
        session_data['prospects'] = unique_prospects
        session_data['status']['total_prospects'] = len(unique_prospects)
        session_data['status']['current_step'] = 'Finding email addresses...'
        
        # Step 2: Find emails
        prospects_with_emails = []
        for prospect in unique_prospects:
            try:
                email_addr = hunter.find_email(prospect)
                if email_addr:
                    prospect.email = email_addr
                    prospects_with_emails.append(prospect)
                    session_data['status']['emails_found'] += 1
            except Exception as e:
                logger.warning(f"Error finding email for {prospect.full_name()}: {str(e)}")
                continue
        
        # Update prospects list
        session_data['prospects'] = prospects_with_emails
        session_data['status']['is_processing'] = False
        session_data['status']['current_step'] = 'Ready to send emails'
        
        # Convert prospects to dict for JSON response
        prospects_data = [p.to_dict() for p in prospects_with_emails]
        
        return jsonify({
            'success': True,
            'prospects': prospects_data,
            'status': session_data['status']
        })
        
    except Exception as e:
        logger.error(f"Error in search_prospects: {str(e)}")
        session_data['status']['is_processing'] = False
        session_data['status']['current_step'] = f'Error: {str(e)}'
        return jsonify({
            'success': False,
            'error': str(e),
            'status': session_data['status']
        }), 500

@app.route('/api/prospect/<int:prospect_id>', methods=['GET'])
def get_prospect_details(prospect_id):
    """Get detailed information about a specific prospect"""
    try:
        if prospect_id < 0 or prospect_id >= len(session_data['prospects']):
            return jsonify({'error': 'Invalid prospect ID'}), 404
        
        prospect = session_data['prospects'][prospect_id]
        return jsonify({
            'success': True,
            'prospect': prospect.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting prospect details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-emails', methods=['POST'])
def send_emails():
    """Send emails to all prospects with valid email addresses"""
    try:
        data = request.json
        dry_run = data.get('dry_run', False)
        
        prospects_with_emails = [p for p in session_data['prospects'] if p.email]
        
        if not prospects_with_emails:
            return jsonify({
                'success': False,
                'message': 'No prospects with email addresses found',
                'status': session_data['status']
            })
        
        # Update status
        session_data['status']['is_processing'] = True
        session_data['status']['current_step'] = 'Sending emails...'
        session_data['status']['emails_sent'] = 0
        
        # Initialize email agent
        _, _, email = init_agents()
        
        # Get user info for email personalization
        user_info = session_data.get('user_info', {})
        
        # Send emails (email generation will use user info from session)
        if dry_run:
            results = email.send_bulk_emails(prospects_with_emails, dry_run=True, user_info=user_info)
        else:
            # For actual sending, we'll use the bulk method
            results = email.send_bulk_emails(prospects_with_emails, dry_run=False, user_info=user_info)
        
        session_data['status']['emails_sent'] = results['sent']
        session_data['status']['emails_failed'] = results.get('failed', 0)
        session_data['status']['is_processing'] = False
        session_data['status']['current_step'] = 'Emails sent successfully'
        
        return jsonify({
            'success': True,
            'message': f"Successfully sent {results['sent']} emails",
            'status': session_data['status'],
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error sending emails: {str(e)}")
        session_data['status']['is_processing'] = False
        session_data['status']['current_step'] = f'Error: {str(e)}'
        return jsonify({
            'success': False,
            'error': str(e),
            'status': session_data['status']
        }), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current processing status"""
    return jsonify({
        'success': True,
        'status': session_data['status']
    })

@app.route('/api/reset', methods=['POST'])
def reset_session():
    """Reset the session data"""
    global session_data
    session_data = {
        'user_info': None,
        'prospects': [],
        'status': {
            'emails_found': 0,
            'emails_sent': 0,
            'total_prospects': 0,
            'is_processing': False,
            'current_step': None
        }
    }
    return jsonify({'success': True, 'message': 'Session reset'})

if __name__ == '__main__':
    # Validate configuration
    try:
        Config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        logger.error("Please check your .env file and ensure all required API keys are set.")
    
    # Create static directory if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=8000)
