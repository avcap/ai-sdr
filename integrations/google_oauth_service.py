import os
import json
import base64
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import gspread
from gspread.exceptions import APIError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class GoogleOAuthService:
    def __init__(self):
        # Use environment variables for the OAuth app credentials
        # These are YOUR app's credentials that users will authorize against
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")
        
        # Scopes for Gmail and Google Sheets
        self.scopes = [
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/gmail.readonly',
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/drive.file'  # Added drive.file scope
        ]
        
        if not all([self.client_id, self.client_secret]):
            logger.warning("Google OAuth credentials not configured")
    
    def get_authorization_url(self, state: str = None) -> str:
        """Get Google OAuth authorization URL"""
        if not self.client_id:
            raise ValueError("Google OAuth not configured")
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.scopes
        )
        flow.redirect_uri = self.redirect_uri
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state
        )
        
        return authorization_url
    
    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access tokens"""
        if not self.client_id:
            raise ValueError("Google OAuth not configured")
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri]
                }
            },
            scopes=self.scopes
        )
        flow.redirect_uri = self.redirect_uri
        
        flow.fetch_token(code=code)
        
        credentials = flow.credentials
        
        # Validate that we have the required scopes (Google may return additional scopes)
        required_scopes = set(self.scopes)
        granted_scopes = set(credentials.scopes) if credentials.scopes else set()
        
        if not required_scopes.issubset(granted_scopes):
            missing_scopes = required_scopes - granted_scopes
            logger.warning(f"Missing required scopes: {missing_scopes}")
        
        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "expires_at": credentials.expiry.isoformat() if credentials.expiry else None,
            "scopes": list(granted_scopes)  # Return all granted scopes
        }
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        if not self.client_id:
            raise ValueError("Google OAuth not configured")
        
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=self.scopes
        )
        
        credentials.refresh(Request())
        
        return {
            "access_token": credentials.token,
            "expires_at": credentials.expiry.isoformat() if credentials.expiry else None
        }
    
    def get_gmail_service(self, access_token: str):
        """Get Gmail service instance"""
        credentials = Credentials(token=access_token)
        return build('gmail', 'v1', credentials=credentials)
    
    def get_sheets_service(self, access_token: str):
        """Get Google Sheets service instance"""
        credentials = Credentials(token=access_token)
        return gspread.authorize(credentials)
    
    def send_email_via_gmail(self, access_token: str, to_email: str, subject: str, body: str, from_email: str = None) -> Dict[str, Any]:
        """Send email using Gmail API"""
        try:
            service = self.get_gmail_service(access_token)
            
            # Get user's email address
            if not from_email:
                profile = service.users().getProfile(userId='me').execute()
                from_email = profile['emailAddress']
            
            # Create email message
            message = self._create_email_message(from_email, to_email, subject, body)
            
            # Send email
            result = service.users().messages().send(
                userId='me',
                body={'raw': message}
            ).execute()
            
            logger.info(f"Email sent via Gmail API to {to_email}")
            
            return {
                "success": True,
                "message_id": result['id'],
                "sent_at": datetime.now().isoformat(),
                "recipient": to_email
            }
            
        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipient": to_email
            }
        except Exception as e:
            logger.error(f"Failed to send email via Gmail: {e}")
            return {
                "success": False,
                "error": str(e),
                "recipient": to_email
            }
    
    def _create_email_message(self, from_email: str, to_email: str, subject: str, body: str) -> str:
        """Create email message in Gmail API format"""
        import email.mime.text
        
        message = email.mime.text.MIMEText(body)
        message['to'] = to_email
        message['from'] = from_email
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return raw_message
    
    def create_spreadsheet(self, access_token: str, title: str) -> Dict[str, Any]:
        """Create a new Google Spreadsheet"""
        try:
            gc = self.get_sheets_service(access_token)
            spreadsheet = gc.create(title)
            
            # Share with the user's email
            spreadsheet.share('', perm_type='anyone', role='writer')
            
            return {
                "success": True,
                "spreadsheet_id": spreadsheet.id,
                "spreadsheet_url": spreadsheet.url,
                "title": title
            }
            
        except APIError as e:
            logger.error(f"Google Sheets API error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Failed to create spreadsheet: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_leads_to_spreadsheet(self, access_token: str, spreadsheet_id: str, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Add leads to Google Spreadsheet"""
        try:
            gc = self.get_sheets_service(access_token)
            spreadsheet = gc.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.sheet1
            
            # Prepare headers
            headers = ['Name', 'Company', 'Title', 'Email', 'Industry', 'Company Size', 'Location', 'Status', 'Last Contact', 'Notes']
            
            # Clear existing data and add headers
            worksheet.clear()
            worksheet.append_row(headers)
            
            # Add leads data
            for lead in leads:
                row = [
                    lead.get('name', ''),
                    lead.get('company', ''),
                    lead.get('title', ''),
                    lead.get('email', ''),
                    lead.get('industry', ''),
                    lead.get('company_size', ''),
                    lead.get('location', ''),
                    'Pending',
                    '',
                    ''
                ]
                worksheet.append_row(row)
            
            return {
                "success": True,
                "rows_added": len(leads),
                "spreadsheet_url": spreadsheet.url
            }
            
        except APIError as e:
            logger.error(f"Google Sheets API error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Failed to add leads to spreadsheet: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_lead_status(self, access_token: str, spreadsheet_id: str, lead_email: str, status: str, notes: str = "") -> Dict[str, Any]:
        """Update lead status in spreadsheet"""
        try:
            gc = self.get_sheets_service(access_token)
            spreadsheet = gc.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.sheet1
            
            # Find the row with the lead's email
            cell = worksheet.find(lead_email)
            if cell:
                row = cell.row
                # Update status and notes columns (columns 8 and 10)
                worksheet.update_cell(row, 8, status)
                worksheet.update_cell(row, 9, datetime.now().strftime('%Y-%m-%d %H:%M'))
                worksheet.update_cell(row, 10, notes)
                
                return {
                    "success": True,
                    "row_updated": row
                }
            else:
                return {
                    "success": False,
                    "error": "Lead not found in spreadsheet"
                }
                
        except APIError as e:
            logger.error(f"Google Sheets API error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"Failed to update lead status: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def send_email_via_gmail(self, access_token: str, to_email: str, subject: str, body: str, from_email: str = None) -> Dict[str, Any]:
        """Send email via Gmail API with custom from_email"""
        try:
            service = self.get_gmail_service(access_token)
            
            # Get user's email if not provided
            if not from_email:
                profile = service.users().getProfile(userId='me').execute()
                from_email = profile['emailAddress']
            
            message = MIMEMultipart()
            message['to'] = to_email
            message['from'] = from_email
            message['subject'] = subject
            message.attach(MIMEText(body, 'plain'))
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            send_message = (service.users().messages().send(
                userId='me', 
                body={'raw': raw_message}
            ).execute())
            
            logger.info(f"Gmail API message sent. Message Id: {send_message['id']}")
            return {
                "success": True, 
                "message_id": send_message['id'],
                "sent_at": datetime.now().isoformat(),
                "from_email": from_email,
                "to_email": to_email
            }
        except HttpError as error:
            logger.error(f"An error occurred sending Gmail message: {error}")
            return {"success": False, "error": str(error)}
        except Exception as e:
            logger.error(f"An unexpected error occurred sending Gmail message: {e}")
            return {"success": False, "error": str(e)}

    def list_user_sheets(self, access_token: str) -> List[Dict[str, Any]]:
        """List user's Google Sheets, excluding campaign-generated sheets"""
        try:
            service = self.get_sheets_service(access_token)
            # Use Drive API to list spreadsheets
            drive_service = build('drive', 'v3', credentials=Credentials(access_token, client_id=self.client_id, client_secret=self.client_secret))
            
            # Query for Google Sheets files, excluding campaign-generated ones
            # Include both owned and shared files
            results = drive_service.files().list(
                q="mimeType='application/vnd.google-apps.spreadsheet'",
                fields="files(id, name, createdTime, modifiedTime, webViewLink)",
                includeItemsFromAllDrives=True,
                supportsAllDrives=True
            ).execute()
            
            sheets = []
            for file in results.get('files', []):
                # Filter out campaign-generated sheets
                if not file['name'].startswith('AI SDR Campaign -'):
                    sheets.append({
                        "id": file['id'],
                        "name": file['name'],
                        "created_time": file.get('createdTime'),
                        "modified_time": file.get('modifiedTime'),
                        "url": file.get('webViewLink')
                    })
            
            logger.info(f"Found {len(sheets)} user-created Google Sheets (excluding campaign sheets)")
            return sheets
        except HttpError as error:
            logger.error(f"An error occurred listing sheets: {error}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred listing sheets: {e}")
            return []

    def preview_sheet_data(self, access_token: str, sheet_id: str, max_rows: int = 10) -> Dict[str, Any]:
        """Preview data from a Google Sheet (first few rows)"""
        try:
            # Use Google Sheets API directly instead of gspread
            credentials = Credentials(access_token)
            service = build('sheets', 'v4', credentials=credentials)
            
            # Get sheet metadata first
            sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            sheet_name = sheet_metadata['sheets'][0]['properties']['title']
            
            # Get the first few rows
            range_name = f"{sheet_name}!A1:Z{max_rows}"
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return {"headers": [], "rows": [], "sheet_name": sheet_name}
            
            # First row is headers
            headers = values[0] if values else []
            rows = values[1:max_rows] if len(values) > 1 else []
            
            # Convert rows to dictionaries
            data_rows = []
            for row in rows:
                row_dict = {}
                for i, header in enumerate(headers):
                    row_dict[header] = row[i] if i < len(row) else ""
                data_rows.append(row_dict)
            
            logger.info(f"Previewed {len(data_rows)} rows from sheet {sheet_name}")
            return {
                "headers": headers,
                "rows": data_rows,
                "sheet_name": sheet_name,
                "total_rows": len(values) - 1  # Exclude header
            }
        except HttpError as error:
            logger.error(f"An error occurred previewing sheet: {error}")
            return {"headers": [], "rows": [], "sheet_name": "", "total_rows": 0}
        except Exception as e:
            logger.error(f"An unexpected error occurred previewing sheet: {e}")
            return {"headers": [], "rows": [], "sheet_name": "", "total_rows": 0}

    def get_sheet_data(self, access_token: str, sheet_id: str) -> List[Dict[str, Any]]:
        """Get all data from a Google Sheet"""
        try:
            # Use Google Sheets API directly instead of gspread
            credentials = Credentials(access_token)
            service = build('sheets', 'v4', credentials=credentials)
            
            # Get sheet metadata first
            sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            sheet_name = sheet_metadata['sheets'][0]['properties']['title']
            
            # Get all data
            range_name = f"{sheet_name}!A1:Z"
            result = service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return []
            
            # First row is headers
            headers = values[0] if values else []
            rows = values[1:] if len(values) > 1 else []
            
            # Convert rows to dictionaries
            data_rows = []
            for row in rows:
                row_dict = {}
                for i, header in enumerate(headers):
                    row_dict[header] = row[i] if i < len(row) else ""
                data_rows.append(row_dict)
            
            logger.info(f"Retrieved {len(data_rows)} rows from sheet {sheet_name}")
            return data_rows
        except HttpError as error:
            logger.error(f"An error occurred getting sheet data: {error}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred getting sheet data: {e}")
            return []
