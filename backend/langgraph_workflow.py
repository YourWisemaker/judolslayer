from langgraph.graph import Graph, StateGraph, END
from typing import TypedDict, List, Dict, Any
import google.generativeai as genai
from googleapiclient.discovery import build
import logging
import time
import json

logger = logging.getLogger(__name__)

class SpamDetectionState(TypedDict):
    video_id: str
    youtube_api_key: str
    gemini_api_key: str
    max_results: int
    dry_run: bool
    comments: List[Dict[str, Any]]
    analyzed_comments: List[Dict[str, Any]]
    spam_comments: List[Dict[str, Any]]
    deleted_comments: List[str]
    errors: List[str]
    processing_stats: Dict[str, Any]

class SpamDetectionWorkflow:
    def __init__(self):
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for spam detection"""
        workflow = StateGraph(SpamDetectionState)
        
        # Add nodes
        workflow.add_node("fetch_comments", self.fetch_comments)
        workflow.add_node("analyze_comments", self.analyze_comments)
        workflow.add_node("filter_spam", self.filter_spam)
        workflow.add_node("delete_spam", self.delete_spam)
        workflow.add_node("generate_report", self.generate_report)
        
        # Add edges
        workflow.add_edge("fetch_comments", "analyze_comments")
        workflow.add_edge("analyze_comments", "filter_spam")
        workflow.add_edge("filter_spam", "delete_spam")
        workflow.add_edge("delete_spam", "generate_report")
        workflow.add_edge("generate_report", END)
        
        # Set entry point
        workflow.set_entry_point("fetch_comments")
        
        return workflow.compile()
    
    def fetch_comments(self, state: SpamDetectionState) -> SpamDetectionState:
        """Fetch comments from YouTube video"""
        try:
            youtube = build('youtube', 'v3', developerKey=state['youtube_api_key'])
            comments = []
            
            request = youtube.commentThreads().list(
                part='snippet',
                videoId=state['video_id'],
                maxResults=min(state['max_results'], 100),
                order='time'
            )
            
            while request and len(comments) < state['max_results']:
                response = request.execute()
                
                for item in response['items']:
                    comment = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'id': item['id'],
                        'text': comment['textDisplay'],
                        'author': comment['authorDisplayName'],
                        'published_at': comment['publishedAt'],
                        'like_count': comment['likeCount'],
                        'channel_id': comment.get('authorChannelId', {}).get('value', '')
                    })
                
                request = youtube.commentThreads().list_next(request, response)
            
            state['comments'] = comments[:state['max_results']]
            logger.info(f"Fetched {len(state['comments'])} comments")
            
        except Exception as e:
            error_msg = f"Error fetching comments: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
            state['comments'] = []
        
        return state
    
    def analyze_comments(self, state: SpamDetectionState) -> SpamDetectionState:
        """Analyze comments using Gemini AI"""
        try:
            genai.configure(api_key=state['gemini_api_key'])
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            
            analyzed_comments = []
            
            for comment in state['comments']:
                try:
                    # Enhanced prompt for better spam detection
                    prompt = f"""
Analyze this YouTube comment for online gambling/betting spam (judol/judi online).

Comment: "{comment['text']}"
Author: {comment['author']}
Likes: {comment['like_count']}

Detection criteria:
1. Gambling keywords: judi, slot, casino, gacor, maxwin, zeus, pragmatic, gates of olympus
2. Promotional patterns: bonus, deposit, daftar, link alternatif, situs terpercaya
3. Suspicious formats: WORD+NUMBERS (GACOR77, ZEUS123)
4. Call-to-action phrases: "klik link", "daftar sekarang", "bonus new member"
5. Emoji patterns commonly used in spam
6. Repetitive or template-like content

