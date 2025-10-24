import gspread
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import os
import pandas as pd
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SheetRow:
    row_number: int
    data: Dict[str, Any]

@dataclass
class CampaignSheet:
    spreadsheet_id: str
    worksheet_name: str
    headers: List[str]
    data: List[Dict[str, Any]]

class GoogleSheetsService:
    def __init__(self):
        self.credentials_file = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json")
        self.token_file = os.getenv("GOOGLE_SHEETS_TOKEN_FILE", "token.json")
        self.spreadsheet_id = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")
        
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        self.service = None
        self.gc = None  # gspread client
        
        if os.path.exists(self.credentials_file):
            self._authenticate()
        else:
            logger.warning("Google Sheets credentials file not found")
    
    def _authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            # Method 1: Service Account (recommended for production)
            if os.path.exists(self.credentials_file):
                creds = Credentials.from_service_account_file(
                    self.credentials_file, 
                    scopes=self.scopes
                )
                self.service = build('sheets', 'v4', credentials=creds)
                self.gc = gspread.service_account(filename=self.credentials_file)
                logger.info("Authenticated with Google Sheets using service account")
                return
            
            # Method 2: OAuth2 (for user authentication)
            creds = None
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes)
                    creds = flow.run_local_server(port=0)
                
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('sheets', 'v4', credentials=creds)
            logger.info("Authenticated with Google Sheets using OAuth2")
            
        except Exception as e:
            logger.error(f"Error authenticating with Google Sheets: {e}")
            raise e
    
    def create_spreadsheet(self, title: str) -> str:
        """Create a new Google Spreadsheet"""
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                }
            }
            
            spreadsheet = self.service.spreadsheets().create(
                body=spreadsheet,
                fields='spreadsheetId'
            ).execute()
            
            spreadsheet_id = spreadsheet.get('spreadsheetId')
            logger.info(f"Created spreadsheet: {spreadsheet_id}")
            
            return spreadsheet_id
            
        except Exception as e:
            logger.error(f"Error creating spreadsheet: {e}")
            raise e
    
    def create_worksheet(self, spreadsheet_id: str, worksheet_name: str, headers: List[str]) -> bool:
        """Create a new worksheet with headers"""
        try:
            # Add worksheet
            requests = [{
                'addSheet': {
                    'properties': {
                        'title': worksheet_name
                    }
                }
            }]
            
            body = {'requests': requests}
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            # Add headers
            self.update_range(
                spreadsheet_id,
                f"{worksheet_name}!A1:{chr(65 + len(headers) - 1)}1",
                [headers]
            )
            
            logger.info(f"Created worksheet '{worksheet_name}' with headers")
            return True
            
        except Exception as e:
            logger.error(f"Error creating worksheet: {e}")
            return False
    
    def update_range(self, spreadsheet_id: str, range_name: str, values: List[List[Any]]) -> bool:
        """Update a range of cells in the spreadsheet"""
        try:
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Updated {result.get('updatedCells')} cells")
            return True
            
        except Exception as e:
            logger.error(f"Error updating range: {e}")
            return False
    
    def append_rows(self, spreadsheet_id: str, worksheet_name: str, rows: List[List[Any]]) -> bool:
        """Append rows to a worksheet"""
        try:
            range_name = f"{worksheet_name}!A:Z"
            
            body = {
                'values': rows
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"Appended {len(rows)} rows")
            return True
            
        except Exception as e:
            logger.error(f"Error appending rows: {e}")
            return False
    
    def read_range(self, spreadsheet_id: str, range_name: str) -> List[List[Any]]:
        """Read data from a range"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            return values
            
        except Exception as e:
            logger.error(f"Error reading range: {e}")
            return []
    
    def get_worksheet_data(self, spreadsheet_id: str, worksheet_name: str) -> List[Dict[str, Any]]:
        """Get all data from a worksheet as list of dictionaries"""
        try:
            range_name = f"{worksheet_name}!A:Z"
            values = self.read_range(spreadsheet_id, range_name)
            
            if not values:
                return []
            
            headers = values[0]
            data = []
            
            for row in values[1:]:
                row_dict = {}
                for i, value in enumerate(row):
                    if i < len(headers):
                        row_dict[headers[i]] = value
                data.append(row_dict)
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting worksheet data: {e}")
            return []
    
    def create_campaign_tracking_sheet(self, campaign_id: str, campaign_name: str) -> str:
        """Create a comprehensive campaign tracking sheet"""
        try:
            # Create spreadsheet
            spreadsheet_id = self.create_spreadsheet(f"AI SDR Campaign - {campaign_name}")
            
            # Create worksheets
            worksheets = [
                {
                    "name": "Campaign Overview",
                    "headers": [
                        "Campaign ID", "Campaign Name", "Status", "Created At", 
                        "Total Leads", "Processed Leads", "Successful Outreach",
                        "Responses Received", "Meetings Scheduled", "Success Rate"
                    ]
                },
                {
                    "name": "Leads",
                    "headers": [
                        "Lead ID", "Name", "Company", "Title", "Email", 
                        "LinkedIn URL", "Phone", "Industry", "Company Size", 
                        "Location", "Status", "Created At"
                    ]
                },
                {
                    "name": "Outreach Logs",
                    "headers": [
                        "Log ID", "Campaign ID", "Lead ID", "Channel", 
                        "Message Sent", "Sent At", "Response Received", 
                        "Response At", "Meeting Scheduled", "Meeting Date", "Status"
                    ]
                },
                {
                    "name": "Analytics",
                    "headers": [
                        "Date", "Total Sent", "Delivered", "Opened", 
                        "Clicked", "Replied", "Meetings Booked", 
                        "Response Rate", "Meeting Rate"
                    ]
                }
            ]
            
            for worksheet in worksheets:
                self.create_worksheet(
                    spreadsheet_id, 
                    worksheet["name"], 
                    worksheet["headers"]
                )
            
            # Add campaign overview data
            overview_data = [
                [
                    campaign_id,
                    campaign_name,
                    "Draft",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "0", "0", "0", "0", "0", "0%"
                ]
            ]
            
            self.append_rows(spreadsheet_id, "Campaign Overview", overview_data)
            
            logger.info(f"Created campaign tracking sheet: {spreadsheet_id}")
            return spreadsheet_id
            
        except Exception as e:
            logger.error(f"Error creating campaign tracking sheet: {e}")
            raise e
    
    def log_campaign_metrics(self, spreadsheet_id: str, campaign_id: str, metrics: Dict[str, Any]) -> bool:
        """Log campaign metrics to the analytics worksheet"""
        try:
            analytics_data = [
                [
                    datetime.now().strftime("%Y-%m-%d"),
                    metrics.get("total_sent", 0),
                    metrics.get("delivered", 0),
                    metrics.get("opened", 0),
                    metrics.get("clicked", 0),
                    metrics.get("replied", 0),
                    metrics.get("meetings_booked", 0),
                    f"{metrics.get('response_rate', 0):.2f}%",
                    f"{metrics.get('meeting_rate', 0):.2f}%"
                ]
            ]
            
            return self.append_rows(spreadsheet_id, "Analytics", analytics_data)
            
        except Exception as e:
            logger.error(f"Error logging campaign metrics: {e}")
            return False
    
    def log_outreach_activity(self, spreadsheet_id: str, outreach_data: Dict[str, Any]) -> bool:
        """Log outreach activity to the outreach logs worksheet"""
        try:
            log_data = [
                [
                    outreach_data.get("log_id", ""),
                    outreach_data.get("campaign_id", ""),
                    outreach_data.get("lead_id", ""),
                    outreach_data.get("channel", ""),
                    outreach_data.get("message_sent", False),
                    outreach_data.get("sent_at", ""),
                    outreach_data.get("response_received", False),
                    outreach_data.get("response_at", ""),
                    outreach_data.get("meeting_scheduled", False),
                    outreach_data.get("meeting_date", ""),
                    outreach_data.get("status", "")
                ]
            ]
            
            return self.append_rows(spreadsheet_id, "Outreach Logs", log_data)
            
        except Exception as e:
            logger.error(f"Error logging outreach activity: {e}")
            return False
    
    def export_campaign_data(self, spreadsheet_id: str, output_format: str = "csv") -> str:
        """Export campaign data from spreadsheet"""
        try:
            # Get all worksheets data
            worksheets = ["Campaign Overview", "Leads", "Outreach Logs", "Analytics"]
            all_data = {}
            
            for worksheet_name in worksheets:
                data = self.get_worksheet_data(spreadsheet_id, worksheet_name)
                all_data[worksheet_name] = data
            
            if output_format.lower() == "csv":
                # Create CSV files for each worksheet
                output_files = []
                for worksheet_name, data in all_data.items():
                    if data:
                        df = pd.DataFrame(data)
                        filename = f"{worksheet_name.lower().replace(' ', '_')}.csv"
                        df.to_csv(filename, index=False)
                        output_files.append(filename)
                
                return f"Exported {len(output_files)} files"
            
            elif output_format.lower() == "excel":
                # Create Excel file with multiple sheets
                filename = "campaign_export.xlsx"
                with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                    for worksheet_name, data in all_data.items():
                        if data:
                            df = pd.DataFrame(data)
                            df.to_excel(writer, sheet_name=worksheet_name, index=False)
                
                return f"Exported to {filename}"
            
            else:
                raise ValueError("Unsupported output format")
                
        except Exception as e:
            logger.error(f"Error exporting campaign data: {e}")
            raise e
    
    def get_campaign_summary(self, spreadsheet_id: str) -> Dict[str, Any]:
        """Get campaign summary from spreadsheet"""
        try:
            # Get campaign overview
            overview_data = self.get_worksheet_data(spreadsheet_id, "Campaign Overview")
            
            if not overview_data:
                return {"error": "No campaign data found"}
            
            campaign_info = overview_data[0]
            
            # Get leads count
            leads_data = self.get_worksheet_data(spreadsheet_id, "Leads")
            
            # Get outreach logs
            outreach_data = self.get_worksheet_data(spreadsheet_id, "Outreach Logs")
            
            # Calculate metrics
            total_leads = len(leads_data)
            successful_outreach = len([log for log in outreach_data if log.get("Message Sent") == "TRUE"])
            responses_received = len([log for log in outreach_data if log.get("Response Received") == "TRUE"])
            meetings_scheduled = len([log for log in outreach_data if log.get("Meeting Scheduled") == "TRUE"])
            
            return {
                "campaign_id": campaign_info.get("Campaign ID"),
                "campaign_name": campaign_info.get("Campaign Name"),
                "status": campaign_info.get("Status"),
                "total_leads": total_leads,
                "successful_outreach": successful_outreach,
                "responses_received": responses_received,
                "meetings_scheduled": meetings_scheduled,
                "response_rate": (responses_received / successful_outreach * 100) if successful_outreach > 0 else 0,
                "meeting_rate": (meetings_scheduled / responses_received * 100) if responses_received > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting campaign summary: {e}")
            return {"error": str(e)}
    
    def sync_campaign_data(self, spreadsheet_id: str, campaign_data: Dict[str, Any]) -> bool:
        """Sync campaign data with spreadsheet"""
        try:
            # Update campaign overview
            overview_range = "Campaign Overview!A2:J2"
            overview_values = [
                [
                    campaign_data.get("campaign_id", ""),
                    campaign_data.get("name", ""),
                    campaign_data.get("status", ""),
                    campaign_data.get("created_at", ""),
                    str(campaign_data.get("total_leads", 0)),
                    str(campaign_data.get("processed_leads", 0)),
                    str(campaign_data.get("successful_outreach", 0)),
                    str(campaign_data.get("responses_received", 0)),
                    str(campaign_data.get("meetings_scheduled", 0)),
                    f"{campaign_data.get('success_rate', 0):.2f}%"
                ]
            ]
            
            self.update_range(spreadsheet_id, overview_range, overview_values)
            
            # Add leads data
            leads_data = campaign_data.get("leads", [])
            if leads_data:
                leads_rows = []
                for lead in leads_data:
                    leads_rows.append([
                        lead.get("id", ""),
                        lead.get("name", ""),
                        lead.get("company", ""),
                        lead.get("title", ""),
                        lead.get("email", ""),
                        lead.get("linkedin_url", ""),
                        lead.get("phone", ""),
                        lead.get("industry", ""),
                        lead.get("company_size", ""),
                        lead.get("location", ""),
                        lead.get("status", ""),
                        lead.get("created_at", "")
                    ])
                
                self.append_rows(spreadsheet_id, "Leads", leads_rows)
            
            logger.info("Campaign data synced successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error syncing campaign data: {e}")
            return False
