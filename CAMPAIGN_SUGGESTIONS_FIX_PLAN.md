# Fix Campaign Suggestions - Remove Hardcoded Data & Enable Real LLM Analysis

## Current Problem

**Campaign suggestions are completely hardcoded** in `services/campaign_intelligence_service.py`:

1. **Lines 42-60**: Knowledge extraction is bypassed with hardcoded mock documents
2. **Lines 500-592**: `_get_document_based_suggestions()` generates static suggestions based on filename patterns, not actual content
3. **No LLM analysis**: Claude is NOT analyzing document content for suggestions
4. **Same suggestions every time**: Users always see the same 3 suggestions regardless of their actual uploaded documents

### Current Flow (BROKEN):
```
User uploads docs → Knowledge extracted → Stored in Supabase
                                              ↓
User opens Smart Campaign modal → analyze_for_campaigns() called
                                              ↓
                                    Hardcoded mock documents used
                                              ↓
                                    Filename pattern matching only
                                              ↓
                                    Same 3 suggestions every time
```

## Root Cause Analysis

### Issue 1: Knowledge Extraction Bypass
```python
# Lines 42-60 in campaign_intelligence_service.py
logger.info("Using document-based suggestions (knowledge extraction temporarily disabled)")
mock_documents = [
    {'filename': 'avius_llc_company_info.txt', 'document_type': 'company_info', ...},
    {'filename': 'Sales_Book-_Free_eBook-MEP.pdf', 'document_type': 'sales_training', ...}
]
```
**Problem**: Real documents are ignored, mock data is always used.

### Issue 2: No LLM Content Analysis
```python
# Lines 500-592: _get_document_based_suggestions()
if 'avius' in filename:
    company_name = "Avius LLC"
    suggestions.append({
        'title': f'{company_name} Executive Outreach',
        'prompt': 'Find me 15 CTOs...',  # Static text
        'reasoning': 'Based on company information document',  # Generic
        'confidence': 0.7  # Fixed score
    })
```
**Problem**: Only checks filenames, doesn't read or analyze actual document content with Claude.

### Issue 3: Unreachable Code
```python
# Lines 62-81: This code is never executed
return result  # Early return on line 60 prevents reaching LLM analysis code below
```
**Problem**: Real LLM suggestion logic exists but is unreachable due to early return.

---

## Solution Architecture

### Desired Flow:
```
User uploads docs → KnowledgeExtractionAgent extracts with Claude
                                              ↓
                                    Stored in Supabase user_knowledge table
                                              ↓
User opens Smart Campaign modal → analyze_for_campaigns() called
                                              ↓
                                    Fetch real knowledge from Supabase
                                              ↓
                                    Claude analyzes aggregated content
                                              ↓
                                    Generate 3 unique, contextual suggestions
                                              ↓
                                    Save to campaign_suggestions table
                                              ↓
                                    Return to frontend with confidence scores
```

---

## Implementation Plan

### Phase 1: Remove Hardcoded Mock Data
**Goal**: Enable real document retrieval from Supabase

#### Step 1.1: Remove Mock Documents (lines 42-60)
**File**: `services/campaign_intelligence_service.py`

```python
# REMOVE THIS ENTIRE BLOCK:
logger.info("Using document-based suggestions (knowledge extraction temporarily disabled)")
mock_documents = [...]
result = self._get_document_based_suggestions(mock_documents)
return result
```

**Replace with**:
```python
# Get real uploaded documents from database
documents = self.supabase.get_user_documents(tenant_id, user_id)

if not documents:
    logger.warning(f"No documents found for user {user_id}")
    return self._get_default_campaign_insights()

logger.info(f"Found {len(documents)} documents for analysis")
```

#### Step 1.2: Add get_user_documents() to SupabaseService
**File**: `services/supabase_service.py`

