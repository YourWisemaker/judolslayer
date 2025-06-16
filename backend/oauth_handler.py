from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os
import json
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class YouTubeOAuthHandler:
    """Handle OAuth2 authentication for YouTube API operations"""
    
    def __init__(self, client_secrets_file: str = None):
        self.client_secrets_file = client_secrets_file or os.getenv('GOOGLE_CLIENT_SECRETS_FILE')
        self.client_id = os.getenv('GOOGLE_CLIENT_ID')
        self.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        self.scopes = ['https://www.googleapis.com/auth/youtube.force-ssl']
        self.redirect_uri = os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:5001/oauth/callback')
        self.credentials = None
        
        # Try to load existing credentials on initialization
        self.load_credentials()
        
    def get_authorization_url(self) -> str:
        """Get the authorization URL for OAuth2 flow"""
        try:
            flow = self._create_flow()
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'  # Force consent to ensure refresh token
            )
            
            # Store state for verification
            self._store_oauth_state(state)
            
            return authorization_url
            
        except Exception as e:
            logger.error(f"Error generating authorization URL: {e}")
            raise
    
    def handle_oauth_callback(self, authorization_code: str, state: str) -> Dict[str, Any]:
        """Handle OAuth2 callback and exchange code for tokens"""
        try:
            # Verify state
            if not self._verify_oauth_state(state):
                raise ValueError("Invalid OAuth state")
            
            flow = self._create_flow()
            
            # Exchange authorization code for tokens
            flow.fetch_token(code=authorization_code)
            
            self.credentials = flow.credentials
            
            # Store credentials securely
            self._store_credentials(self.credentials)
            
            # Get user info
            youtube = build('youtube', 'v3', credentials=self.credentials)
            channels_response = youtube.channels().list(
                part='snippet',
                mine=True
            ).execute()
            
            user_info = {
                'authenticated': True,
                'channel_id': channels_response['items'][0]['id'] if channels_response['items'] else None,
                'channel_title': channels_response['items'][0]['snippet']['title'] if channels_response['items'] else None,
                'has_deletion_permission': True
            }
            
            return user_info
            
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {e}")
            raise
    
    def load_credentials(self) -> bool:
        """Load stored credentials"""
        try:
            credentials_file = os.getenv('OAUTH_CREDENTIALS_FILE', 'credentials.json')
            logger.info(f"[OAUTH DEBUG] Attempting to load credentials from {credentials_file}")
            
            if os.path.exists(credentials_file):
                logger.info(f"[OAUTH DEBUG] Credentials file exists, loading...")
                self.credentials = Credentials.from_authorized_user_file(credentials_file, self.scopes)
                
                if self.credentials:
                    logger.info(f"[OAUTH DEBUG] Credentials loaded. Valid: {self.credentials.valid}, Expired: {self.credentials.expired}")
                    logger.info(f"[OAUTH DEBUG] Token: {self.credentials.token[:20]}...")
                    logger.info(f"[OAUTH DEBUG] Refresh token available: {bool(self.credentials.refresh_token)}")
                    logger.info(f"[OAUTH DEBUG] Scopes: {self.credentials.scopes}")
                    
                    # Check if we have a refresh token
                    if not self.credentials.refresh_token:
                        logger.warning("[OAUTH DEBUG] No refresh token available. User needs to re-authenticate.")
                        return False
                    
                    # Refresh if expired
                    if self.credentials.expired:
                        logger.info("[OAUTH DEBUG] Credentials expired, attempting to refresh...")
                        try:
                            self.credentials.refresh(Request())
                            self._store_credentials(self.credentials)
                            logger.info("[OAUTH DEBUG] Credentials refreshed successfully")
                            logger.info(f"[OAUTH DEBUG] New token: {self.credentials.token[:20]}...")
                        except Exception as refresh_error:
                            logger.error(f"[OAUTH DEBUG] Failed to refresh credentials: {refresh_error}")
                            return False
                    else:
                        logger.info("[OAUTH DEBUG] Credentials are not expired")
                
                final_result = self.credentials and self.credentials.valid
                logger.info(f"[OAUTH DEBUG] Final load_credentials result: {final_result}")
                return final_result
            else:
                logger.warning(f"[OAUTH DEBUG] Credentials file {credentials_file} not found")
            
            return False
            
        except Exception as e:
            logger.error(f"[OAUTH DEBUG] Error loading credentials: {e}")
            import traceback
            logger.error(f"[OAUTH DEBUG] Traceback: {traceback.format_exc()}")
            return False
    
    def get_authenticated_youtube_service(self):
        """Get authenticated YouTube service for API operations"""
        try:
            if not self.credentials or not self.credentials.valid:
                logger.info("[OAUTH DEBUG] Credentials invalid, attempting to reload...")
                if not self.load_credentials():
                    raise ValueError("No valid credentials available. Please authenticate first.")
            
            logger.info("[OAUTH DEBUG] Building YouTube service with valid credentials")
            service = build('youtube', 'v3', credentials=self.credentials)
            logger.info("[OAUTH DEBUG] YouTube service created successfully")
            return service
            
        except Exception as e:
            logger.error(f"[OAUTH DEBUG] Failed to create YouTube service: {e}")
            raise
    
    def delete_comment(self, comment_id: str) -> bool:
        """Delete a YouTube comment using authenticated service with retry logic"""
        import time
        from googleapiclient.errors import HttpError
        
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[OAUTH DEBUG] delete_comment() attempt {attempt + 1}/{max_retries} for comment_id: {comment_id}")
                
                # Check authentication status before attempting deletion
                auth_status = self.is_authenticated()
                logger.info(f"[OAUTH DEBUG] Authentication status before deletion: {auth_status}")
                
                if not auth_status:
                    logger.error(f"[OAUTH DEBUG] Authentication failed, cannot delete comment {comment_id}")
                    return False
                
                youtube = self.get_authenticated_youtube_service()
                logger.info(f"[OAUTH DEBUG] Got YouTube service, attempting to delete comment {comment_id}")
                
                # Attempt the deletion
                youtube.comments().delete(id=comment_id).execute()
                logger.info(f"[OAUTH DEBUG] Successfully deleted comment: {comment_id}")
                return True
                
            except HttpError as e:
                error_code = e.resp.status
                error_reason = e.error_details[0].get('reason', 'unknown') if e.error_details else 'unknown'
                
                logger.error(f"[OAUTH DEBUG] HTTP Error {error_code} for comment {comment_id}: {error_reason}")
                
                # Handle specific error cases
                if error_code == 400:
                    if 'processingFailure' in error_reason:
                        logger.warning(f"Comment {comment_id} cannot be deleted due to YouTube policy restrictions (processingFailure). This is normal for some comments.")
                        return False  # Don't retry for processingFailure
                    else:
                        logger.error(f"Bad request for comment {comment_id}: {error_reason}")
                        return False
                elif error_code == 403:
                    if 'quotaExceeded' in str(e) or 'rateLimitExceeded' in str(e):
                        logger.warning(f"Rate limit exceeded for comment {comment_id}, attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                            continue
                    elif 'forbidden' in str(e).lower():
                        logger.error(f"Permission denied for comment {comment_id}. User may not own this comment.")
                        return False
                elif error_code == 404:
                    logger.error(f"Comment {comment_id} not found. It may have been already deleted.")
                    return False
                elif error_code == 401:
                    logger.error(f"Authentication error for comment {comment_id}. Token may be expired.")
                    # Try to refresh credentials and retry
                    if attempt < max_retries - 1:
                        self.credentials = None
                        time.sleep(retry_delay)
                        continue
                    return False
                
                # For other HTTP errors, retry with backoff
                if attempt < max_retries - 1:
                    logger.warning(f"Retrying comment deletion in {retry_delay * (2 ** attempt)} seconds...")
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    logger.error(f"Failed to delete comment {comment_id} after {max_retries} attempts: HTTP {error_code} - {error_reason}")
                    return False
                    
            except Exception as e:
                logger.error(f"[OAUTH DEBUG] Unexpected error deleting comment {comment_id} (attempt {attempt + 1}/{max_retries}): {type(e).__name__}: {e}")
                
                # For unexpected errors, retry with backoff
                if attempt < max_retries - 1:
                    logger.warning(f"Retrying comment deletion in {retry_delay * (2 ** attempt)} seconds...")
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    logger.error(f"Failed to delete comment {comment_id} after {max_retries} attempts due to unexpected error")
                    return False
        
        return False
    
    def moderate_comment(self, comment_id: str, moderation_status: str = 'rejected', ban_author: bool = False) -> bool:
        """Moderate a YouTube comment using setModerationStatus API
        
        Args:
            comment_id: The ID of the comment to moderate
            moderation_status: 'published', 'rejected', or 'heldForReview'
            ban_author: Whether to ban the comment author (only valid with 'rejected')
        
        Returns:
            bool: True if moderation was successful, False otherwise
        """
        import time
        from googleapiclient.errors import HttpError
        
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"[OAUTH DEBUG] moderate_comment() attempt {attempt + 1}/{max_retries} for comment_id: {comment_id}, status: {moderation_status}")
                
                # Check authentication status before attempting moderation
                auth_status = self.is_authenticated()
                logger.info(f"[OAUTH DEBUG] Authentication status before moderation: {auth_status}")
                
                if not auth_status:
                    logger.error(f"[OAUTH DEBUG] Authentication failed, cannot moderate comment {comment_id}")
                    return False
                
                youtube = self.get_authenticated_youtube_service()
                logger.info(f"[OAUTH DEBUG] Got YouTube service, attempting to moderate comment {comment_id}")
                
                # Prepare moderation request
                request_params = {
                    'id': comment_id,
                    'moderationStatus': moderation_status
                }
                
                # Add banAuthor parameter only if rejecting and ban_author is True
                if moderation_status == 'rejected' and ban_author:
                    request_params['banAuthor'] = True
                
                # Attempt the moderation
                youtube.comments().setModerationStatus(**request_params).execute()
                logger.info(f"[OAUTH DEBUG] Successfully moderated comment: {comment_id} to status: {moderation_status}")
                return True
                
            except HttpError as e:
                error_code = e.resp.status
                error_reason = e.error_details[0].get('reason', 'unknown') if e.error_details else 'unknown'
                
                logger.error(f"[OAUTH DEBUG] HTTP Error {error_code} for comment moderation {comment_id}: {error_reason}")
                
                # Handle specific error cases
                if error_code == 400:
                    if 'banWithoutReject' in error_reason:
                        logger.error(f"Cannot ban author without rejecting comment {comment_id}")
                        return False
                    elif 'operationNotSupported' in error_reason:
                        logger.error(f"Moderation not supported for comment {comment_id} (legacy Google+ comment)")
                        return False
                    elif 'processingFailure' in error_reason:
                        logger.warning(f"Comment {comment_id} cannot be moderated due to YouTube policy restrictions (processingFailure)")
                        return False
                    else:
                        logger.error(f"Bad request for comment moderation {comment_id}: {error_reason}")
                        return False
                elif error_code == 403:
                    if 'quotaExceeded' in str(e) or 'rateLimitExceeded' in str(e):
                        logger.warning(f"Rate limit exceeded for comment moderation {comment_id}, attempt {attempt + 1}/{max_retries}")
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                            continue
                    elif 'forbidden' in str(e).lower():
                        logger.error(f"Permission denied for comment moderation {comment_id}. User may not be channel/video owner.")
                        return False
                elif error_code == 404:
                    logger.error(f"Comment {comment_id} not found for moderation. It may have been deleted.")
                    return False
                elif error_code == 401:
                    logger.error(f"Authentication error for comment moderation {comment_id}. Token may be expired.")
                    # Try to refresh credentials and retry
                    if attempt < max_retries - 1:
                        self.credentials = None
                        time.sleep(retry_delay)
                        continue
                    return False
                
                # For other HTTP errors, retry with backoff
                if attempt < max_retries - 1:
                    logger.warning(f"Retrying comment moderation in {retry_delay * (2 ** attempt)} seconds...")
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    logger.error(f"Failed to moderate comment {comment_id} after {max_retries} attempts: HTTP {error_code} - {error_reason}")
                    return False
                    
            except Exception as e:
                logger.error(f"[OAUTH DEBUG] Unexpected error moderating comment {comment_id} (attempt {attempt + 1}/{max_retries}): {type(e).__name__}: {e}")
                
                # For unexpected errors, retry with backoff
                if attempt < max_retries - 1:
                    logger.warning(f"Retrying comment moderation in {retry_delay * (2 ** attempt)} seconds...")
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    logger.error(f"Failed to moderate comment {comment_id} after {max_retries} attempts due to unexpected error")
                    return False
        
        return False
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        logger.info("[OAUTH DEBUG] is_authenticated() called")
        
        # Always try to load/refresh credentials first
        load_result = self.load_credentials()
        logger.info(f"[OAUTH DEBUG] load_credentials() returned: {load_result}")
        
        if not load_result:
            logger.warning("[OAUTH DEBUG] load_credentials() failed, returning False")
            return False
            
        creds_exist = self.credentials is not None
        creds_valid = self.credentials.valid if self.credentials else False
        
        logger.info(f"[OAUTH DEBUG] Credentials exist: {creds_exist}, Valid: {creds_valid}")
        
        final_result = self.credentials and self.credentials.valid
        logger.info(f"[OAUTH DEBUG] is_authenticated() final result: {final_result}")
        
        return final_result
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get authenticated user information"""
        try:
            if not self.is_authenticated():
                return None
            
            youtube = self.get_authenticated_youtube_service()
            channels_response = youtube.channels().list(
                part='snippet',
                mine=True
            ).execute()
            
            if channels_response['items']:
                channel = channels_response['items'][0]
                return {
                    'channel_id': channel['id'],
                    'channel_title': channel['snippet']['title'],
                    'thumbnail_url': channel['snippet']['thumbnails']['default']['url'],
                    'authenticated': True
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    def logout(self) -> bool:
        """Logout user and clear credentials"""
        try:
            self.credentials = None
            
            # Remove stored credentials
            credentials_file = os.getenv('OAUTH_CREDENTIALS_FILE', 'credentials.json')
            if os.path.exists(credentials_file):
                os.remove(credentials_file)
            
            return True
            
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return False
    
    def _store_credentials(self, credentials: Credentials):
        """Store credentials securely"""
        try:
            credentials_file = os.getenv('OAUTH_CREDENTIALS_FILE', 'credentials.json')
            
            with open(credentials_file, 'w') as f:
                f.write(credentials.to_json())
            
            # Set restrictive permissions
            os.chmod(credentials_file, 0o600)
            
        except Exception as e:
            logger.error(f"Error storing credentials: {e}")
    
    def _store_oauth_state(self, state: str):
        """Store OAuth state for verification"""
        try:
            state_file = os.getenv('OAUTH_STATE_FILE', 'oauth_state.txt')
            
            with open(state_file, 'w') as f:
                f.write(state)
            
            os.chmod(state_file, 0o600)
            
        except Exception as e:
            logger.error(f"Error storing OAuth state: {e}")
    
    def _verify_oauth_state(self, state: str) -> bool:
        """Verify OAuth state"""
        try:
            state_file = os.getenv('OAUTH_STATE_FILE', 'oauth_state.txt')
            
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    stored_state = f.read().strip()
                
                # Clean up state file
                os.remove(state_file)
                
                return state == stored_state
            
            return False
            
        except Exception as e:
            logger.error(f"Error verifying OAuth state: {e}")
            return False
    
    def _create_flow(self) -> Flow:
        """Create OAuth flow using environment variables or client secrets file"""
        try:
            # Try to use environment variables first
            if self.client_id and self.client_secret:
                client_config = {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                        "redirect_uris": [self.redirect_uri]
                    }
                }
                
                flow = Flow.from_client_config(
                    client_config,
                    scopes=self.scopes
                )
                flow.redirect_uri = self.redirect_uri
                logger.info("Using OAuth credentials from environment variables")
                return flow
            
            # Fall back to client secrets file
            elif self.client_secrets_file and os.path.exists(self.client_secrets_file):
                flow = Flow.from_client_secrets_file(
                    self.client_secrets_file,
                    scopes=self.scopes,
                    redirect_uri=self.redirect_uri
                )
                logger.info("Using OAuth credentials from client secrets file")
                return flow
            
            else:
                raise ValueError(
                    "No valid OAuth configuration found. Please provide either:\n"
                    "1. GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables, or\n"
                    "2. A valid client_secrets.json file"
                )
                
        except Exception as e:
            logger.error(f"Failed to create OAuth flow: {e}")
            raise