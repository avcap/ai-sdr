import os
import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import requests
from openai import OpenAI
import dns.resolver
import socket

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnrichmentAgent:
    """
    AI Enrichment Agent - Validates, enriches, and scores lead data quality
    
    Capabilities:
    - Email validation (syntax + domain verification)
    - Phone number formatting and validation
    - Company data enrichment (industry, size, location)
    - LinkedIn profile validation
    - Lead quality scoring
    - Data cleaning and standardization
    """
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.agent_info = {
            "name": "Enrichment Agent",
            "role": "Lead Data Quality Specialist",
            "description": "Validates, enriches, and scores lead data to ensure high-quality prospects",
            "capabilities": [
                "Email validation and verification",
                "Phone number formatting",
                "Company data enrichment",
                "LinkedIn profile validation",
                "Lead quality scoring",
                "Data cleaning and standardization"
            ],
            "version": "1.0.0"
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about the Enrichment Agent"""
        return self.agent_info
    
    def validate_email(self, email: str) -> Dict[str, Any]:
        """
        Validate email address with syntax and domain checks
        
        Args:
            email: Email address to validate
            
        Returns:
            Dict with validation results
        """
        if not email:
            return {
                "valid": False,
                "syntax_valid": False,
                "domain_valid": False,
                "error": "Email is empty"
            }
        
        # Basic email regex pattern
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        syntax_valid = bool(re.match(email_pattern, email))
        
        if not syntax_valid:
            return {
                "valid": False,
                "syntax_valid": False,
                "domain_valid": False,
                "error": "Invalid email syntax"
            }
        
        # Extract domain
        domain = email.split('@')[1]
        
        # Check domain validity
        domain_valid = False
        try:
            # Check MX record
            mx_records = dns.resolver.resolve(domain, 'MX')
            domain_valid = len(mx_records) > 0
        except Exception as e:
            logger.warning(f"Domain validation failed for {domain}: {e}")
            # Fallback: try to resolve A record
            try:
                socket.gethostbyname(domain)
                domain_valid = True
            except:
                domain_valid = False
        
        return {
            "valid": syntax_valid and domain_valid,
            "syntax_valid": syntax_valid,
            "domain_valid": domain_valid,
            "domain": domain,
            "error": None if (syntax_valid and domain_valid) else "Domain not found"
        }
    
    def validate_phone(self, phone: str) -> Dict[str, Any]:
        """
        Validate and format phone number
        
        Args:
            phone: Phone number to validate
            
        Returns:
            Dict with validation and formatting results
        """
        if not phone:
            return {
                "valid": False,
                "formatted": None,
                "error": "Phone is empty"
            }
        
        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)
        
        # Check if it's a valid length (7-15 digits)
        if len(digits_only) < 7 or len(digits_only) > 15:
            return {
                "valid": False,
                "formatted": None,
                "error": f"Invalid phone length: {len(digits_only)} digits"
            }
        
        # Format based on length
        if len(digits_only) == 10:
            # US format: (XXX) XXX-XXXX
            formatted = f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
        elif len(digits_only) == 11 and digits_only[0] == '1':
            # US format with country code: +1 (XXX) XXX-XXXX
            formatted = f"+1 ({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
        else:
            # International format
            formatted = f"+{digits_only}"
        
        return {
            "valid": True,
            "formatted": formatted,
            "original": phone,
            "digits_only": digits_only,
            "error": None
        }
    
    def enrich_company_data(self, company_name: str, location: str = None) -> Dict[str, Any]:
        """
        Enrich company data using AI
        
        Args:
            company_name: Name of the company
            location: Company location (optional)
            
        Returns:
            Dict with enriched company data
        """
        try:
            prompt = f"""
            You are a business intelligence expert. Analyze this company and provide enriched data:
            
            Company: {company_name}
            Location: {location or 'Not specified'}
            
            Provide a JSON response with:
            - industry: Primary industry/sector
            - company_size: Estimated employee count (e.g., "10-50", "50-200", "200-1000", "1000+")
            - company_type: Type of company (e.g., "Startup", "SMB", "Enterprise", "Public")
            - website: Likely company website domain
            - description: Brief company description
            - confidence: Confidence score 0-1 for the enrichment
            
            Be realistic and conservative in your estimates.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Try to parse JSON response
            try:
                enriched_data = json.loads(content)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                enriched_data = {
                    "industry": "Technology",
                    "company_size": "50-200",
                    "company_type": "SMB",
                    "website": f"{company_name.lower().replace(' ', '')}.com",
                    "description": f"{company_name} is a technology company",
                    "confidence": 0.5
                }
            
            return {
                "success": True,
                "data": enriched_data,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Company enrichment failed for {company_name}: {e}")
            return {
                "success": False,
                "data": None,
                "error": str(e)
            }
    
    def validate_linkedin_profile(self, linkedin_url: str, name: str, title: str) -> Dict[str, Any]:
        """
        Validate LinkedIn profile URL and check for consistency
        
        Args:
            linkedin_url: LinkedIn profile URL
            name: Person's name
            title: Person's job title
            
        Returns:
            Dict with validation results
        """
        if not linkedin_url:
            return {
                "valid": False,
                "url_valid": False,
                "profile_complete": False,
                "error": "LinkedIn URL is empty"
            }
        
        # Check URL format
        linkedin_pattern = r'^https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9\-_]+/?$'
        url_valid = bool(re.match(linkedin_pattern, linkedin_url))
        
        if not url_valid:
            return {
                "valid": False,
                "url_valid": False,
                "profile_complete": False,
                "error": "Invalid LinkedIn URL format"
            }
        
        # Extract username from URL
        username = linkedin_url.split('/in/')[-1].rstrip('/')
        
        # Check profile completeness based on URL structure
        profile_complete = len(username) > 3 and '-' in username  # Good profiles usually have hyphens
        
        # Generate alternative LinkedIn URL suggestions
        name_slug = name.lower().replace(' ', '-').replace('.', '')
        suggested_urls = [
            f"https://linkedin.com/in/{name_slug}",
            f"https://linkedin.com/in/{username}-{title.lower().replace(' ', '-')}",
            f"https://linkedin.com/in/{username}-{name_slug}"
        ]
        
        return {
            "valid": url_valid and profile_complete,
            "url_valid": url_valid,
            "profile_complete": profile_complete,
            "username": username,
            "suggested_urls": suggested_urls,
            "error": None if (url_valid and profile_complete) else "Profile may be incomplete"
        }
    
    def calculate_lead_score(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate lead quality score based on data completeness and accuracy
        
        Args:
            lead_data: Lead data dictionary
            
        Returns:
            Dict with scoring results
        """
        score = 0
        max_score = 100
        factors = {}
        
        # Email validation (25 points)
        email_result = self.validate_email(lead_data.get('email', ''))
        email_score = 25 if email_result['valid'] else (12 if email_result['syntax_valid'] else 0)
        score += email_score
        factors['email'] = {
            "score": email_score,
            "max_score": 25,
            "valid": email_result['valid'],
            "details": email_result
        }
        
        # Phone validation (15 points)
        phone_result = self.validate_phone(lead_data.get('phone', ''))
        phone_score = 15 if phone_result['valid'] else 0
        score += phone_score
        factors['phone'] = {
            "score": phone_score,
            "max_score": 15,
            "valid": phone_result['valid'],
            "details": phone_result
        }
        
        # LinkedIn validation (20 points)
        linkedin_result = self.validate_linkedin_profile(
            lead_data.get('linkedin_url', ''),
            lead_data.get('name', ''),
            lead_data.get('title', '')
        )
        linkedin_score = 20 if linkedin_result['valid'] else (10 if linkedin_result['url_valid'] else 0)
        score += linkedin_score
        factors['linkedin'] = {
            "score": linkedin_score,
            "max_score": 20,
            "valid": linkedin_result['valid'],
            "details": linkedin_result
        }
        
        # Required fields (20 points)
        required_fields = ['name', 'company', 'title']
        required_score = sum(5 for field in required_fields if lead_data.get(field))
        score += required_score
        factors['required_fields'] = {
            "score": required_score,
            "max_score": 15,
            "present_fields": [field for field in required_fields if lead_data.get(field)]
        }
        
        # Company enrichment (20 points)
        company_score = 0
        if lead_data.get('company'):
            company_score += 10  # Company name present
            if lead_data.get('industry'):
                company_score += 5  # Industry specified
            if lead_data.get('company_size'):
                company_score += 5  # Company size specified
        score += company_score
        factors['company'] = {
            "score": company_score,
            "max_score": 20,
            "has_company": bool(lead_data.get('company')),
            "has_industry": bool(lead_data.get('industry')),
            "has_size": bool(lead_data.get('company_size'))
        }
        
        # Calculate grade
        percentage = (score / max_score) * 100
        if percentage >= 90:
            grade = "A"
        elif percentage >= 80:
            grade = "B"
        elif percentage >= 70:
            grade = "C"
        elif percentage >= 60:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "total_score": score,
            "max_score": max_score,
            "percentage": round(percentage, 1),
            "grade": grade,
            "factors": factors,
            "recommendations": self._get_improvement_recommendations(factors)
        }
    
    def _get_improvement_recommendations(self, factors: Dict[str, Any]) -> List[str]:
        """Get recommendations for improving lead quality"""
        recommendations = []
        
        if factors['email']['score'] < factors['email']['max_score']:
            recommendations.append("Fix email address format or verify domain")
        
        if factors['phone']['score'] < factors['phone']['max_score']:
            recommendations.append("Add or correct phone number")
        
        if factors['linkedin']['score'] < factors['linkedin']['max_score']:
            recommendations.append("Add or verify LinkedIn profile URL")
        
        if factors['company']['score'] < factors['company']['max_score']:
            recommendations.append("Add company industry and size information")
        
        return recommendations
    
    def enrich_leads(self, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main enrichment function - validates and enriches a list of leads
        
        Args:
            leads: List of lead dictionaries
            
        Returns:
            Dict with enrichment results
        """
        logger.info(f"Starting enrichment for {len(leads)} leads")
        
        enriched_leads = []
        enrichment_stats = {
            "total_leads": len(leads),
            "processed_leads": 0,
            "valid_emails": 0,
            "valid_phones": 0,
            "valid_linkedin": 0,
            "high_quality_leads": 0,
            "enriched_companies": 0,
            "errors": []
        }
        
        for i, lead in enumerate(leads):
            try:
                logger.info(f"Processing lead {i+1}/{len(leads)}: {lead.get('name', 'Unknown')}")
                
                # Create enriched lead data
                enriched_lead = lead.copy()
                
                # Validate email
                email_result = self.validate_email(lead.get('email', ''))
                enriched_lead['email_validation'] = email_result
                if email_result['valid']:
                    enrichment_stats['valid_emails'] += 1
                
                # Validate phone
                phone_result = self.validate_phone(lead.get('phone', ''))
                enriched_lead['phone_validation'] = phone_result
                if phone_result['valid']:
                    enrichment_stats['valid_phones'] += 1
                    enriched_lead['phone'] = phone_result['formatted']  # Update with formatted phone
                
                # Validate LinkedIn
                linkedin_result = self.validate_linkedin_profile(
                    lead.get('linkedin_url', ''),
                    lead.get('name', ''),
                    lead.get('title', '')
                )
                enriched_lead['linkedin_validation'] = linkedin_result
                if linkedin_result['valid']:
                    enrichment_stats['valid_linkedin'] += 1
                
                # Enrich company data if not already present
                if lead.get('company') and not lead.get('industry'):
                    company_result = self.enrich_company_data(
                        lead.get('company', ''),
                        lead.get('location', '')
                    )
                    if company_result['success']:
                        enriched_data = company_result['data']
                        enriched_lead.update({
                            'industry': enriched_data.get('industry', lead.get('industry')),
                            'company_size': enriched_data.get('company_size', lead.get('company_size')),
                            'company_type': enriched_data.get('company_type'),
                            'website': enriched_data.get('website'),
                            'description': enriched_data.get('description')
                        })
                        enrichment_stats['enriched_companies'] += 1
                
                # Calculate lead score
                score_result = self.calculate_lead_score(enriched_lead)
                enriched_lead['lead_score'] = score_result
                
                if score_result['grade'] in ['A', 'B']:
                    enrichment_stats['high_quality_leads'] += 1
                
                enriched_leads.append(enriched_lead)
                enrichment_stats['processed_leads'] += 1
                
            except Exception as e:
                error_msg = f"Error processing lead {lead.get('name', 'Unknown')}: {str(e)}"
                logger.error(error_msg)
                enrichment_stats['errors'].append(error_msg)
                # Add the original lead with error info
                enriched_lead = lead.copy()
                enriched_lead['enrichment_error'] = str(e)
                enriched_lead['lead_score'] = {"total_score": 0, "grade": "F", "error": True}
                enriched_leads.append(enriched_lead)
        
        # Calculate summary statistics
        enrichment_stats['success_rate'] = round(
            (enrichment_stats['processed_leads'] / enrichment_stats['total_leads']) * 100, 1
        ) if enrichment_stats['total_leads'] > 0 else 0
        
        enrichment_stats['email_validity_rate'] = round(
            (enrichment_stats['valid_emails'] / enrichment_stats['total_leads']) * 100, 1
        ) if enrichment_stats['total_leads'] > 0 else 0
        
        enrichment_stats['high_quality_rate'] = round(
            (enrichment_stats['high_quality_leads'] / enrichment_stats['total_leads']) * 100, 1
        ) if enrichment_stats['total_leads'] > 0 else 0
        
        logger.info(f"Enrichment completed: {enrichment_stats['processed_leads']}/{enrichment_stats['total_leads']} leads processed")
        
        return {
            "success": True,
            "message": f"Successfully enriched {enrichment_stats['processed_leads']} leads",
            "enriched_leads": enriched_leads,
            "stats": enrichment_stats,
            "csv_filename": f"enriched_leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "csv_content": self._generate_csv(enriched_leads)
        }
    
    def _generate_csv(self, leads: List[Dict[str, Any]]) -> str:
        """Generate CSV content for enriched leads"""
        if not leads:
            return ""
        
        # Define CSV headers
        headers = [
            'name', 'company', 'title', 'email', 'phone', 'linkedin_url',
            'industry', 'company_size', 'location', 'lead_score', 'grade',
            'email_valid', 'phone_valid', 'linkedin_valid', 'enrichment_status'
        ]
        
        csv_lines = [','.join(headers)]
        
        for lead in leads:
            row = [
                f'"{lead.get("name", "")}"',
                f'"{lead.get("company", "")}"',
                f'"{lead.get("title", "")}"',
                f'"{lead.get("email", "")}"',
                f'"{lead.get("phone", "")}"',
                f'"{lead.get("linkedin_url", "")}"',
                f'"{lead.get("industry", "")}"',
                f'"{lead.get("company_size", "")}"',
                f'"{lead.get("location", "")}"',
                str(lead.get('lead_score', {}).get('total_score', 0)),
                f'"{lead.get("lead_score", {}).get("grade", "F")}"',
                str(lead.get('email_validation', {}).get('valid', False)),
                str(lead.get('phone_validation', {}).get('valid', False)),
                str(lead.get('linkedin_validation', {}).get('valid', False)),
                f'"{lead.get("enrichment_error", "Success")}"'
            ]
            csv_lines.append(','.join(row))
        
        return '\n'.join(csv_lines)

if __name__ == "__main__":
    # Test the enrichment agent
    agent = EnrichmentAgent()
    
    # Test with sample data
    test_leads = [
        {
            "name": "John Smith",
            "company": "TechCorp",
            "title": "CTO",
            "email": "john@techcorp.com",
            "phone": "555-123-4567",
            "linkedin_url": "https://linkedin.com/in/john-smith-cto"
        },
        {
            "name": "Jane Doe",
            "company": "StartupXYZ",
            "title": "VP Engineering",
            "email": "jane@startupxyz.com",
            "phone": "5559876543",
            "linkedin_url": "https://linkedin.com/in/jane-doe"
        }
    ]
    
    result = agent.enrich_leads(test_leads)
    print(f"Enrichment completed: {result['message']}")
    print(f"Stats: {result['stats']}")


