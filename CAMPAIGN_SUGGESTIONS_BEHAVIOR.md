# Campaign Suggestions Behavior - Updated Plan

## Key Design Decision

**NO SUGGESTIONS WITHOUT TRAINING DATA**

The campaign suggestions feature will **only work** when users have uploaded documents or provided training data. This ensures all suggestions are contextual and personalized.

---

## Three Scenarios

### 1️⃣ No Documents Uploaded (No Training Data)
**User Experience:**
- Opens Smart Campaign modal
- Sees **0 suggestions** (empty array)
- Sees beautiful empty state UI:
  - 📄 Icon with heading "Upload Training Data to Get Smart Suggestions"
  - Clear message explaining need for documents
  - **"Go to Knowledge Bank"** button (call-to-action)
  - List of acceptable document types (company info, products, sales training, websites)

**Backend Behavior:**
```python
# returns
{
  'suggested_campaigns': [],  # EMPTY
  'document_count': 0,
  'has_knowledge': False,
  'message': 'No training data available. Please upload documents...',
  'call_to_action': 'Upload company information, product details...'
}
```

**Why this approach?**
- Forces users to add value before getting value
- Ensures all suggestions are contextual, not generic
- Clear onboarding path to Knowledge Bank
- No confusion with fake/generic suggestions

---

### 2️⃣ Documents Uploaded + Claude Working (Normal Operation)
**User Experience:**
- Opens Smart Campaign modal
- Sees **3 AI-generated suggestions**
- Each suggestion includes:
  - Title referencing company/product (e.g., "Avius LLC AI Agents Outreach")
  - Specific prompt with roles, company sizes, industries
  - Reasoning that quotes actual document content
  - Confidence score: **75-95%** (green badge)
  - No "fallback" or "generic" tags

**Backend Behavior:**
```python
# Claude 3.5 Sonnet analyzes extracted knowledge:
suggestions = claude.messages.create(
    model="claude-3-5-sonnet-20241022",
    prompt=f"""
    Generate 3 campaign suggestions for:
    - Company: {company_name}
    - Products: {products}
    - Target Audience: {target_audience}
    - Value Props: {value_propositions}
    ...
    """
)

# Returns personalized suggestions
{
  'suggested_campaigns': [
    {
      'title': 'Avius LLC AI Agent Automation Outreach',
      'prompt': 'Find me 20 CTOs at 100-500 employee tech companies evaluating AI automation',
      'reasoning': 'Avius specializes in AI agents for task automation. This targets decision makers at mid-market companies likely to invest in AI solutions for operational efficiency.',
      'confidence': 0.85,
      'category': 'product_focused'
    }
  ],
  'document_count': 3,
  'has_knowledge': True
}
```

**Why this approach?**
- True personalization using actual document content
- High confidence scores reflect strong data foundation
- Actionable, ready-to-execute prompts
- Builds trust in AI capabilities

---

### 3️⃣ Documents Uploaded + Claude API Fails (Graceful Degradation)
**User Experience:**
- Opens Smart Campaign modal
- Sees **1-2 basic suggestions** (using extracted knowledge, not LLM)
- Orange warning banner: "Using Basic Suggestions"
  - "Claude AI is temporarily unavailable. Showing basic suggestions based on your uploaded documents."
- Each suggestion includes:
  - Title using company name from knowledge
  - Prompt using extracted roles/industry
  - Reasoning explains it's a fallback: "(Note: Claude API unavailable - using basic suggestion from extracted knowledge)"
  - Confidence score: **~50%** (yellow/orange badge)
  - Tagged with `is_fallback: true` and `fallback_reason: 'llm_api_error'`

**Backend Behavior:**
```python
try:
    # Try Claude first
    suggestions = self._generate_llm_suggestions(campaign_context)
except Exception as llm_error:
    # Fallback to knowledge-based suggestions
    suggestions = self._handle_llm_error_fallback(llm_error, campaign_context)
    
# Returns basic suggestions from extracted knowledge:
{
  'suggested_campaigns': [
    {
      'title': 'Avius LLC Target Audience Outreach',
      'prompt': 'Find me CTOs, VPs of Engineering at companies in technology',
      'reasoning': 'Based on your uploaded company information. (Note: Claude API unavailable - using basic suggestion from extracted knowledge)',
      'confidence': 0.5,
      'is_fallback': True,
      'fallback_reason': 'llm_api_error'
    }
  ],
  'document_count': 3,
  'has_knowledge': True
}
```

