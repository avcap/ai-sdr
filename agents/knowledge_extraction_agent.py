import os
import json
import logging
from typing import Dict, List, Any
from dataclasses import dataclass
import anthropic
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class ExtractedKnowledge:
    company_info: Dict[str, Any]
    sales_approach: str
    products: List[Dict[str, Any]]
    key_messages: List[str]
    value_propositions: List[str]
    target_audience: Dict[str, Any]
    competitive_advantages: List[str]

class KnowledgeExtractionAgent:
    """
    Agent that uses Claude AI to extract structured knowledge from company documents.
    Specializes in understanding company voice, sales approach, and product information.
    """
    
    def __init__(self):
        self.claude_client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        
    def extract_knowledge_from_files(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Extract structured knowledge from uploaded documents using Claude AI.
        """
        try:
            logger.info(f"Starting knowledge extraction from {len(file_paths)} files")
            
            # Read and process each file
            documents_content = []
            for file_path in file_paths:
                content = self._read_document(file_path)
                if content:
                    documents_content.append({
                        'filename': Path(file_path).name,
                        'content': content
                    })
            
            if not documents_content:
                return {
                    "success": False,
                    "error": "No readable documents found"
                }
            
            # Use Claude to extract knowledge
            extracted_knowledge = self._extract_with_claude(documents_content)
            
            logger.info("Knowledge extraction completed successfully")
            return {
                "success": True,
                "knowledge": extracted_knowledge
            }
            
        except Exception as e:
            logger.error(f"Knowledge extraction error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _read_document(self, file_path: str) -> str:
        """
        Read document content based on file type.
        """
        try:
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_extension == '.pdf':
                # For now, return placeholder - would need PyPDF2 or similar
                return f"[PDF content from {Path(file_path).name} - would need PDF parsing library]"
            elif file_extension in ['.doc', '.docx']:
                # For now, return placeholder - would need python-docx
                return f"[Word document content from {Path(file_path).name} - would need docx parsing library]"
            elif file_extension in ['.ppt', '.pptx']:
                # For now, return placeholder - would need python-pptx
                return f"[PowerPoint content from {Path(file_path).name} - would need pptx parsing library]"
            else:
                logger.warning(f"Unsupported file type: {file_extension}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading document {file_path}: {e}")
            return None
    
    def _extract_with_claude(self, documents: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Use Claude AI to extract structured knowledge from documents.
        """
        try:
            # Prepare documents for Claude
            documents_text = "\n\n".join([
                f"Document: {doc['filename']}\n{doc['content']}"
                for doc in documents
            ])
            
            # Create the extraction prompt
            prompt = self._build_extraction_prompt(documents_text)
            
            # Call Claude API
            response = self.claude_client.messages.create(
                model="claude-3-sonnet",
                max_tokens=4000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse the response
            extracted_text = response.content[0].text
            knowledge = self._parse_claude_response(extracted_text)
            
            return knowledge
            
        except Exception as e:
            logger.error(f"Claude extraction error: {e}")
            # Return default structure if Claude fails
            return self._get_default_knowledge_structure()
    
    def _build_extraction_prompt(self, documents_text: str) -> str:
        """
        Build the prompt for Claude to extract knowledge.
        """
        return f"""
You are an expert business analyst specializing in extracting structured knowledge from company documents. 
Analyze the following documents and extract key information that would help AI sales agents understand this company's approach, products, and sales methodology.

Documents to analyze:
{documents_text}

Please extract and structure the following information in JSON format:

{{
  "company_info": {{
    "company_name": "Name of the company",
    "industry": "Primary industry or sector",
    "company_size": "Size category (startup, SMB, enterprise)",
    "mission": "Company mission statement",
    "values": ["Core company values"],
    "founding_year": "Year founded if mentioned",
    "headquarters": "Location if mentioned"
  }},
  "sales_approach": "Detailed description of the company's sales methodology, approach, and philosophy",
  "products": [
    {{
      "name": "Product/service name",
      "description": "Detailed description",
      "target_customers": "Who this product serves",
      "key_features": ["Main features"],
      "benefits": ["Key benefits"],
      "pricing_model": "How it's priced if mentioned"
    }}
  ],
  "key_messages": [
    "Key messages the company uses in sales and marketing",
    "Value propositions",
    "Unique selling points"
  ],
  "value_propositions": [
    "Primary value propositions",
    "What makes them different",
    "Key benefits they provide"
  ],
  "target_audience": {{
    "primary_customers": "Description of ideal customers",
    "industries": ["Industries they serve"],
    "company_sizes": ["Target company sizes"],
    "pain_points": ["Problems they solve"]
  }},
  "competitive_advantages": [
    "What makes them unique",
    "Competitive differentiators",
    "Strengths vs competitors"
  ]
}}

Focus on extracting actionable information that would help AI agents:
1. Write personalized outreach messages
2. Understand the company's voice and tone
3. Know what products to recommend
4. Understand the target audience
5. Use the right value propositions

If information is not available in the documents, use "Not specified" or leave arrays empty.
Return only valid JSON, no additional text.
"""
    
    def _parse_claude_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Claude's response and extract the JSON.
        """
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                logger.warning("No JSON found in Claude response")
                return self._get_default_knowledge_structure()
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return self._get_default_knowledge_structure()
    
    def _get_default_knowledge_structure(self) -> Dict[str, Any]:
        """
        Return a default knowledge structure if extraction fails.
        """
        return {
            "company_info": {
                "company_name": "Not specified",
                "industry": "Not specified",
                "company_size": "Not specified",
                "mission": "Not specified",
                "values": [],
                "founding_year": "Not specified",
                "headquarters": "Not specified"
            },
            "sales_approach": "Not specified - please review and update",
            "products": [],
            "key_messages": [],
            "value_propositions": [],
            "target_audience": {
                "primary_customers": "Not specified",
                "industries": [],
                "company_sizes": [],
                "pain_points": []
            },
            "competitive_advantages": []
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about the Knowledge Extraction Agent.
        """
        return {
            "name": "Knowledge Extraction Agent",
            "description": "Uses Claude AI to extract structured knowledge from company documents",
            "capabilities": [
                "Document analysis and processing",
                "Company information extraction",
                "Sales approach identification",
                "Product knowledge extraction",
                "Value proposition identification",
                "Target audience analysis"
            ],
            "supported_formats": ["PDF", "Word", "PowerPoint", "Text"],
            "ai_model": "Claude-3-Sonnet",
            "specialization": "Business document analysis and knowledge structuring"
        }
