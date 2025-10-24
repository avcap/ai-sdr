# Enhanced Lead Ingestion Strategy

## Current Options Analysis

### Option 1: CSV Upload (Current)
**Pros:**
- ✅ Simple implementation
- ✅ Works offline
- ✅ No Google dependency

**Cons:**
- ❌ File management overhead
- ❌ No real-time updates
- ❌ Manual re-uploads needed
- ❌ Version control issues

### Option 2: Google Sheets Integration (Recommended)
**Pros:**
- ✅ Uses existing Google OAuth
- ✅ Real-time collaboration
- ✅ Version history
- ✅ Familiar interface
- ✅ No file uploads
- ✅ Automatic updates

**Cons:**
- ❌ Requires Google account
- ❌ Internet dependency

## Recommended Implementation

### Step 1: Add Google Sheets Lead Ingestion
1. **Sheets Picker**: Let users select from their Google Sheets
2. **Sheet Preview**: Show column headers and sample data
3. **Column Mapping**: Map sheet columns to lead fields
4. **Data Validation**: Validate data before import

### Step 2: Enhanced User Flow
```
1. User connects Google account ✅ (Already done)
2. User clicks "Import Leads from Google Sheets"
3. System shows list of user's spreadsheets
4. User selects the lead sheet
5. System previews data and maps columns
6. User confirms import
7. Leads are imported and ready for campaigns
```

### Step 3: Technical Implementation

#### Backend Endpoints Needed:
- `GET /google/sheets/list` - List user's spreadsheets
- `GET /google/sheets/{sheet_id}/preview` - Preview sheet data
- `POST /google/sheets/{sheet_id}/import` - Import leads from sheet

#### Frontend Components Needed:
- `SheetsPicker` - Dropdown of available sheets
- `SheetPreview` - Table showing sample data
- `ColumnMapper` - Map sheet columns to lead fields
- `ImportConfirmation` - Final confirmation step

## Quick Implementation Plan

### Phase 1: Basic Sheets Integration (1-2 hours)
1. Add endpoint to list user's Google Sheets
2. Add endpoint to read sheet data
3. Update frontend to show sheets picker
4. Import leads directly from selected sheet

### Phase 2: Enhanced Features (2-3 hours)
1. Add column mapping interface
2. Add data validation
3. Add preview functionality
4. Add error handling

## Code Structure

### Backend Endpoints:
```python
@app.get("/google/sheets/list")
async def list_user_sheets(current_user, db):
    # Return list of user's Google Sheets

@app.get("/google/sheets/{sheet_id}/preview")
async def preview_sheet(sheet_id, current_user, db):
    # Return first 10 rows of sheet data

@app.post("/google/sheets/{sheet_id}/import")
async def import_leads_from_sheet(sheet_id, campaign_id, current_user, db):
    # Import leads from sheet to campaign
```

### Frontend Components:
```jsx
// SheetsPicker.jsx
const SheetsPicker = ({ onSheetSelect }) => {
  // Show dropdown of available sheets
}

// SheetPreview.jsx
const SheetPreview = ({ sheetData }) => {
  // Show table preview of sheet data
}

// ColumnMapper.jsx
const ColumnMapper = ({ columns, onMapping }) => {
  // Map sheet columns to lead fields
}
```

## User Experience Flow

1. **Dashboard**: "Import Leads" button
2. **Sheets Selection**: Dropdown of available sheets
3. **Preview**: Table showing sample data
4. **Mapping**: Map columns to lead fields
5. **Confirmation**: Review and confirm import
6. **Success**: Leads imported to campaign

## Benefits of This Approach

- **User-Friendly**: Familiar Google Sheets interface
- **Efficient**: No file uploads or management
- **Scalable**: Works with any size dataset
- **Collaborative**: Multiple users can update the same sheet
- **Real-time**: Changes reflect immediately
- **Reliable**: Google's infrastructure

## Next Steps

1. Implement basic sheets listing endpoint
2. Add sheet data reading functionality
3. Update frontend with sheets picker
4. Test with sample Google Sheet
5. Add column mapping and validation
6. Deploy and test with real users

This approach leverages the existing Google OAuth integration and provides a much better user experience than file uploads.


