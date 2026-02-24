# AI SDR - Automated Sales Development Representative

A complete, production-ready CrewAI-powered AI SDR multi-agent workflow for automating B2B outbound prospecting, personalized outreach, reply tracking, and meeting booking.

## Features

- **Multi-Agent Workflow**: Prospecting, Personalization, Outreach, and Coordinator agents
- **Modern Web Interface**: Next.js frontend with authentication and dashboard
- **API-First Backend**: FastAPI with comprehensive endpoints
- **Integrations**: LinkedIn, Email (SMTP/IMAP), Google Sheets
- **Campaign Management**: Create, execute, and track outreach campaigns
- **Lead Management**: Upload, edit, and manage prospect data
- **Real-time Analytics**: Track campaign performance and metrics
- ** Phase 3: Adaptive AI**: Intelligent adaptation based on knowledge levels and market conditions
- ** Market Intelligence**: Real-time market data integration with Grok AI
- ** Knowledge Fusion**: Multi-source knowledge integration with conflict resolution
- ** Smart Model Selection**: Optimal LLM selection based on task requirements
- ** Predictive Analytics**: Campaign performance prediction and optimization

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL (optional, SQLite works for demo)
- Redis (for background tasks)

### Backend Setup

1. **Install Python dependencies**:
```bash
cd ai-sdr
pip install -r requirements.txt
```

2. **Configure environment variables**:
```bash
cp env.example .env
# Edit .env with your API keys and credentials
```

3. **Start the backend**:
```bash
cd backend
python main.py
```

### Frontend Setup

1. **Install Node.js dependencies**:
```bash
cd frontend
npm install
```

2. **Configure environment variables**:
```bash
cp env.local.example .env.local
# Edit .env.local with your configuration
```

3. **Start the frontend**:
```bash
npm run dev
```

### Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Configuration

### Required API Keys

1. **OpenAI API Key** (for CrewAI):
   - Get from: https://platform.openai.com/api-keys
   - Set in `.env`: `OPENAI_API_KEY=your_key_here`

2. **Email Configuration**:
   - SMTP settings for sending emails
   - IMAP settings for tracking replies
   - Set in `.env`: `SMTP_USERNAME`, `SMTP_PASSWORD`, etc.

3. **LinkedIn API** (optional):
   - LinkedIn Developer App credentials
   - Set in `.env`: `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`

4. **Google Sheets API** (optional):
   - Service account credentials
   - Set in `.env`: `GOOGLE_SHEETS_CREDENTIALS_FILE`

### Demo Credentials

For testing, use these demo credentials:
- Email: demo@example.com
- Password: password

## Usage

### 1. Create a Campaign

1. Sign in to the web interface
2. Click "Create Campaign"
3. Fill in campaign details:
   - Name and description
   - Target audience
   - Value proposition
   - Call to action

### 2. Add Leads

**Option A: Upload CSV/Excel file**
1. Go to campaign detail page
2. Click "Upload Leads"
3. Upload file with columns: name, company, title (required)
4. Optional columns: email, linkedin_url, phone, industry, company_size, location

**Option B: Add individual leads**
1. Click "Add Lead"
2. Fill in lead information
3. Save

### 3. Execute Campaign

1. Click "Execute" on campaign card
2. Monitor progress in real-time
3. View results and analytics

### 4. Track Results

- View campaign statistics
- Monitor outreach logs
- Track responses and meetings
- Export data to CSV/Excel

## API Endpoints

### Campaigns
- `GET /campaigns` - List campaigns
- `POST /campaigns` - Create campaign
- `GET /campaigns/{id}` - Get campaign details
- `PUT /campaigns/{id}` - Update campaign
- `DELETE /campaigns/{id}` - Delete campaign
- `POST /campaigns/{id}/execute` - Execute campaign

### Leads
- `GET /campaigns/{id}/leads` - List campaign leads
- `POST /campaigns/{id}/leads` - Add lead
- `POST /campaigns/{id}/leads/upload` - Upload leads file

