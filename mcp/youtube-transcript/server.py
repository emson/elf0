#!/usr/bin/env python3
# mcp/youtube-transcript/server.py
"""
YouTube Transcript MCP Server
Minimal implementation for extracting YouTube video transcripts and metadata
Compatible with Elf0's MCP client implementation
"""
import json
import sys
import re
from urllib.parse import urlparse, parse_qs
from youtube_transcript_api import YouTubeTranscriptApi

try:
    from rich.console import Console
    console = Console(stderr=True)
except ImportError:
    console = None

def log_message(message: str, style: str = None):
    """Log message using rich if available, otherwise print to stderr"""
    if console:
        console.print(message, style=style)
    else:
        print(f"[YouTube MCP] {message}", file=sys.stderr)


def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL"""
    # Handle youtube.com/watch?v=ID
    if 'youtube.com/watch' in url:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if 'v' in params:
            return params['v'][0]
    
    # Handle youtu.be/ID
    if 'youtu.be/' in url:
        return url.split('youtu.be/')[-1].split('?')[0]
    
    # Handle direct video ID
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    
    raise ValueError(f"Could not extract video ID from URL: {url}")


def validate_youtube_url(url: str) -> bool:
    """Validate if URL is a YouTube video URL"""
    try:
        extract_video_id(url)
        return True
    except ValueError:
        return False


def extract_transcript(url: str, language: str = "en") -> dict:
    """Extract transcript from YouTube video"""
    try:
        video_id = extract_video_id(url)
        log_message(f"📺 Fetching transcript for video: {video_id}", "blue")
        
        # Try to get transcript in specified language
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        except Exception:
            # Fallback to auto-generated or any available language
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Join all transcript segments
        transcript_text = ' '.join([item['text'] for item in transcript_list])
        word_count = len(transcript_text.split())
        
        log_message(f"✅ Transcript extracted: {word_count} words, {len(transcript_list)} segments", "green")
        
        return {
            "transcript_text": transcript_text,
            "language": language,
            "word_count": word_count,
            "segment_count": len(transcript_list)
        }
    
    except Exception as e:
        raise Exception(f"Failed to extract transcript: {str(e)}")


def get_transcript_text(url: str, language: str = "en") -> str:
    """Extract transcript text only from YouTube video"""
    try:
        log_message(f"🔍 DEBUG: get_transcript_text called with URL: {url}", "yellow")
        log_message(f"🔍 DEBUG: Language parameter: {language}", "yellow")
        
        video_id = extract_video_id(url)
        log_message(f"📺 Fetching transcript text for video: {video_id}", "blue")
        log_message(f"🔍 DEBUG: Extracted video ID: {video_id} from URL: {url}", "yellow")
        
        # Try to get transcript in specified language
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
            log_message(f"🔍 DEBUG: Successfully got transcript in {language}", "yellow")
        except Exception as e:
            log_message(f"🔍 DEBUG: Language {language} failed: {e}, trying fallback", "yellow")
            # Fallback to auto-generated or any available language
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            log_message(f"🔍 DEBUG: Fallback transcript retrieved", "yellow")
        
        # Join all transcript segments
        transcript_text = ' '.join([item['text'] for item in transcript_list])
        word_count = len(transcript_text.split())
        
        log_message(f"✅ Transcript text extracted: {word_count} words, {len(transcript_list)} segments", "green")
        log_message(f"🔍 DEBUG: First 100 chars of transcript: {transcript_text[:100]}...", "yellow")
        
        return transcript_text
    
    except Exception as e:
        log_message(f"❌ DEBUG: Error in get_transcript_text: {str(e)}", "red")
        raise Exception(f"Failed to extract transcript text: {str(e)}")


def get_video_metadata(url: str) -> dict:
    """Get basic YouTube video metadata from URL"""
    try:
        video_id = extract_video_id(url)
        log_message(f"📋 Getting metadata for video: {video_id}", "cyan")
        
        return {
            "video_id": video_id,
            "url": url,
            "platform": "YouTube",
            "note": "Full metadata extraction temporarily disabled due to YouTube API restrictions"
        }
    
    except Exception as e:
        raise Exception(f"Failed to get video metadata: {str(e)}")


def main():
    """Handle MCP requests via stdin/stdout"""
    log_message("🚀 YouTube Transcript MCP Server starting...", "bold green")
    log_message("💡 Waiting for MCP requests via stdin", "dim")
    
    tools = [
        {
            "name": "extract_transcript",
            "description": "Extract transcript text from a YouTube video",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "YouTube video URL or video ID"},
                    "language": {"type": "string", "description": "Language code (default: 'en')", "default": "en"}
                },
                "required": ["url"]
            }
        },
        {
            "name": "get_transcript_text",
            "description": "Extract transcript text only from a YouTube video (returns plain text)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "YouTube video URL or video ID"},
                    "language": {"type": "string", "description": "Language code (default: 'en')", "default": "en"}
                },
                "required": ["url"]
            }
        },
        {
            "name": "get_video_metadata",
            "description": "Get metadata for a YouTube video (title, channel, duration, etc.)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "YouTube video URL or video ID"}
                },
                "required": ["url"]
            }
        },
        {
            "name": "validate_youtube_url",
            "description": "Validate if a URL is a valid YouTube video URL",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to validate"}
                },
                "required": ["url"]
            }
        }
    ]
    
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            method = request.get("method")
            params = request.get("params", {})
            
            if method == "initialize":
                log_message("🔌 Client connected and initialized", "green")
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "youtube-transcript", "version": "0.1.0"}
                    }
                }
            elif method == "tools/list":
                response = {
                    "jsonrpc": "2.0", 
                    "id": request.get("id"),
                    "result": {"tools": tools}
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                
                try:
                    if tool_name == "extract_transcript":
                        url = args.get("url")
                        language = args.get("language", "en")
                        
                        if not url:
                            raise ValueError("URL is required")
                        
                        result = extract_transcript(url, language)
                        
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "result": {
                                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                            }
                        }
                    
                    elif tool_name == "get_transcript_text":
                        url = args.get("url")
                        language = args.get("language", "en")
                        
                        if not url:
                            raise ValueError("URL is required")
                        
                        result = get_transcript_text(url, language)
                        
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "result": {
                                "content": [{"type": "text", "text": result}]
                            }
                        }
                    
                    elif tool_name == "get_video_metadata":
                        url = args.get("url")
                        
                        if not url:
                            raise ValueError("URL is required")
                        
                        result = get_video_metadata(url)
                        
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "result": {
                                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                            }
                        }
                    
                    elif tool_name == "validate_youtube_url":
                        url = args.get("url")
                        
                        if not url:
                            raise ValueError("URL is required")
                        
                        is_valid = validate_youtube_url(url)
                        result = {"valid": is_valid, "url": url}
                        
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "result": {
                                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
                            }
                        }
                    
                    else:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request.get("id"),
                            "error": {"code": -1, "message": f"Unknown tool: {tool_name}"}
                        }
                
                except Exception as e:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {"code": -1, "message": str(e)}
                    }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                }
            
            print(json.dumps(response), flush=True)
            
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {"code": -32603, "message": str(e)}
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()