from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import logging
from langgraph_workflow import SpamDetectionWorkflow, SpamDetectionState
from typing import Dict, Any
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize workflow
workflow = SpamDetectionWorkflow()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'YouTube Spam Detector with LangGraph',
        'version': '2.0.0',
        'timestamp': time.time()
    })

@app.route('/api/process-video', methods=['POST'])
def process_video():
    """Process a YouTube video for spam detection using LangGraph workflow"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['video_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get API keys from environment variables
        youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        if not youtube_api_key:
            return jsonify({'error': 'YouTube API key not configured on server'}), 500
        if not gemini_api_key:
            return jsonify({'error': 'Gemini API key not configured on server'}), 500
        
        # Validate video_id format
        video_id = data['video_id']
        if len(video_id) != 11:  # YouTube video IDs are 11 characters
            return jsonify({'error': 'Invalid video_id format'}), 400
        
        # Optional parameters with defaults
        max_results = min(data.get('max_results', 50), 200)  # Cap at 200
        dry_run = data.get('dry_run', True)
        
        # Create initial state
        initial_state: SpamDetectionState = {
            'video_id': video_id,
            'youtube_api_key': youtube_api_key,
            'gemini_api_key': gemini_api_key,
            'max_results': max_results,
            'dry_run': dry_run,
            'comments': [],
            'analyzed_comments': [],
            'spam_comments': [],
            'deleted_comments': [],
            'errors': [],
            'processing_stats': {}
        }
        
        logger.info(f"Starting spam detection for video: {video_id}")
        start_time = time.time()
        
        # Run the workflow
        result = workflow.run(initial_state)
        
        processing_time = time.time() - start_time
        result['processing_stats']['total_processing_time'] = round(processing_time, 2)
        
        # Prepare response
        response = {
            'success': True,
            'video_id': video_id,
            'dry_run': dry_run,
            'processing_stats': result['processing_stats'],
            'spam_comments': result['spam_comments'],
            'deleted_comments': result['deleted_comments'],
            'errors': result['errors']
        }
        
        # Add summary for easier consumption
        response['summary'] = {
            'total_comments_processed': result['processing_stats'].get('total_comments', 0),
            'spam_detected': result['processing_stats'].get('spam_detected', 0),
            'comments_deleted': result['processing_stats'].get('deleted_count', 0),
            'spam_rate': f"{result['processing_stats'].get('spam_rate_percent', 0)}%",
            'processing_time': f"{processing_time:.2f} seconds"
        }
        
        logger.info(f"Processing completed for video {video_id}: {response['summary']}")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"API error in process_video: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }), 500

@app.route('/api/analyze-comment', methods=['POST'])
def analyze_single_comment():
    """Analyze a single comment for spam detection"""
    try:
        data = request.get_json()
        
        if 'comment_text' not in data:
            return jsonify({'error': 'Missing comment_text'}), 400
        
        # Get API key from environment
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            return jsonify({'error': 'Gemini API key not configured'}), 500
        
        comment_text = data['comment_text']
        if len(comment_text.strip()) == 0:
            return jsonify({'error': 'Comment text cannot be empty'}), 400
        
        # Create a minimal workflow state for single comment analysis
        from langgraph_workflow import SpamDetectionWorkflow
        import google.generativeai as genai
        import json
        
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = f"""
Analyze this comment for online gambling/betting spam (judol/judi online).

Comment: "{comment_text}"

Detection criteria:
1. Gambling keywords: judi, slot, casino, gacor, maxwin, zeus, pragmatic
2. Promotional patterns: bonus, deposit, daftar, link alternatif
3. Suspicious formats: WORD+NUMBERS (GACOR77, ZEUS123)
4. Call-to-action phrases: "klik link", "daftar sekarang"
5. Emoji patterns commonly used in spam