**Why this approach?**
- User still gets value (better than nothing)
- Suggestions use their actual data (company name, extracted roles)
- Clear communication about degraded experience
- Encourages retry later for full AI experience

---

## Decision Matrix

| Scenario | Documents? | Claude API? | Suggestions | Confidence | UI State |
|----------|-----------|-------------|-------------|------------|----------|
| **1** | ❌ No | N/A | **0** | N/A | Empty state + CTA |
| **2** | ✅ Yes | ✅ Working | **3** | 75-95% | Normal (green) |
| **3** | ✅ Yes | ❌ Failed | **1-2** | ~50% | Warning banner (orange) |

---

## Implementation Notes

### Backend Changes
1. **Remove all hardcoded mock documents** (lines 42-60)
2. **Remove `_get_document_based_suggestions()`** method (filename pattern matching)
3. **Return empty suggestions when `source_count == 0`**
4. **Add `_handle_llm_error_fallback()`** for graceful degradation
5. **Update `_generate_llm_suggestions()`** to use Claude 3.5 Sonnet

### Frontend Changes
1. **Add empty state UI** when `suggestions.length === 0 && has_knowledge === false`
2. **Add router.push('/knowledge-bank')** button
3. **Add orange warning banner** when `suggestions[0].is_fallback === true`
4. **Add confidence badges** (green 80%+, yellow 60-80%, orange <60%)

---

## User Flow Example

### New User Experience:
1. **Signs up** → Dashboard
2. **Clicks "Smart Campaign"** → Sees empty state
3. **Clicks "Go to Knowledge Bank"** → Uploads `company_info.txt`
4. **Document processed** → Knowledge extracted
5. **Returns to Smart Campaign** → Sees 3 personalized suggestions
6. **Clicks suggestion** → Executes campaign with leads

### Returning User with Data:
1. **Opens Smart Campaign** → Immediately sees 3 suggestions
2. **Uploads new document** → Suggestions regenerate (more context)
3. **Claude API down (rare)** → Sees warning + basic suggestions

---

## Why No Generic Fallback?

**Original plan had generic suggestions for no documents. Why removed?**

1. **Confusing UX**: Users would think the system is working but get poor results
2. **No value**: Generic "Find CTOs in tech" suggestions are not better than letting user type their own prompt
3. **Trust issue**: If suggestions are generic, users won't trust them when they ARE personalized
4. **Onboarding**: Empty state forces proper onboarding (upload documents first)
5. **Product positioning**: We're selling AI-powered personalization, not generic templates

**Better approach:**
- Show clear empty state
- Guide user to Knowledge Bank
- Only show suggestions when we can be confident they're good
- Build trust with quality over quantity

---

## Testing Commands

### Test Scenario 1: No Documents
```bash
# Delete all user documents in Supabase
# Open Smart Campaign modal
# Expected: Empty state UI with "Go to Knowledge Bank" button
```

### Test Scenario 2: With Documents
```bash
# Upload avius_llc_company_info.txt
# Wait for knowledge extraction
# Open Smart Campaign modal
# Expected: 3 suggestions mentioning "Avius LLC" and "AI agents"
```

### Test Scenario 3: Claude API Error
```bash
# Temporarily set ANTHROPIC_API_KEY=""
# Open Smart Campaign modal (with existing documents)
# Expected: Orange warning banner + 1-2 basic suggestions
```

---

## Success Criteria

✅ **No suggestions shown without documents**
✅ **Empty state guides users to upload documents**
✅ **Claude generates contextual suggestions when documents exist**
✅ **Graceful degradation when Claude API fails**
✅ **Clear UI indicators for all three states**
✅ **Confidence scores reflect data quality**
✅ **All suggestions are actionable (specific roles, sizes, industries)**