### Analytics
- `GET /campaigns/{id}/stats` - Campaign statistics
- `GET /campaigns/{id}/outreach-logs` - Outreach activity logs

## Architecture

### Backend Components

1. **CrewAI Agents** (`agents/workflow.py`):
   - Prospecting Agent: Validates and processes lead data
   - Personalization Agent: Generates contextual messages
   - Outreach Agent: Sends messages and tracks responses
   - Coordinator Agent: Orchestrates the workflow

2. **API Layer** (`backend/main.py`):
   - FastAPI application with comprehensive endpoints
   - Authentication and authorization
   - Background task processing with Celery

3. **Integrations** (`integrations/`):
   - Email service (SMTP/IMAP)
   - LinkedIn API integration
   - Google Sheets API integration

### Frontend Components

1. **Authentication**: NextAuth.js with credential provider
2. **Dashboard**: Campaign overview and management
3. **Campaign Detail**: Lead management and analytics
4. **File Upload**: CSV/Excel lead import
5. **Real-time Updates**: Campaign status monitoring

## Development

### Running Tests

```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests
cd frontend
npm test
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

### Background Tasks

```bash
# Start Celery worker
celery -A backend.main.celery_app worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A backend.main.celery_app beat --loglevel=info
```

## Phase 3: Adaptive AI & Market Intelligence

Phase 3 introduces advanced adaptive AI capabilities that enable the system to intelligently adapt its behavior based on available knowledge sources, market conditions, and user context.

### Key Phase 3 Features

- ** Adaptive AI Agent**: Automatically assesses knowledge levels and selects optimal strategies
- ** Knowledge Fusion**: Combines knowledge from documents, prompts, and market data
- ** LLM Selector**: Intelligently selects optimal models based on task requirements
- ** Market Intelligence**: Real-time market data integration with Grok AI
- ** Predictive Analytics**: Campaign performance prediction and optimization
- ** Market Monitoring**: Continuous tracking of market conditions and opportunities

### Phase 3 Configuration

Add these environment variables for Phase 3 features:

```bash
# Grok API Configuration
GROK_API_KEY=your_grok_api_key_here
GROK_API_URL=https://api.x.ai/v1

# LLM Model Selection
DEFAULT_EXTRACTION_MODEL=claude-haiku
ADVANCED_REASONING_MODEL=claude-sonnet
PERSONALIZATION_MODEL=gpt-4
QUICK_TASK_MODEL=gpt-3.5-turbo
MARKET_ANALYSIS_MODEL=grok

# Knowledge Quality Thresholds
QUALITY_EXCELLENT_THRESHOLD=0.9
QUALITY_GOOD_THRESHOLD=0.7
QUALITY_ACCEPTABLE_THRESHOLD=0.5
QUALITY_POOR_THRESHOLD=0.3
```

### Phase 3 Testing

Run the comprehensive Phase 3 test suite:

```bash
python test_phase3_comprehensive.py
```

### Phase 3 Documentation

For detailed Phase 3 documentation, see [PHASE3_DOCUMENTATION.md](PHASE3_DOCUMENTATION.md).

## Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Production Considerations

1. **Environment Variables**: Set all required API keys
2. **Database**: Use PostgreSQL for production
3. **Redis**: Configure Redis for background tasks
4. **Security**: Implement proper JWT validation
5. **Monitoring**: Add logging and monitoring
6. **Rate Limiting**: Implement API rate limiting

## Troubleshooting

### Common Issues

1. **OpenAI API Key**: Ensure valid API key is set
2. **Email Authentication**: Check SMTP/IMAP credentials
3. **Database Connection**: Verify database URL and credentials
4. **Redis Connection**: Ensure Redis is running and accessible

### Logs

- Backend logs: Check console output or log files
- Frontend logs: Check browser console
- Celery logs: Check worker output

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API documentation at `/docs`
