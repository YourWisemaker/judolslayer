from langgraph.graph import Graph, StateGraph, END
from typing import TypedDict, List, Dict, Any, Optional
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
    oauth_handler: Optional[Any]

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
You are an expert content moderator specializing in detecting online gambling/betting spam in Indonesian comments.

Analyze this comment for gambling/betting spam characteristics:
Comment: "{comment['text']}"

IMPORTANT: Only flag as gambling spam if the comment is clearly promoting or discussing online gambling activities. Regular words like "main" (play), "bagus" (good), "test" should NOT trigger spam detection unless used in clear gambling context.

Consider these criteria:
1. Specific Gambling Keywords: judi, slot casino, gacor, maxwin, zeus slot, pragmatic play, gates of olympus, bonus deposit, putrispin, jackpot, ironslot
2. Gambling Actions: main slot, main judi, pola gacor, wd lancar, cuan besar, modal receh
3. Promotional Language: daftar slot, link alternatif, klik link slot, bonus new member, info slot, promosi slot
4. Gambling Site Names: dora88, sinar88, jpdewa, pintuslot, luxury777, nagaslot, qq77, momo4d
5. Context: The comment must be clearly related to gambling/betting activities, not just containing common words

Examples of NOT spam:
- "test wah bagus" (just testing/commenting)
- "main game ini seru" (playing regular games)
- "bagus banget videonya" (complimenting content)