```python
def get_user_documents(self, tenant_id: str, user_id: str) -> List[Dict[str, Any]]:
    """
    Get all uploaded documents for a user.
    
    Args:
        tenant_id: User's tenant ID
        user_id: User's ID
        
    Returns:
        List of document records with id, filename, document_type, file_path, created_at
    """
    try:
        response = (
            self.client
            .from_('uploaded_documents')
            .select('id, filename, document_type, file_path, created_at, extracted_content')
            .eq('tenant_id', tenant_id)
            .eq('user_id', user_id)
            .order('created_at', desc=True)
            .execute()
        )
        
        if response.data:
            logger.info(f"Retrieved {len(response.data)} documents for user {user_id}")
            return response.data
        
        return []
        
    except Exception as e:
        logger.error(f"Error retrieving user documents: {e}")
        return []
```

---

### Phase 2: Enable Real LLM Analysis
**Goal**: Use Claude to analyze document content and generate contextual suggestions

#### Step 2.1: Fix Knowledge Retrieval Flow
**File**: `services/campaign_intelligence_service.py` (line 40-41)

**Current**:
```python
knowledge = self.knowledge_service.get_user_knowledge(tenant_id, user_id, task_type='campaign')
# Then immediately bypassed with mock data
```

**Update**:
```python
# Get aggregated knowledge from all user documents
knowledge = self.knowledge_service.get_user_knowledge(tenant_id, user_id, task_type='campaign')

if not knowledge or knowledge.get('source_count', 0) == 0:
    logger.warning(f"No knowledge available for user {user_id}")
    return self._get_default_campaign_insights()

logger.info(f"Retrieved knowledge from {knowledge.get('source_count', 0)} sources")
```

#### Step 2.2: Implement _generate_llm_suggestions() Method
**File**: `services/campaign_intelligence_service.py`

**Update the existing method** (it exists but has placeholder logic):

