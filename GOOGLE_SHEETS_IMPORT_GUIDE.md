# Google Sheets Lead Import Template

## Sample Lead Data Structure

Create a Google Sheet with the following columns for optimal import:

| Name | Company | Title | Email | LinkedIn URL | Phone | Industry | Company Size | Location |
|------|---------|-------|-------|--------------|-------|----------|--------------|----------|
| John Smith | TechCorp Inc | VP of Engineering | john@techcorp.com | https://linkedin.com/in/johnsmith | +1-555-0123 | Technology | 100-500 | San Francisco CA |
| Sarah Johnson | DataFlow Systems | CTO | sarah@dataflow.com | https://linkedin.com/in/sarahjohnson | +1-555-0124 | Data Analytics | 50-100 | Austin TX |
| Mike Chen | StartupXYZ | Founder | mike@startupxyz.com | https://linkedin.com/in/mikechen | +1-555-0125 | Fintech | 10-50 | New York NY |
| Lisa Rodriguez | MarketingPro | Marketing Director | lisa@marketingpro.com | https://linkedin.com/in/lisarodriguez | +1-555-0126 | Marketing | 500-1000 | Chicago IL |
| David Kim | CloudTech Solutions | CTO | david@cloudtech.com | https://linkedin.com/in/davidkim | +1-555-0127 | Cloud Computing | 100-500 | Seattle WA |

## Required Columns
- **Name** (required): Full name of the lead
- **Company** (required): Company name
- **Title** (required): Job title or position

## Optional Columns
- **Email**: Email address for outreach
- **LinkedIn URL**: LinkedIn profile URL
- **Phone**: Phone number
- **Industry**: Industry sector
- **Company Size**: Size of the company
- **Location**: Geographic location

## Import Process

1. **Connect Google Account**: Authorize the app to access your Google Sheets
2. **Select Sheet**: Choose from your existing Google Sheets
3. **Preview Data**: Review the first 10 rows of data
4. **Map Columns**: Map sheet columns to lead fields
5. **Import**: Confirm and import leads to your campaign

## Tips for Best Results

- Use consistent column headers (exactly as shown above)
- Ensure data quality (no empty required fields)
- Use proper email formats
- Include LinkedIn URLs when available
- Add industry and company size for better personalization

## Column Mapping

The system will automatically try to map columns based on:
- Exact matches (Name → name)
- Partial matches (Company Name → company)
- Keyword matching (Email Address → email)

You can manually adjust the mapping during the import process.

## Troubleshooting

### Common Issues:
- **Missing required fields**: Ensure Name, Company, and Title columns exist
- **Empty rows**: Remove completely empty rows
- **Special characters**: Avoid special characters in column headers
- **Data types**: Keep data consistent (all emails in email column, etc.)

### Error Messages:
- "No Google account connected": Connect your Google account first
- "Sheet not found": Check sheet permissions and sharing settings
- "Invalid column mapping": Ensure required fields are mapped correctly
- "No data found": Check if sheet has data in the expected format

## Sample CSV for Testing

If you prefer to test with CSV upload first, use this sample data:

```csv
Name,Company,Title,Email,LinkedIn URL,Phone,Industry,Company Size,Location
John Smith,TechCorp Inc,VP of Engineering,john@techcorp.com,https://linkedin.com/in/johnsmith,+1-555-0123,Technology,100-500,San Francisco CA
Sarah Johnson,DataFlow Systems,CTO,sarah@dataflow.com,https://linkedin.com/in/sarahjohnson,+1-555-0124,Data Analytics,50-100,Austin TX
Mike Chen,StartupXYZ,Founder,mike@startupxyz.com,https://linkedin.com/in/mikechen,+1-555-0125,Fintech,10-50,New York NY
Lisa Rodriguez,MarketingPro,Marketing Director,lisa@marketingpro.com,https://linkedin.com/in/lisarodriguez,+1-555-0126,Marketing,500-1000,Chicago IL
David Kim,CloudTech Solutions,CTO,david@cloudtech.com,https://linkedin.com/in/davidkim,+1-555-0127,Cloud Computing,100-500,Seattle WA
```

## Next Steps

After importing leads:
1. Review imported leads in the campaign dashboard
2. Set up your campaign messaging
3. Execute the campaign to send personalized outreach
4. Track responses and meetings in real-time
5. Export results to Google Sheets for further analysis


