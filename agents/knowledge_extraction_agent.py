import os
import json
import logging
from typing import Dict, List, Any
from dataclasses import dataclass
import anthropic
from pathlib import Path
import pypdf
from docx import Document
import pptx

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
        
    def extract_knowledge_from_files(self, file_paths: List[str], document_type: str = None) -> Dict[str, Any]:
        """
        Extract structured knowledge from uploaded documents using Claude AI.
        
        Args:
            file_paths: List of file paths to process
            document_type: Optional document type to guide extraction
        """
        try:
            logger.info(f"Starting knowledge extraction from {len(file_paths)} files")
            if document_type:
                logger.info(f"Using explicit document type: {document_type}")
            
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
            
            # Use Claude to extract knowledge with optional document type
            extracted_knowledge = self._extract_with_claude(documents_content, document_type)
            
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
                return self._read_pdf(file_path)
            elif file_extension in ['.doc', '.docx']:
                return self._read_word_document(file_path)
            elif file_extension in ['.ppt', '.pptx']:
                return self._read_powerpoint(file_path)
            else:
                logger.warning(f"Unsupported file type: {file_extension}")
                return None
                
        except Exception as e:
            logger.error(f"Error reading document {file_path}: {e}")
            return None
    
    def _read_pdf(self, file_path: str) -> str:
        """Read PDF content using pypdf."""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text.strip()
        except Exception as e:
            logger.error(f"Error reading PDF {file_path}: {e}")
            return f"[Error reading PDF: {str(e)}]"
    
    def _read_word_document(self, file_path: str) -> str:
        """Read Word document content using python-docx."""
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error reading Word document {file_path}: {e}")
            return f"[Error reading Word document: {str(e)}]"
    
    def _read_powerpoint(self, file_path: str) -> str:
        """Read PowerPoint content using python-pptx."""
        try:
            prs = pptx.Presentation(file_path)
            text = ""
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"Error reading PowerPoint {file_path}: {e}")
            return f"[Error reading PowerPoint: {str(e)}]"
    
    def _extract_with_claude(self, documents: List[Dict[str, str]], document_type: str = None) -> Dict[str, Any]:
        """
        Use Claude AI to extract structured knowledge from documents.
        
        Args:
            documents: List of document content
            document_type: Optional explicit document type to guide extraction
        """
        try:
            # Prepare documents for Claude
            documents_text = "\n\n".join([
                f"Document: {doc['filename']}\n{doc['content']}"
                for doc in documents
            ])
            
            # Create the extraction prompt with optional document type
            prompt = self._build_extraction_prompt(documents_text, document_type)
            
            # Call Claude API
            response = self.claude_client.messages.create(
                model="claude-3-haiku-20240307",
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
    
    def _build_extraction_prompt(self, documents_text: str, document_type: str = None) -> str:
        """
        Build the prompt for Claude to extract knowledge based on document type.
        
        Args:
            documents_text: The content of documents to analyze
            document_type: Optional explicit document type to guide extraction
        """
        if document_type:
            # Use explicit document type - skip detection step
            return self._build_targeted_prompt(documents_text, document_type)
        else:
            # Use automatic detection (existing logic)
            return self._build_detection_prompt(documents_text)
    
    def _build_targeted_prompt(self, documents_text: str, document_type: str) -> str:
        """
        Build a targeted prompt for a specific document type.
        """
        if document_type == "company_info":
            return f"""
You are an expert business analyst specializing in extracting company information from documents.

Extract the following information from the documents:

Documents to analyze:
{documents_text}

Extract company information in this JSON format:
{{
  "document_type": "company_info",
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

IMPORTANT INSTRUCTIONS:
1. If information is not available, use "Not specified" or leave arrays empty
2. Focus on extracting actionable information that would help AI sales agents
3. Return only valid JSON, no additional text

Return the JSON structure.
"""
        
        elif document_type == "products":
            return f"""
You are an expert business analyst specializing in extracting product information from documents.

Extract the following information from the documents:

Documents to analyze:
{documents_text}

Extract product information in this JSON format:
{{
  "document_type": "products",
  "products": [
    {{
      "name": "Product/service name",
      "description": "Detailed description",
      "target_customers": "Who this product serves",
      "key_features": ["Main features"],
      "benefits": ["Key benefits"],
      "pricing_model": "How it's priced if mentioned",
      "use_cases": ["Specific use cases"],
      "integration_requirements": ["Technical requirements"],
      "competitors": ["Competing products/services"]
    }}
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
  ],
  "key_messages": [
    "Key messages about the products",
    "Value propositions",
    "Unique selling points"
  ]
}}

IMPORTANT INSTRUCTIONS:
1. If information is not available, use "Not specified" or leave arrays empty
2. Focus on extracting actionable information that would help AI sales agents
3. Return only valid JSON, no additional text

Return the JSON structure.
"""
        
        elif document_type == "sales_training":
            return f"""
You are an expert business analyst specializing in extracting sales training knowledge from documents.

Extract the following information from the documents:

Documents to analyze:
{documents_text}

Extract sales training knowledge in this JSON format:
{{
  "document_type": "sales_training",
  "sales_methodologies": [
    "Sales techniques and approaches mentioned",
    "Best practices for prospecting",
    "Communication strategies"
  ],
  "target_audience_insights": {{
    "buyer_personas": ["Types of buyers mentioned"],
    "pain_points": ["Common problems prospects face"],
    "decision_making_process": ["How buyers make decisions"]
  }},
  "sales_philosophy": "Overall sales approach and mindset",
  "key_messages": [
    "Important sales messages and frameworks",
    "Value propositions that work",
    "Objection handling techniques"
  ],
  "industry_context": {{
    "industries_mentioned": ["Industries discussed"],
    "market_trends": ["Trends and insights"],
    "competitive_landscape": ["Competitive information"]
  }},
  "practical_advice": [
    "Actionable sales tips",
    "Scripts and templates",
    "Follow-up strategies"
  ]
}}

IMPORTANT INSTRUCTIONS:
1. If information is not available, use "Not specified" or leave arrays empty
2. Focus on extracting actionable information that would help AI sales agents
3. Return only valid JSON, no additional text

Return the JSON structure.
"""
        
        else:
            # Fallback to detection prompt for unknown types
            return self._build_detection_prompt(documents_text)
    
    def _build_detection_prompt(self, documents_text: str) -> str:
        """
        Build the original detection-based prompt (existing logic).
        """
        return f"""
You are an expert business analyst specializing in extracting structured knowledge from various types of documents. 
First, analyze the following documents to determine their type, then extract relevant information accordingly.

Documents to analyze:
{documents_text}

STEP 1: Determine the document type(s) from these categories:
- "company_info": Documents about a specific company (business plans, company profiles, product sheets)
- "sales_training": Training materials about sales techniques, methodologies, or best practices
- "industry_knowledge": Documents about industries, markets, or general business knowledge
- "product_docs": Technical documentation, user manuals, or product specifications
- "mixed": Documents containing multiple types of information

STEP 2: Extract knowledge based on the document type(s):

For COMPANY_INFO documents, extract:
{{
  "document_type": "company_info",
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

For SALES_TRAINING documents, extract:
{{
  "document_type": "sales_training",
  "sales_methodologies": [
    "Sales techniques and approaches mentioned",
    "Best practices for prospecting",
    "Communication strategies"
  ],
  "target_audience_insights": {{
    "buyer_personas": ["Types of buyers mentioned"],
    "pain_points": ["Common problems prospects face"],
    "decision_making_process": ["How buyers make decisions"]
  }},
  "sales_philosophy": "Overall sales approach and mindset",
  "key_messages": [
    "Important sales messages and frameworks",
    "Value propositions that work",
    "Objection handling techniques"
  ],
  "industry_context": {{
    "industries_mentioned": ["Industries discussed"],
    "market_trends": ["Trends and insights"],
    "competitive_landscape": ["Competitive information"]
  }},
  "practical_advice": [
    "Actionable sales tips",
    "Scripts and templates",
    "Follow-up strategies"
  ]
}}

For INDUSTRY_KNOWLEDGE documents, extract:
{{
  "document_type": "industry_knowledge",
  "industry_insights": {{
    "industries_covered": ["Industries discussed"],
    "market_size": "Market information if mentioned",
    "growth_trends": ["Growth patterns and trends"],
    "key_players": ["Major companies mentioned"]
  }},
  "buyer_behavior": {{
    "decision_makers": ["Types of decision makers"],
    "purchase_process": ["How buying decisions are made"],
    "pain_points": ["Common industry challenges"]
  }},
  "sales_opportunities": [
    "Potential sales opportunities mentioned",
    "Timing considerations",
    "Market entry strategies"
  ],
  "competitive_intelligence": [
    "Competitive information",
    "Market positioning insights",
    "Differentiation strategies"
  ]
}}

For MIXED documents, extract the most relevant information from the appropriate categories above.

IMPORTANT INSTRUCTIONS:
1. If the document is clearly about sales training (like "how to be the best AI SDR"), use the sales_training format
2. If the document is about a specific company, use the company_info format
3. If the document is about industries or markets, use the industry_knowledge format
4. If information is not available, use "Not specified" or leave arrays empty
5. Focus on extracting actionable information that would help AI sales agents
6. Return only valid JSON, no additional text

Return the appropriate JSON structure based on the document type you identify.
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
            "document_type": "company_info",
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
