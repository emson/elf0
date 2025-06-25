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
        
        # Try to get transcript in specified language
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        except Exception:
            # Fallback to auto-generated or any available language
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Join all transcript segments
        transcript_text = ' '.join([item['text'] for item in transcript_list])
        
        return {
            "transcript_text": transcript_text,
            "language": language,
            "word_count": len(transcript_text.split()),
            "segment_count": len(transcript_list)
        }
    
    except Exception as e:
        raise Exception(f"Failed to extract transcript: {str(e)}")


def get_video_metadata(url: str) -> dict:
    """Get basic YouTube video metadata from URL"""
    try:
        video_id = extract_video_id(url)
        
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