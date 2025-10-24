# AI SDR - Quick Start Guide

## Prerequisites

- Python 3.8+
- Node.js 16+
- Redis (for background tasks)
- OpenAI API key

## Installation

### Option 1: Automated Setup (Recommended)

```bash
# Clone or download the project
cd ai-sdr

# Run the setup script
./setup.sh
```

### Option 2: Manual Setup

1. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

2. **Install Node.js dependencies**:
```bash
cd frontend
npm install
cd ..
```

3. **Configure environment**:
```bash
cp env.example .env
cp frontend/env.local.example frontend/.env.local
```

4. **Edit configuration files**:
   - `.env` - Add your API keys
   - `frontend/.env.local` - Frontend configuration

## Configuration

### Required API Keys

1. **OpenAI API Key** (Required):
   ```bash
   OPENAI_API_KEY=sk-your-openai-key-here
   ```

2. **Email Configuration** (Optional):
   ```bash
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   ```

3. **LinkedIn API** (Optional):
   ```bash
   LINKEDIN_CLIENT_ID=your-linkedin-client-id
   LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret
   ```

4. **Google Sheets API** (Optional):
   ```bash
   GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
   ```

## Running the Application

### Start Backend
```bash
python backend/main.py
```

### Start Frontend (in new terminal)
```bash
cd frontend
npm run dev
```

### Start Background Tasks (optional)
```bash
# Start Celery worker
celery -A backend.main.celery_app worker --loglevel=info

# Start Celery beat (for scheduled tasks)
celery -A backend.main.celery_app beat --loglevel=info
```

## Access Points

- **Web Application**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Endpoint**: http://localhost:8000

## Demo Credentials

- **Email**: demo@example.com
- **Password**: password

## First Steps

1. **Sign in** with demo credentials
2. **Create a campaign**:
   - Click "Create Campaign"
   - Fill in campaign details
   - Save

3. **Add leads**:
   - Go to campaign detail page
   - Upload CSV file or add individual leads
   - Required columns: name, company, title

4. **Execute campaign**:
   - Click "Execute" button
   - Monitor progress
   - View results and analytics

## Sample Lead Data

Create a CSV file with these columns:

```csv
name,company,title,email,linkedin_url,industry,company_size,location
John Smith,TechCorp Inc,VP of Engineering,john@techcorp.com,https://linkedin.com/in/johnsmith,Technology,100-500,San Francisco CA
Sarah Johnson,DataFlow Systems,CTO,sarah@dataflow.com,https://linkedin.com/in/sarahjohnson,Data Analytics,50-100,Austin TX
```

## Troubleshooting

### Common Issues

1. **"OpenAI API Key not found"**:
   - Ensure `OPENAI_API_KEY` is set in `.env`
   - Verify the key is valid and has credits

2. **"Redis connection failed"**:
   - Install and start Redis: `brew install redis && brew services start redis`
   - Or use Docker: `docker run -d -p 6379:6379 redis:alpine`

3. **"Database connection failed"**:
   - The app uses SQLite by default (no setup required)
   - For PostgreSQL, update `DATABASE_URL` in `.env`

4. **Frontend not loading**:
   - Check if backend is running on port 8000
   - Verify `NEXT_PUBLIC_API_URL` in `frontend/.env.local`

### Getting Help

1. Check the logs in the terminal
2. Review the API documentation at `/docs`
3. Check browser console for frontend errors
4. Ensure all required environment variables are set

## Production Deployment

For production deployment:

1. **Use PostgreSQL** instead of SQLite
2. **Set up Redis** for background tasks
3. **Configure proper authentication**
4. **Set up monitoring and logging**
5. **Use Docker** for containerized deployment

See `docker-compose.yml` for containerized setup.

## API Usage

The API is fully documented at http://localhost:8000/docs when running.

Key endpoints:
- `POST /campaigns` - Create campaign
- `POST /campaigns/{id}/leads/upload` - Upload leads
- `POST /campaigns/{id}/execute` - Execute campaign
- `GET /campaigns/{id}/stats` - Get statistics

## Support

For issues and questions:
1. Check this guide
2. Review the README.md
3. Check the API documentation
4. Create an issue in the repository