Respond with JSON:
{{
  "is_spam": boolean,
  "confidence": 0.0-1.0,
  "spam_type": "gambling|promotional|suspicious|clean",
  "reason": "detailed explanation",
  "detected_patterns": ["list of patterns"],
  "risk_level": "low|medium|high|critical",
  "recommended_action": "ignore|review|delete|ban_user"
}}
"""
        
        response = model.generate_content(prompt)
        analysis = json.loads(response.text)
        
        return jsonify({
            'success': True,
            'comment_text': comment_text,
            'analysis': analysis,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Comment analysis error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': time.time()
        }), 500

@app.route('/api/video-info', methods=['POST'])
def get_video_info():
    """Get basic information about a YouTube video"""
    try:
        data = request.get_json()
        
        if 'video_id' not in data:
            return jsonify({'error': 'Missing video_id'}), 400
        
        # Get YouTube API key from environment variables
        youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        
        if not youtube_api_key:
            return jsonify({'error': 'YouTube API key not configured on server'}), 500
        
        from googleapiclient.discovery import build
        
        youtube = build('youtube', 'v3', developerKey=youtube_api_key)
        
        # Get video details
        video_response = youtube.videos().list(
            part='snippet,statistics',
            id=data['video_id']
        ).execute()
        
        if not video_response['items']:
            return jsonify({'error': 'Video not found'}), 404
        
        video = video_response['items'][0]
        snippet = video['snippet']
        statistics = video['statistics']
        
        # Get comment count estimate
        try:
            comments_response = youtube.commentThreads().list(
                part='snippet',
                videoId=data['video_id'],
                maxResults=1
            ).execute()
            
            total_comments = int(statistics.get('commentCount', 0))
        except:
            total_comments = 0
        
        video_info = {
            'video_id': data['video_id'],
            'title': snippet['title'],
            'channel_title': snippet['channelTitle'],
            'published_at': snippet['publishedAt'],
            'view_count': int(statistics.get('viewCount', 0)),
            'like_count': int(statistics.get('likeCount', 0)),
            'comment_count': total_comments,
            'description': snippet.get('description', '')[:500] + '...' if len(snippet.get('description', '')) > 500 else snippet.get('description', ''),
            'thumbnail_url': snippet['thumbnails']['medium']['url']
        }
        
        return jsonify({
            'success': True,
            'video_info': video_info
        })
        
    except Exception as e:
        logger.error(f"Video info error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/batch-process', methods=['POST'])
def batch_process_videos():
    """Process multiple videos in batch"""
    try:
        data = request.get_json()
        
        required_fields = ['video_ids']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Get API keys from environment variables
        youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        if not youtube_api_key:
            return jsonify({'error': 'YouTube API key not configured on server'}), 500
        if not gemini_api_key:
            return jsonify({'error': 'Gemini API key not configured on server'}), 500
        
        video_ids = data['video_ids']
        if not isinstance(video_ids, list) or len(video_ids) == 0:
            return jsonify({'error': 'video_ids must be a non-empty list'}), 400
        
        if len(video_ids) > 10:  # Limit batch size
            return jsonify({'error': 'Maximum 10 videos per batch'}), 400
        
        max_results = min(data.get('max_results', 50), 100)
        dry_run = data.get('dry_run', True)
        
        batch_results = []
        
        for video_id in video_ids:
            try:
                initial_state: SpamDetectionState = {
                    'video_id': video_id,
                    'youtube_api_key': youtube_api_key,
                    'gemini_api_key': gemini_api_key,
                    'max_results': max_results,
                    'dry_run': dry_run,
                    'comments': [],
                    'analyzed_comments': [],
                    'spam_comments': [],
                    'deleted_comments': [],
                    'errors': [],
                    'processing_stats': {}
                }
                
                result = workflow.run(initial_state)
                
                batch_results.append({
                    'video_id': video_id,
                    'success': True,
                    'processing_stats': result['processing_stats'],
                    'spam_count': len(result['spam_comments']),
                    'deleted_count': len(result['deleted_comments']),
                    'errors': result['errors']
                })
                
            except Exception as e:
                batch_results.append({
                    'video_id': video_id,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'batch_results': batch_results,
            'total_videos': len(video_ids),
            'successful_processes': sum(1 for r in batch_results if r['success'])
        })
        
    except Exception as e:
        logger.error(f"Batch process error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)