Consider context:
- Comment relevance to video content
- Author's comment history pattern
- Engagement metrics

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
                    
                    analyzed_comment = {
                        **comment,
                        'analysis': analysis,
                        'analyzed_at': time.time()
                    }
                    
                    analyzed_comments.append(analyzed_comment)
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Error analyzing comment {comment['id']}: {e}")
                    analyzed_comment = {
                        **comment,
                        'analysis': {
                            'is_spam': False,
                            'confidence': 0.0,
                            'spam_type': 'error',
                            'reason': f"Analysis failed: {str(e)}",
                            'detected_patterns': [],
                            'risk_level': 'low',
                            'recommended_action': 'ignore'
                        },
                        'analyzed_at': time.time()
                    }
                    analyzed_comments.append(analyzed_comment)
            
            state['analyzed_comments'] = analyzed_comments
            logger.info(f"Analyzed {len(analyzed_comments)} comments")
            
        except Exception as e:
            error_msg = f"Error in comment analysis: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
            state['analyzed_comments'] = []
        
        return state
    
    def filter_spam(self, state: SpamDetectionState) -> SpamDetectionState:
        """Filter and categorize spam comments"""
        try:
            spam_comments = []
            
            for comment in state['analyzed_comments']:
                analysis = comment['analysis']
                
                # Filter based on confidence and risk level
                if (analysis['is_spam'] and 
                    analysis['confidence'] > 0.7 and 
                    analysis['risk_level'] in ['high', 'critical']):
                    
                    spam_comments.append({
                        **comment,
                        'spam_category': analysis['spam_type'],
                        'priority': self._calculate_priority(analysis),
                        'action_recommended': analysis['recommended_action']
                    })
            
            # Sort by priority (highest first)
            spam_comments.sort(key=lambda x: x['priority'], reverse=True)
            
            state['spam_comments'] = spam_comments
            logger.info(f"Identified {len(spam_comments)} spam comments")
            
        except Exception as e:
            error_msg = f"Error filtering spam: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
            state['spam_comments'] = []
        
        return state
    
    def delete_spam(self, state: SpamDetectionState) -> SpamDetectionState:
        """Delete spam comments if not in dry run mode"""
        deleted_comments = []
        
        if state['dry_run']:
            logger.info("Dry run mode - no comments will be deleted")
            state['deleted_comments'] = []
            return state
        
        try:
            youtube = build('youtube', 'v3', developerKey=state['youtube_api_key'])
            
            for comment in state['spam_comments']:
                try:
                    # Only delete high-confidence spam
                    if (comment['analysis']['confidence'] > 0.8 and 
                        comment['analysis']['risk_level'] == 'critical'):
                        
                        youtube.comments().delete(id=comment['id']).execute()
                        deleted_comments.append(comment['id'])
                        logger.info(f"Deleted spam comment: {comment['id']}")
                        
                        # Rate limiting
                        time.sleep(1)
                        
                except Exception as e:
                    error_msg = f"Failed to delete comment {comment['id']}: {str(e)}"
                    logger.error(error_msg)
                    state['errors'].append(error_msg)
            
            state['deleted_comments'] = deleted_comments
            logger.info(f"Deleted {len(deleted_comments)} spam comments")
            
        except Exception as e:
            error_msg = f"Error in deletion process: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
            state['deleted_comments'] = []
        
        return state
    
    def generate_report(self, state: SpamDetectionState) -> SpamDetectionState:
        """Generate processing report"""
        try:
            total_comments = len(state['comments'])
            analyzed_comments = len(state['analyzed_comments'])
            spam_detected = len(state['spam_comments'])
            deleted_count = len(state['deleted_comments'])
            
            # Calculate statistics
            spam_rate = (spam_detected / total_comments * 100) if total_comments > 0 else 0
            deletion_rate = (deleted_count / spam_detected * 100) if spam_detected > 0 else 0
            
            # Categorize spam types
            spam_categories = {}
            risk_levels = {}
            
            for comment in state['spam_comments']:
                spam_type = comment['analysis']['spam_type']
                risk_level = comment['analysis']['risk_level']
                
                spam_categories[spam_type] = spam_categories.get(spam_type, 0) + 1
                risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
            
            state['processing_stats'] = {
                'total_comments': total_comments,
                'analyzed_comments': analyzed_comments,
                'spam_detected': spam_detected,
                'deleted_count': deleted_count,
                'spam_rate_percent': round(spam_rate, 2),
                'deletion_rate_percent': round(deletion_rate, 2),
                'spam_categories': spam_categories,
                'risk_levels': risk_levels,
                'errors_count': len(state['errors']),
                'processing_time': time.time()
            }
            
            logger.info(f"Processing complete: {spam_detected} spam detected, {deleted_count} deleted")
            
        except Exception as e:
            error_msg = f"Error generating report: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
        
        return state
    
    def _calculate_priority(self, analysis: Dict[str, Any]) -> int:
        """Calculate priority score for spam comments"""
        priority = 0
        
        # Base priority from confidence
        priority += int(analysis['confidence'] * 100)
        
        # Risk level multiplier
        risk_multipliers = {
            'critical': 50,
            'high': 30,
            'medium': 10,
            'low': 0
        }
        priority += risk_multipliers.get(analysis['risk_level'], 0)
        
        # Spam type bonus
        type_bonus = {
            'gambling': 40,
            'promotional': 20,
            'suspicious': 10
        }
        priority += type_bonus.get(analysis['spam_type'], 0)
        
        return priority
    
    def run(self, initial_state: SpamDetectionState) -> SpamDetectionState:
        """Run the complete spam detection workflow"""
        # Initialize state with default values
        initial_state.setdefault('comments', [])
        initial_state.setdefault('analyzed_comments', [])
        initial_state.setdefault('spam_comments', [])
        initial_state.setdefault('deleted_comments', [])
        initial_state.setdefault('errors', [])
        initial_state.setdefault('processing_stats', {})
        
        try:
            result = self.workflow.invoke(initial_state)
            return result
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            initial_state['errors'].append(f"Workflow error: {str(e)}")
            return initial_state