```python
def _generate_llm_suggestions(self, campaign_context: Dict[str, Any], count: int = 3) -> List[Dict[str, Any]]:
    """
    Use Claude to generate contextual campaign suggestions from extracted knowledge.
    
    Args:
        campaign_context: Extracted campaign context from documents
        count: Number of suggestions to generate
        
    Returns:
        List of LLM-generated campaign suggestions
    """
    try:
        # Build comprehensive context from knowledge
        company_name = campaign_context.get('company_name', 'Your Company')
        industry = campaign_context.get('industry', 'Technology')
        products = campaign_context.get('products', [])
        target_audience = campaign_context.get('target_audience', {})
        value_props = campaign_context.get('value_propositions', [])
        sales_approach = campaign_context.get('sales_approach', '')
        competitive_advantages = campaign_context.get('competitive_advantages', [])
        
        # Create rich prompt for Claude
        analysis_prompt = f"""
        Analyze this company's information and generate {count} highly specific, actionable campaign suggestions.
        
        COMPANY PROFILE:
        - Company: {company_name}
        - Industry: {industry}
        - Products/Services: {', '.join(products[:5]) if products else 'Not specified'}
        - Target Audience: {json.dumps(target_audience, indent=2)}
        - Value Propositions: {', '.join(value_props[:3]) if value_props else 'Not specified'}
        - Sales Approach: {sales_approach or 'Not specified'}
        - Competitive Advantages: {', '.join(competitive_advantages[:3]) if competitive_advantages else 'Not specified'}
        
        INSTRUCTIONS:
        Generate {count} unique campaign suggestions that are:
        1. Specific to this company's offerings and target market
        2. Include concrete prospecting criteria (roles, company sizes, industries)
        3. Reference specific pain points or value propositions
        4. Include actionable prompts ready to execute
        
        For each suggestion, provide:
        - title: Compelling campaign title (max 60 chars)
        - prompt: Complete, specific prospecting prompt with target roles, company size, industry, and qualifying criteria
        - reasoning: Why this campaign fits the company's profile (2-3 sentences, reference specific company details)
        - confidence: Score from 0.0-1.0 based on how well company data supports this campaign
        - category: Campaign category (executive_prospecting, mid_market, enterprise_focus, industry_specific, problem_focused)
        
        Return ONLY valid JSON array:
        [
            {{
                "title": "...",
                "prompt": "...",
                "reasoning": "...",
                "confidence": 0.85,
                "category": "..."
            }}
        ]
        """
        
        # Call Claude for analysis
        logger.info(f"🤖 Calling Claude to generate {count} campaign suggestions")
        
        response = self.claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.7,  # Allow some creativity
            messages=[{
                "role": "user",
                "content": analysis_prompt
            }]
        )
        
        # Parse Claude's response
        suggestions_text = response.content[0].text.strip()
        
        # Extract JSON from response (handle code blocks)
        if "```json" in suggestions_text:
            suggestions_text = suggestions_text.split("```json")[1].split("```")[0].strip()
        elif "```" in suggestions_text:
            suggestions_text = suggestions_text.split("```")[1].split("```")[0].strip()
        
        suggestions = json.loads(suggestions_text)
        
        # Add metadata to each suggestion
        for i, suggestion in enumerate(suggestions):
            suggestion['id'] = f"llm_{hashlib.md5(suggestion['title'].encode()).hexdigest()[:8]}"
            suggestion['generated_at'] = datetime.now().isoformat()
            suggestion['model_used'] = 'claude-3-5-sonnet'
        
        logger.info(f"✅ Generated {len(suggestions)} LLM-powered suggestions")
        
        # Save suggestions to database for tracking
        for suggestion in suggestions:
            self._save_suggestion_to_db(suggestion, campaign_context.get('tenant_id'), campaign_context.get('user_id'))
        
        return suggestions[:count]
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude's response as JSON: {e}")
        logger.error(f"Response text: {suggestions_text}")
        return self._get_fallback_suggestions()
        
    except Exception as e:
        logger.error(f"Error generating LLM suggestions: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return self._get_fallback_suggestions()
```

#### Step 2.3: Update _extract_campaign_context() Method
**File**: `services/campaign_intelligence_service.py` (lines 115-165)

**Current**: Returns mostly empty defaults

**Update**:
```python
def _extract_campaign_context(self, knowledge: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract campaign-relevant context from aggregated knowledge.
    
    Args:
        knowledge: User's aggregated knowledge from knowledge_service
        
    Returns:
        Dict containing campaign context for LLM
    """
    # Extract real data from aggregated knowledge
    company_info = knowledge.get('company_info', {})
    
    context = {
        'company_name': company_info.get('company_name', 'Your Company'),
        'industry': company_info.get('industry', knowledge.get('industry_context', {}).get('industry', 'Technology')),
        'products': knowledge.get('products', []),
        'target_audience': knowledge.get('target_audience', {}),
        'sales_approach': knowledge.get('sales_approach', ''),
        'competitive_advantages': knowledge.get('competitive_advantages', []),
        'value_propositions': knowledge.get('value_propositions', []),
        'key_messages': knowledge.get('key_messages', []),
        'sales_methodologies': knowledge.get('sales_methodologies', []),
        'source_count': knowledge.get('source_count', 0)
    }
    
    logger.info(f"📊 Extracted campaign context: {context['company_name']} in {context['industry']}")
    
    return context
```

---

### Phase 3: Database Integration
**Goal**: Save and track LLM-generated suggestions

#### Step 3.1: Update _save_suggestion_to_db() Method
**File**: `services/campaign_intelligence_service.py`

```python
def _save_suggestion_to_db(self, suggestion: Dict[str, Any], tenant_id: str = None, user_id: str = None) -> bool:
    """
    Save campaign suggestion to database for analytics and tracking.
    
    Args:
        suggestion: Suggestion dictionary
        tenant_id: User's tenant ID
        user_id: User's ID
        
    Returns:
        True if saved successfully
    """
    if not tenant_id or not user_id:
        logger.warning("Cannot save suggestion: missing tenant_id or user_id")
        return False
    
    try:
        suggestion_data = {
            'tenant_id': tenant_id,
            'user_id': user_id,
            'suggestion_type': suggestion.get('category', 'general'),
            'prompt_text': suggestion.get('prompt', ''),
            'reasoning': suggestion.get('reasoning', ''),
            'confidence_score': suggestion.get('confidence', 0.7),
            'metadata': {
                'title': suggestion.get('title', ''),
                'model_used': suggestion.get('model_used', 'claude'),
                'generated_at': suggestion.get('generated_at', datetime.now().isoformat())
            }
        }
        
        response = self.supabase.client.from_('campaign_suggestions').insert(suggestion_data).execute()
        
        if response.data:
            logger.info(f"💾 Saved suggestion to database: {suggestion.get('title', 'Untitled')}")
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error saving suggestion to database: {e}")
        return False
```

#### Step 3.2: Add Claude Client to __init__
**File**: `services/campaign_intelligence_service.py`

```python
def __init__(self):
    self.knowledge_service = KnowledgeService()
    self.learning_service = CampaignLearningService()
    self.supabase = SupabaseService()
    
    # Add Claude client for LLM analysis
    import anthropic
    self.claude_client = anthropic.Anthropic(
        api_key=os.getenv('ANTHROPIC_API_KEY')
    )
```

---

### Phase 4: Improve Error Handling & No Documents State
**Goal**: Clear messaging when no documents uploaded, graceful LLM error handling

#### Step 4.1: Update _get_default_campaign_insights() - No Suggestions When No Documents
**File**: `services/campaign_intelligence_service.py`

```python
def _get_default_campaign_insights(self) -> Dict[str, Any]:
    """
    Return default insights when no knowledge is available.
    User MUST upload documents to get suggestions.
    """
    return {
        'target_audience': {
            'buyer_personas': [],
            'company_sizes': [],
            'industries': [],
            'pain_points': []
        },
        'industry_focus': '',
        'product_categories': [],
        'sales_approach': '',
        'competitive_positioning': [],
        'suggested_campaigns': [],  # EMPTY - no suggestions without documents
        'document_count': 0,
        'analysis_timestamp': datetime.now().isoformat(),
        'has_knowledge': False,
        'message': 'No training data available. Please upload documents in the Knowledge Bank to get AI-powered campaign suggestions.',
        'call_to_action': 'Upload company information, product details, sales training materials, or website links in the Knowledge Bank to enable smart campaign suggestions.'
    }
```

#### Step 4.2: Add LLM Fallback ONLY for API Errors (Not Empty Knowledge)
**File**: `services/campaign_intelligence_service.py`

```python
def _handle_llm_error_fallback(self, error: Exception, campaign_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fallback when LLM API fails BUT user has uploaded documents.
    Uses extracted knowledge to create basic suggestions without LLM analysis.
    
    Only called when:
    - User HAS documents uploaded
    - Claude API fails (rate limit, timeout, error)
    
    Args:
        error: The exception that occurred
        campaign_context: Extracted context from user's documents
        
    Returns:
        List of basic suggestions derived from extracted knowledge (not generic)
    """
    logger.error(f"LLM API error, using knowledge-based fallback: {error}")
    
    company_name = campaign_context.get('company_name', 'Your Company')
    industry = campaign_context.get('industry', 'your industry')
    products = campaign_context.get('products', [])
    target_audience = campaign_context.get('target_audience', {})
    
    # Extract target roles from knowledge
    buyer_personas = target_audience.get('buyer_personas', [])
    if not buyer_personas:
        buyer_personas = ['decision makers', 'executives']
    
    # Create 1-2 basic suggestions using extracted knowledge
    suggestions = []
    
    # Suggestion 1: Based on company info
    suggestions.append({
        'id': 'knowledge_fallback_1',
        'title': f'{company_name} Target Audience Outreach',
        'prompt': f'Find me {", ".join(buyer_personas[:2])} at companies in {industry}',
        'reasoning': f'Based on your uploaded company information. (Note: Claude API unavailable - using basic suggestion from extracted knowledge)',
        'confidence': 0.5,
        'category': 'knowledge_based',
        'generated_at': datetime.now().isoformat(),
        'is_fallback': True,
        'fallback_reason': 'llm_api_error'
    })
    
    # Suggestion 2: If we have product info
    if products:
        suggestions.append({
            'id': 'knowledge_fallback_2',
            'title': f'{products[0]} Product-Focused Campaign',
            'prompt': f'Target decision makers interested in {products[0]} solutions',
            'reasoning': f'Based on your product information. (Note: Claude API unavailable - using basic suggestion from extracted knowledge)',
            'confidence': 0.5,
            'category': 'knowledge_based',
            'generated_at': datetime.now().isoformat(),
            'is_fallback': True,
            'fallback_reason': 'llm_api_error'
        })
    
    return suggestions[:2]  # Return 1-2 suggestions based on available knowledge
```

#### Step 4.3: Update analyze_for_campaigns() Logic
**File**: `services/campaign_intelligence_service.py`

```python
def analyze_for_campaigns(self, tenant_id: str, user_id: str) -> Dict[str, Any]:
    """
    Analyze user's uploaded documents and generate AI-powered campaign suggestions.
    """
    try:
        logger.info(f"Analyzing documents for campaigns for user {user_id}")
        
        # Get user's knowledge from uploaded documents
        knowledge = self.knowledge_service.get_user_knowledge(tenant_id, user_id, task_type='campaign')
        
        # Check if user has uploaded any documents
        if not knowledge or knowledge.get('source_count', 0) == 0:
            logger.warning(f"No documents found for user {user_id} - cannot generate suggestions")
            return self._get_default_campaign_insights()
        
        logger.info(f"Retrieved knowledge from {knowledge.get('source_count', 0)} sources")
        
        # Extract campaign context from knowledge
        campaign_context = self._extract_campaign_context(knowledge)
        campaign_context['tenant_id'] = tenant_id
        campaign_context['user_id'] = user_id
        
        # Try to generate LLM-powered suggestions
        try:
            suggestions = self._generate_llm_suggestions(campaign_context, count=3)
        except Exception as llm_error:
            # LLM failed but user HAS documents - use knowledge-based fallback
            logger.error(f"LLM generation failed: {llm_error}")
            suggestions = self._handle_llm_error_fallback(llm_error, campaign_context)
        
        # Calculate insights
        insights = {
            'target_audience': campaign_context.get('target_audience', {}),
            'industry_focus': campaign_context.get('industry', 'Technology'),
            'product_categories': campaign_context.get('products', []),
            'sales_approach': campaign_context.get('sales_approach', ''),
            'competitive_positioning': campaign_context.get('competitive_advantages', []),
            'suggested_campaigns': suggestions,
            'document_count': knowledge.get('source_count', 0),
            'analysis_timestamp': datetime.now().isoformat(),
            'has_knowledge': True
        }
        
        logger.info(f"Generated {len(suggestions)} campaign suggestions")
        return insights
        
    except Exception as e:
        logger.error(f"Error analyzing documents for campaigns: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Major error - return no suggestions
        return self._get_default_campaign_insights()
```

---

### Phase 5: Frontend Enhancement
**Goal**: Show LLM analysis quality and prompt user to upload docs

#### Step 5.1: Update Smart Campaign Modal
**File**: `frontend/components/SmartCampaign.js`

Add visual indicators for suggestion quality:

```javascript
// In the suggestions rendering section
{suggestions.map((suggestion, index) => (
  <div
    key={index}
    onClick={() => handleSuggestionClick(suggestion)}
    className={`p-4 border rounded-lg cursor-pointer transition-all ${
      selectedSuggestion?.title === suggestion.title
        ? 'border-blue-500 bg-blue-50'
        : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
    }`}
  >
    <div className="flex items-start justify-between mb-2">
      <h4 className="font-semibold text-gray-800">{suggestion.title}</h4>
      <div className="flex items-center gap-2">
        {/* Confidence Badge */}
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          suggestion.confidence >= 0.8 ? 'bg-green-100 text-green-800' :
          suggestion.confidence >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
          'bg-gray-100 text-gray-600'
        }`}>
          {Math.round(suggestion.confidence * 100)}% match
        </span>
        
        {/* Fallback Indicator */}
        {suggestion.is_fallback && (
          <span className="px-2 py-1 rounded text-xs bg-orange-100 text-orange-700">
            Generic
          </span>
        )}
      </div>
    </div>
    
    <p className="text-sm text-gray-600 mb-3">{suggestion.prompt}</p>
    
    <div className="flex items-start gap-2">
      <svg className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p className="text-xs text-gray-500 italic">{suggestion.reasoning}</p>
    </div>
  </div>
))}
```

#### Step 5.2: Add Empty State UI - NO Suggestions Without Documents
**File**: `frontend/components/SmartCampaign.js`

```javascript
{/* Show empty state when NO documents uploaded */}
{(!suggestions || suggestions.length === 0) && campaignInsights?.has_knowledge === false && (
  <div className="mb-6 p-6 bg-blue-50 border-2 border-blue-200 rounded-lg">
    <div className="flex flex-col items-center text-center gap-3">
      <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
        <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      </div>
      
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Upload Training Data to Get Smart Suggestions
        </h3>
        <p className="text-sm text-gray-600 mb-4 max-w-md">
          {campaignInsights?.message || 'Upload company information, product details, sales training materials, or website links in the Knowledge Bank to enable AI-powered campaign suggestions.'}
        </p>
        
        <button
          onClick={() => router.push('/knowledge-bank')}
          className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          Go to Knowledge Bank
        </button>
      </div>
      
      <div className="mt-4 pt-4 border-t border-blue-200 w-full">
        <p className="text-xs text-gray-500 mb-3">You can upload:</p>
        <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-blue-400 rounded-full"></span>
            Company Information
          </div>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-blue-400 rounded-full"></span>
            Product Details
          </div>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-blue-400 rounded-full"></span>
            Sales Training Materials
          </div>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-blue-400 rounded-full"></span>
            Website Content
          </div>
        </div>
      </div>
    </div>
  </div>
)}

{/* Show warning banner when using LLM error fallback */}
{suggestions && suggestions.length > 0 && suggestions[0]?.is_fallback && suggestions[0]?.fallback_reason === 'llm_api_error' && (
  <div className="mb-4 p-4 bg-orange-50 border border-orange-200 rounded-lg">
    <div className="flex items-start gap-3">
      <svg className="w-5 h-5 text-orange-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <div>
        <p className="text-sm font-medium text-orange-800 mb-1">
          Using Basic Suggestions
        </p>
        <p className="text-xs text-orange-700">
          Claude AI is temporarily unavailable. Showing basic suggestions based on your uploaded documents. Try again later for enhanced AI-powered suggestions.
        </p>
      </div>
    </div>
  </div>
)}
```

Add router import at top of file:
```javascript
import { useRouter } from 'next/router';

// In component:
const router = useRouter();
```

---

## Testing Checklist

### Test Case 1: No Documents Uploaded ✅ CORRECT BEHAVIOR
- [ ] User opens Smart Campaign without uploading any documents
- [ ] Should see **ZERO suggestions** (empty array)
- [ ] Should see blue empty state card with:
  - Icon and "Upload Training Data to Get Smart Suggestions" heading
  - Message: "No training data available. Please upload documents..."
  - "Go to Knowledge Bank" button
  - List of uploadable document types
- [ ] **Should NOT show generic suggestions**

### Test Case 2: Single Company Document
- [ ] User uploads `avius_llc_company_info.txt`
- [ ] Knowledge extraction runs successfully with Claude
- [ ] Open Smart Campaign modal
- [ ] Should see **3 AI-generated suggestions** referencing:
  - "Avius LLC" by name
  - "AI agents" or specific products from document
  - Specific target roles extracted from document
- [ ] Confidence scores should be **60-80%** (based on single source)
- [ ] Reasoning should quote or reference **specific company details** from the document
- [ ] No "Generic" or "Fallback" tags

### Test Case 3: Multiple Document Types (Best Case)
- [ ] User uploads company info + sales training + product docs
- [ ] All documents processed and knowledge extracted
- [ ] Open Smart Campaign modal
- [ ] Should see **3 unique suggestions** combining insights:
  - Suggestion 1: Company + product focus
  - Suggestion 2: Sales methodology + target audience
  - Suggestion 3: Competitive positioning angle
- [ ] Confidence scores should be **75-95%** (high confidence with multiple sources)
- [ ] Each suggestion references different document insights
- [ ] Prompts should be highly specific and actionable

### Test Case 4: LLM API Failure (Claude Down)
- [ ] User HAS uploaded documents (knowledge exists)
- [ ] Temporarily break Claude API key or mock API error
- [ ] Open Smart Campaign modal
- [ ] Should see **1-2 knowledge-based fallback suggestions** (NOT generic)
- [ ] Suggestions use extracted knowledge (company name, products, roles)
- [ ] Should see **orange warning banner**: "Using Basic Suggestions"
- [ ] Banner explains: "Claude AI is temporarily unavailable"
- [ ] Confidence scores should be **~50%** (lower than LLM-generated)
- [ ] Suggestions marked with `is_fallback: true` and `fallback_reason: 'llm_api_error'`

### Test Case 5: Website URL Upload
- [ ] User uploads website URL in Knowledge Bank
- [ ] Content extracted and processed
- [ ] Open Smart Campaign modal
- [ ] Should see **3 suggestions** based on website content
- [ ] Reasoning references website data

### Test Case 6: Suggestion Quality (LLM-Generated)
- [ ] Prompts must include:
  - Specific roles (e.g., "CTOs and VPs of Engineering")
  - Company size ranges (e.g., "50-200 employees")
  - Industry qualifiers (e.g., "SaaS companies in healthcare")
  - Qualifying criteria (e.g., "evaluating AI automation tools")
- [ ] Reasoning must:
  - Reference actual company data (not "Based on company information document")
  - Quote specific products, values, or strategies
  - Explain WHY this campaign fits the company
- [ ] Confidence scores:
  - Single document: 0.6-0.8
  - Multiple documents: 0.75-0.95
  - Fallback (LLM error): 0.5
  - No documents: N/A (no suggestions)

---

## Success Metrics

### Before Fix:
- ❌ Same 3 hardcoded suggestions for all users
- ❌ 0% personalization (filename pattern matching only)
- ❌ No Claude analysis of content
- ❌ Fake confidence scores (always 70%)
- ❌ Generic reasoning ("Based on document")
- ❌ Shows suggestions even with no documents

### After Fix:
- ✅ **NO suggestions without documents** (empty state with CTA)
- ✅ Unique suggestions per user based on actual document content
- ✅ **Claude 3.5 Sonnet analyzes** actual extracted knowledge
- ✅ Real confidence scores:
  - 0.75-0.95 (multiple documents)
  - 0.6-0.8 (single document)
  - 0.5 (fallback when Claude fails)
  - N/A (no documents = no suggestions)
- ✅ Reasoning references **specific company data** from documents
- ✅ Graceful fallback when Claude API fails (uses extracted knowledge)
- ✅ Clear UI states for all scenarios

---

## Implementation Priority

### High Priority (Do First):
1. ✅ Phase 1: Remove hardcoded mock data
2. ✅ Phase 2: Enable LLM analysis with Claude
3. ✅ Phase 3: Database integration for tracking

### Medium Priority:
4. ✅ Phase 4: Improve fallback handling
5. ✅ Phase 5: Frontend visual enhancements

### Low Priority (Future):
6. Add caching for suggestions (24-hour TTL)
7. Track which suggestions are used most
8. A/B test different prompt engineering approaches
9. Add "regenerate suggestions" button

---

## Files to Modify

1. **services/campaign_intelligence_service.py** (Primary)
   - Lines 42-60: Remove mock documents
   - Lines 115-165: Fix `_extract_campaign_context()`
   - Lines 200-250: Update `_generate_llm_suggestions()`
   - Lines 500-592: Delete `_get_document_based_suggestions()` (no longer needed)
   - Line ~30: Add Claude client to `__init__`

2. **services/supabase_service.py** (New method)
   - Add `get_user_documents()` method

3. **frontend/components/SmartCampaign.js** (Enhancement)
   - Add confidence score badges
   - Add fallback/generic indicators
   - Add empty state message for no documents

---

## Rollback Plan

If LLM suggestions cause issues:

1. Keep `_get_fallback_suggestions()` as safety net
2. Add feature flag in `.env`: `ENABLE_LLM_SUGGESTIONS=true`
3. Wrap LLM code in conditional:
   ```python
   if os.getenv('ENABLE_LLM_SUGGESTIONS', 'true').lower() == 'true':
       suggestions = self._generate_llm_suggestions(campaign_context)
   else:
       suggestions = self._get_fallback_suggestions()
   ```
4. Can disable instantly by setting `ENABLE_LLM_SUGGESTIONS=false`

---

## Estimated Implementation Time

- Phase 1: 15 minutes
- Phase 2: 30 minutes
- Phase 3: 15 minutes
- Phase 4: 15 minutes
- Phase 5: 20 minutes
- Testing: 30 minutes

**Total: ~2 hours**