Examples of spam:
- "main slot di situs gacor"
- "daftar sekarang bonus 100%"
- "pola zeus maxwin"

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
                    response_text = response.text.strip()
                    
                    # Try to extract JSON from response
                    try:
                        # Look for JSON block in response
                        if '```json' in response_text:
                            json_start = response_text.find('```json') + 7
                            json_end = response_text.find('```', json_start)
                            json_text = response_text[json_start:json_end].strip()
                        elif '{' in response_text and '}' in response_text:
                            json_start = response_text.find('{')
                            json_end = response_text.rfind('}') + 1
                            json_text = response_text[json_start:json_end]
                        else:
                            json_text = response_text
                        
                        analysis = json.loads(json_text)
                    except json.JSONDecodeError:
                        # Fallback: create analysis based on keywords
                        text_lower = comment['text'].lower()
                        gambling_keywords = [
                            'judi', 'slot', 'casino', 'gacor', 'maxwin', 'maxxwin', 'zeus', 'pragmatic', 'gates of olympus', 
                            'bonus deposit', 'putrispin', 'jackpot', 'ironslot', 'main slot', 'main judi', 'main di situs', 
                            'pola gacor', 'tempat judi', 'selalu menang', 'wd lancar', 'cuan besar', 'modal receh',
                            'gw jelasin pola', 'gk pernah pakek pola', 'daftar slot', 'link alternatif', 
                            'langsung gas', 'auto cuan', 'jam hoki', 'gacor pol', 'dora88', 'sinar88', 'jpdewa',
                            'pintuslot', 'luxury777', 'nagaslot', 'qq77', 'momo4d', 'situs judi', 'situs slot', 
                            'klik link slot', 'daftar sekarang', 'bonus new member', 'info slot', 
                            'promosi slot', 'akun slot', 'menang terus', 'deposit murah'
                        ]
                        detected_keywords = [kw for kw in gambling_keywords if kw in text_lower]
                        
                        is_spam = len(detected_keywords) > 0
                        confidence = min(len(detected_keywords) * 0.3, 1.0)
                        
                        analysis = {
                            'is_spam': is_spam,
                            'confidence': confidence,
                            'spam_type': 'gambling' if is_spam else 'clean',
                            'reason': f"Keyword-based detection. Found: {detected_keywords}" if is_spam else "No gambling keywords detected",
                            'detected_patterns': detected_keywords,
                            'risk_level': 'high' if confidence > 0.7 else 'medium' if confidence > 0.3 else 'low',
                            'recommended_action': 'delete' if confidence > 0.7 else 'review' if confidence > 0.3 else 'ignore'
                        }
                    
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
            all_comments = []
            spam_count = 0
            high_confidence_spam_count = 0
            
            for comment in state['analyzed_comments']:
                analysis = comment['analysis']
                
                # Add all comments to the list (both spam and clean)
                processed_comment = {
                    **comment,
                    'spam_category': analysis['spam_type'],
                    'priority': self._calculate_priority(analysis),
                    'action_recommended': analysis['recommended_action']
                }
                
                all_comments.append(processed_comment)
                
                # Count spam comments
                if analysis['is_spam']:
                    spam_count += 1
                    # Count high-confidence gambling spam (what will actually be deleted)
                    if (analysis['confidence'] > 0.7 and 
                        analysis['spam_type'] == 'gambling'):
                        high_confidence_spam_count += 1
            
            # Sort by priority (highest first)
            all_comments.sort(key=lambda x: x['priority'], reverse=True)
            
            # Store all comments in spam_comments (this is what frontend expects)
            state['spam_comments'] = all_comments
            logger.info(f"Identified {spam_count} spam comments ({high_confidence_spam_count} high-confidence) out of {len(all_comments)} total")
            
        except Exception as e:
            error_msg = f"Error filtering spam: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
            state['spam_comments'] = []
        
        return state
    
    def delete_spam(self, state: SpamDetectionState) -> SpamDetectionState:
        """Moderate spam comments if not in dry run mode using OAuth authentication"""
        
        if state['dry_run']:
            logger.info("Dry run mode - no comments will be deleted")
            state['deleted_comments'] = []
            return state
        
        # Get OAuth handler from state
        oauth_handler = state.get('oauth_handler')
        logger.info(f"[WORKFLOW DEBUG] OAuth handler exists: {oauth_handler is not None}")
        
        if not oauth_handler:
            error_msg = "OAuth handler not available for comment deletion"
            logger.error(f"[WORKFLOW DEBUG] {error_msg}")
            state['errors'].append(error_msg)
            state['deleted_comments'] = []
            return state
            
        logger.info("[WORKFLOW DEBUG] Checking OAuth authentication status...")
        auth_status = oauth_handler.is_authenticated()
        logger.info(f"[WORKFLOW DEBUG] OAuth authentication status: {auth_status}")
        
        if not auth_status:
            error_msg = "OAuth authentication required for comment deletion"
            logger.error(f"[WORKFLOW DEBUG] {error_msg}")
            state['errors'].append(error_msg)
            state['deleted_comments'] = []
            return state
        
        # Get authenticated user's channel ID for ownership verification
        user_info = oauth_handler.get_user_info()
        if not user_info or not user_info.get('channel_id'):
            error_msg = "Could not retrieve authenticated user's channel ID"
            logger.error(f"[WORKFLOW DEBUG] {error_msg}")
            state['errors'].append(error_msg)
            state['deleted_comments'] = []
            return state
        
        user_channel_id = user_info['channel_id']
        logger.info(f"[WORKFLOW DEBUG] Authenticated user channel ID: {user_channel_id}")
        
        try:
            processed_comments = 0
            
            for comment in state['spam_comments']:
                try:
                    # Delete spam comments with high confidence (any type)
                    # Also log what we're checking for debugging
                    is_spam = comment['analysis']['is_spam']
                    spam_type = comment['analysis']['spam_type']
                    confidence = comment['analysis']['confidence']
                    
                    logger.info(f"[DELETE DEBUG] Comment {comment['id']}: is_spam={is_spam}, type={spam_type}, confidence={confidence}")
                    
                    # Process high-confidence spam of any type - use moderation for all comments
                    if (is_spam and confidence > 0.7):
                        logger.info(f"[MODERATE DEBUG] Attempting to moderate comment {comment['id']} (type: {spam_type}, confidence: {confidence})")
                        
                        moderation_success = oauth_handler.moderate_comment(
                            comment['id'], 
                            moderation_status='rejected',
                            ban_author=True  # Ban repeat spam offenders
                        )
                        if moderation_success:
                            logger.info(f"Successfully moderated spam comment {comment['id']} as rejected and banned author")
                            # Track moderated comments (treated as deleted for UI)
                            if 'moderated_comments' not in state:
                                state['moderated_comments'] = []
                            state['moderated_comments'].append(comment['id'])
                            logger.info(f"[STATE DEBUG] Added comment {comment['id']} to moderated_comments. Current list: {state['moderated_comments']}")
                            logger.info(f"[STATE DEBUG] State keys: {list(state.keys())}")
                            logger.info(f"[STATE DEBUG] moderated_comments length: {len(state['moderated_comments'])}")
                        else:
                            logger.info(f"Comment {comment['id']} could not be moderated (likely due to YouTube policy restrictions)")
                        
                        # Rate limiting
                        time.sleep(1)
                        processed_comments += 1
                    else:
                        logger.info(f"[MODERATE DEBUG] Skipping comment {comment['id']}: not high-confidence spam (confidence: {confidence})")
                        
                except Exception as e:
                    error_msg = f"Failed to moderate comment {comment['id']}: {str(e)}"
                    logger.error(error_msg)
                    state['errors'].append(error_msg)
            
            # Get moderated comments count
            moderated_comments = state.get('moderated_comments', [])
            
            # No deleted comments - only moderated comments (treated as deleted for UI)
            state['deleted_comments'] = []
            logger.info(f"[WORKFLOW DEBUG] Processed {processed_comments} high-confidence spam comments")
            logger.info(f"Successfully moderated {len(moderated_comments)} comments as rejected")
            
        except Exception as e:
            error_msg = f"Error in deletion process: {str(e)}"
            logger.error(error_msg)
            state['errors'].append(error_msg)
            state['deleted_comments'] = []
        
        return state
    
    def generate_report(self, state: SpamDetectionState) -> SpamDetectionState:
        """Generate processing report"""
        try:
            logger.info(f"[GENERATE_REPORT DEBUG] Received state keys: {list(state.keys())}")
            logger.info(f"[GENERATE_REPORT DEBUG] moderated_comments in state: {state.get('moderated_comments', 'NOT_FOUND')}")
            logger.info(f"[GENERATE_REPORT DEBUG] moderated_comments length: {len(state.get('moderated_comments', []))}")
            total_comments = len(state['comments'])
            analyzed_comments = len(state['analyzed_comments'])
            
            # Count only actual spam comments
            actual_spam_comments = [c for c in state['spam_comments'] if c['analysis']['is_spam']]
            spam_detected = len(actual_spam_comments)
            
            # Count high-confidence gambling spam (what would be deleted)
            high_confidence_spam = [c for c in actual_spam_comments if 
                                   c['analysis']['confidence'] > 0.7 and 
                                   c['analysis']['spam_type'] == 'gambling']
            high_confidence_count = len(high_confidence_spam)
            
            deleted_count = 0  # No deletions - only moderation
            moderated_comments_list = state.get('moderated_comments', [])
            moderated_count = len(moderated_comments_list)
            total_actions = moderated_count  # Only moderated comments
            
            # Debug logging for moderated comments
            logger.info(f"[REPORT DEBUG] deleted_count: {deleted_count}, moderated_count: {moderated_count}, total_actions: {total_actions}")
            logger.info(f"[REPORT DEBUG] moderated_comments list: {moderated_comments_list}")
            logger.info(f"[REPORT DEBUG] deleted_comments list: {state['deleted_comments']}")
            
            # Calculate statistics
            spam_rate = (spam_detected / total_comments * 100) if total_comments > 0 else 0
            high_confidence_rate = (high_confidence_count / spam_detected * 100) if spam_detected > 0 else 0
            action_rate = (total_actions / high_confidence_count * 100) if high_confidence_count > 0 else 0
            
            # Categorize spam types (only for actual spam)
            spam_categories = {}
            risk_levels = {}
            
            for comment in actual_spam_comments:
                spam_type = comment['analysis']['spam_type']
                risk_level = comment['analysis']['risk_level']
                
                spam_categories[spam_type] = spam_categories.get(spam_type, 0) + 1
                risk_levels[risk_level] = risk_levels.get(risk_level, 0) + 1
            
            state['processing_stats'] = {
                'total_comments': total_comments,
                'analyzed_comments': analyzed_comments,
                'spam_detected': spam_detected,
                'high_confidence_spam': high_confidence_count,
                'deleted_count': deleted_count,
                'moderated_count': moderated_count,
                'total_actions': total_actions,
                'spam_rate_percent': round(spam_rate, 2),
                'high_confidence_rate_percent': round(high_confidence_rate, 2),
                'action_rate_percent': round(action_rate, 2),
                'spam_categories': spam_categories,
                'risk_levels': risk_levels,
                'errors_count': len(state['errors']),
                'processing_time': time.time()
            }
            
            logger.info(f"Processing complete: {spam_detected} spam detected ({high_confidence_count} high-confidence), {moderated_count} moderated as rejected")
            
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
    
    def run(self, initial_state: SpamDetectionState, oauth_handler=None) -> SpamDetectionState:
        """Run the complete spam detection workflow"""
        # Initialize state with default values
        initial_state.setdefault('comments', [])
        initial_state.setdefault('analyzed_comments', [])
        initial_state.setdefault('spam_comments', [])
        initial_state.setdefault('deleted_comments', [])
        initial_state.setdefault('moderated_comments', [])
        initial_state.setdefault('errors', [])
        initial_state.setdefault('processing_stats', {})
        
        # Store OAuth handler in state for deletion step
        initial_state['oauth_handler'] = oauth_handler
        
        try:
            result = self.workflow.invoke(initial_state)
            return result
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            initial_state['errors'].append(f"Workflow error: {str(e)}")
            return initial_state