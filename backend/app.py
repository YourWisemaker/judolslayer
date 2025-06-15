from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv
import logging
import time
from typing import List, Dict, Any
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini AI
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.0-flash-exp')

class YouTubeSpamDetector:
    def __init__(self, youtube_api_key: str, gemini_api_key: str):
        self.youtube = build('youtube', 'v3', developerKey=youtube_api_key)
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
    def get_video_comments(self, video_id: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """Fetch comments from a YouTube video"""
        try:
            comments = []
            request = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=min(max_results, 100),
                order='time'
            )
            
            while request and len(comments) < max_results:
                response = request.execute()
                
                for item in response['items']:
                    comment = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'id': item['id'],
                        'text': comment['textDisplay'],
                        'author': comment['authorDisplayName'],
                        'published_at': comment['publishedAt'],
                        'like_count': comment['likeCount']
                    })
                
                request = self.youtube.commentThreads().list_next(request, response)
                
            return comments[:max_results]
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            raise
    
    def detect_spam_with_ai(self, comment_text: str) -> Dict[str, Any]:
        """Use Gemini AI to detect spam in comments"""
        prompt = f"""
Analyze this YouTube comment and determine if it's spam related to online gambling/betting (judol/judi online).

Comment: "{comment_text}"

Look for:
1. Online gambling/betting keywords (judi, slot, casino, gacor, maxwin, etc.)
2. Promotional language for gambling sites
3. Links or references to betting platforms
4. Patterns like WORD+NUMBERS (e.g., GACOR77, ZEUS123)
5. Phrases like "bonus deposit", "daftar sekarang", "link alternatif"
6. Suspicious promotional content

Respond with a JSON object:
{{
  "is_spam": true/false,
  "confidence": 0.0-1.0,
  "reason": "explanation of why it's spam or not",
  "detected_patterns": ["list of spam patterns found"]
}}

Be strict - only mark as spam if you're confident it's gambling-related spam.
"""
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            return result
        except Exception as e:
            logger.error(f"AI detection error: {e}")
            return {
                "is_spam": False,
                "confidence": 0.0,
                "reason": f"Error in AI detection: {str(e)}",
                "detected_patterns": []
            }
    
    def delete_comment(self, comment_id: str) -> bool:
        """Delete a comment from YouTube"""
        try:
            self.youtube.comments().delete(id=comment_id).execute()
            return True
        except HttpError as e:
            logger.error(f"Failed to delete comment {comment_id}: {e}")
            return False
    
    def process_video_comments(self, video_id: str, max_results: int = 100, dry_run: bool = True) -> Dict[str, Any]:
        """Process all comments in a video for spam detection"""
        try:
            comments = self.get_video_comments(video_id, max_results)
            spam_comments = []
            processed_count = 0
            deleted_count = 0
            
            for comment in comments:
                processed_count += 1
                detection_result = self.detect_spam_with_ai(comment['text'])
                
                if detection_result['is_spam'] and detection_result['confidence'] > 0.7:
                    spam_info = {
                        'comment_id': comment['id'],
                        'text': comment['text'],
                        'author': comment['author'],
                        'confidence': detection_result['confidence'],
                        'reason': detection_result['reason'],
                        'patterns': detection_result['detected_patterns'],
                        'deleted': False
                    }
                    
                    if not dry_run:
                        if self.delete_comment(comment['id']):
                            spam_info['deleted'] = True
                            deleted_count += 1
                            time.sleep(1)  # Rate limiting
                    
                    spam_comments.append(spam_info)
            
            return {
                'success': True,
                'video_id': video_id,
                'processed_comments': processed_count,
                'spam_detected': len(spam_comments),
                'deleted_count': deleted_count,
                'dry_run': dry_run,
                'spam_comments': spam_comments
            }
            
        except Exception as e:
            logger.error(f"Error processing video comments: {e}")
            return {
                'success': False,
                'error': str(e)
            }

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'YouTube Spam Detector'})

@app.route('/api/detect-spam', methods=['POST'])
def detect_spam():
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
        
        # Optional parameters
        max_results = data.get('max_results', 50)
        dry_run = data.get('dry_run', True)
        
        # Initialize detector
        detector = YouTubeSpamDetector(
            youtube_api_key=youtube_api_key,
            gemini_api_key=gemini_api_key
        )
        
        # Process comments
        result = detector.process_video_comments(
            video_id=data['video_id'],
            max_results=max_results,
            dry_run=dry_run
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-comment', methods=['POST'])
def analyze_comment():
    """Analyze a single comment for spam detection"""
    try:
        data = request.get_json()
        
        if 'comment_text' not in data:
            return jsonify({'error': 'Missing comment_text'}), 400
        
        # Get Gemini API key from environment variables
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        if not gemini_api_key:
            return jsonify({'error': 'Gemini API key not configured on server'}), 500
        
        detector = YouTubeSpamDetector(
            youtube_api_key='dummy',  # Not needed for single comment analysis
            gemini_api_key=gemini_api_key
        )
        
        result = detector.detect_spam_with_ai(data['comment_text'])
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Comment analysis error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)