# YouTube Spam Detection Tool

An AI-powered tool to detect and remove spam comments from YouTube videos using Gemini AI, built with Flask backend and Next.js frontend.

## 🚀 Quick Start

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd judolslayer
   ```

2. **Set up the backend** (see [Backend Setup](#backend-setup))
3. **Set up the frontend** (see [Frontend Setup](#frontend-setup))
4. **Configure API keys** in environment files
5. **Start both servers** and visit `http://localhost:3000`

## Features

- 🤖 **AI-Powered Detection**: Uses Google's Gemini AI (gemini-2.0-flash) for intelligent spam detection
- 🎯 **Advanced Filtering**: Detects gambling, scam, promotional, and other types of spam
- 🔍 **Dry Run Mode**: Preview what would be deleted before taking action
- 📊 **Detailed Analytics**: View comprehensive statistics and analysis
- 🚀 **Modern UI**: Beautiful, responsive interface built with Next.js and Tailwind CSS
- 🔄 **Batch Processing**: Process multiple videos at once
- 📤 **Export Results**: Download analysis results as JSON or CSV
- ⚡ **Real-time Processing**: Live updates during processing

## Architecture

### Backend (Flask + LangGraph)
- **Flask**: RESTful API server
- **LangGraph**: Workflow orchestration for complex spam detection logic
- **Gemini AI**: Advanced language model for spam classification
- **YouTube Data API**: Fetch and manage comments
- **TensorFlow/PyTorch**: Additional ML capabilities (extensible)

### Frontend (Next.js)
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **React Query**: Data fetching and caching
- **React Hook Form**: Form management with validation
- **Heroicons**: Beautiful icons

## Prerequisites

- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **YouTube Data API v3 key** from [Google Cloud Console](https://console.cloud.google.com/)
- **Google AI (Gemini) API key** from [Google AI Studio](https://makersuite.google.com/)
- **Git** for version control

### Getting API Keys

1. **YouTube Data API v3**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable YouTube Data API v3
   - Create credentials (API key)
   - Restrict the key to YouTube Data API v3 for security

2. **Google AI (Gemini) API**:
   - Visit [Google AI Studio](https://makersuite.google.com/)
   - Sign in with your Google account
   - Create a new API key
   - Copy the key for use in your environment file

## Installation

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create environment file:
```bash
cp .env.example .env
```

5. Configure your `.env` file:
```env
# API Keys (Required)
YOUTUBE_API_KEY=your_youtube_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=generated_secure_secret_key_here

# CORS Settings
CORS_ORIGINS=http://localhost:3000

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO
```

**Important**: 
- Replace `your_youtube_api_key_here` with your actual YouTube Data API v3 key
- Replace `your_gemini_api_key_here` with your actual Google AI (Gemini) API key
- The SECRET_KEY has been automatically generated for security
- Never commit your `.env` file to version control

6. Run the Flask application:
```bash
python app.py
```

The backend will be available at `http://localhost:5000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create environment file:
```bash
cp .env.local.example .env.local
```

4. Configure your `.env.local` file:
```env
NEXT_PUBLIC_API_URL=http://localhost:5000
```

5. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## API Endpoints

### Backend API

- `GET /api/health` - Health check
- `POST /api/process-video` - Process video for spam detection
- `POST /api/analyze-comment` - Analyze a single comment
- `POST /api/video-info` - Get video information
- `POST /api/batch-process` - Process multiple videos

**Note**: All API keys are now configured via environment variables for enhanced security. No need to include them in API requests.

### Request Examples

#### Process Video for Spam Detection
```bash
curl -X POST http://localhost:5000/api/process-video \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "dQw4w9WgXcQ",
    "max_results": 100,
    "dry_run": true
  }'
```

#### Analyze Single Comment
```bash
curl -X POST http://localhost:5000/api/analyze-comment \
  -H "Content-Type: application/json" \
  -d '{
    "comment_text": "Check out my crypto trading bot!"
  }'
```

## Usage

1. **Start the Application**:
   - Ensure both backend and frontend servers are running
   - Open `http://localhost:3000` in your browser

2. **Enter Video Information**:
   - Paste YouTube video ID or full URL
   - Configure detection settings (API keys are automatically loaded from environment)
   - Adjust advanced options if needed

3. **Run Analysis**:
   - **Recommended**: Use "Dry Run" first to preview results without making changes
   - Review the analysis and statistics
   - If satisfied, disable "Dry Run" and click "Remove Spam" to delete detected spam comments

4. **Review Results**:
   - View detailed statistics and confidence scores
   - Filter comments by type (All, Spam, Clean)
   - Sort by confidence, date, or risk level
   - Export results for further analysis

### ⚠️ Important Notes

- **Always test with Dry Run first** to avoid accidentally deleting legitimate comments
- **Spam removal is permanent** - deleted comments cannot be recovered
- **Rate limits apply** - YouTube API has daily quotas
- **Review results carefully** - AI detection may have false positives

## Configuration

### Spam Detection Settings

- **Confidence Threshold**: Minimum confidence level for spam classification (0.0-1.0)
- **Risk Levels**: High, Medium, Low risk categorization
- **Spam Types**: Gambling, Scam, Promotional, Offensive, etc.
- **Dry Run**: Preview mode without actual deletion

### Advanced Options

- **Max Comments**: Limit number of comments to process
- **Include Replies**: Process comment replies
- **Custom Patterns**: Add custom spam detection patterns
- **Batch Processing**: Process multiple videos simultaneously

## Development

### Backend Development

```bash
# Run with auto-reload
python app.py

# Run tests (if test files exist)
python -m pytest tests/

# Format code (install tools first: pip install black flake8)
black .
flake8 .
```

### Frontend Development

```bash
# Development server
npm run dev

# Build for production
npm run build

# Run production server
npm start

# Lint code
npm run lint

# Type check
npm run type-check
```

## Deployment

### Backend (Flask)

1. **Using Gunicorn**:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. **Using Docker**:
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Frontend (Next.js)

1. **Static Export**:
```bash
npm run build
npm run export
```

2. **Vercel Deployment**:
```bash
npm install -g vercel
vercel
```

## Security Considerations

- **API Keys**: 
  - All API keys are managed via environment variables
  - Never commit `.env` files to version control
  - Use `.env.example` as a template for required variables
  - `credentials.json` is automatically ignored by Git
- **Secret Key**: Generate a secure Flask secret key for production
- **Rate Limiting**: Implement proper rate limiting for production
- **CORS**: Configure CORS properly for your domain
- **Input Validation**: All inputs are validated and sanitized
- **Error Handling**: Comprehensive error handling and logging
- **Git Security**: 
  - Comprehensive `.gitignore` file protects sensitive data
  - OAuth credentials and API keys are excluded from version control
  - If you accidentally committed sensitive files, remove them from Git history

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the API examples

## Troubleshooting

### Common Issues

1. **"API key not found" error**:
   - Ensure `.env` file exists in backend directory
   - Check that API keys are properly set in environment variables
   - Restart the backend server after changing environment variables

2. **"Video not found" error**:
   - Verify the YouTube video ID or URL is correct
   - Ensure the video is public and comments are enabled
   - Check if the video exists and is accessible

3. **CORS errors**:
   - Ensure backend is running on port 5000
   - Check CORS_ORIGINS setting in backend `.env`
   - Verify frontend is accessing the correct backend URL

4. **Rate limit exceeded**:
   - YouTube API has daily quotas
   - Wait for quota reset or request quota increase
   - Reduce the number of comments processed per request

### Getting Help

- Check the browser console for error messages
- Review backend logs for detailed error information
- Ensure all dependencies are installed correctly
- Verify API keys have proper permissions

## Acknowledgments

- Google AI for Gemini API
- YouTube Data API
- LangGraph for workflow orchestration
- Next.js and React communities
- Tailwind CSS for styling
- Open source community for tools and libraries