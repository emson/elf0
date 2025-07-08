# YouTube Transcript MCP Server

A minimal Model Context Protocol (MCP) server for extracting YouTube video transcripts and metadata, designed for integration with Elf0 workflows.

## Features

- **Extract transcripts** from YouTube videos with language support
- **Get video metadata** including title, channel, duration, view count
- **Validate YouTube URLs** for proper format checking
- **Simple integration** with Elf0 MCP workflows

## Installation

From the project root directory, install the required dependency:

```bash
uv pip install youtube-transcript-api
```

## Starting the Server

Start the MCP server from the project root:

```bash
uv run python mcp/youtube-transcript/server.py
```

The server will start and wait for JSON-RPC requests via stdin. This is normal behaviour - it communicates with Elf0 workflows automatically.

## Testing the Server

### Quick Test with Elf0
Test the server with a real YouTube video using the example workflow:

```bash
uv run elf0 agent specs/content/youtube_analyzer.yaml --prompt "Analyse this youtube video https://www.youtube.com/watch?v=9tOmppsiO2w"
```

### Manual JSON-RPC Testing

```bash
# Test server connectivity
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | uv run python mcp/youtube-transcript/server.py

# Test transcript extraction
echo '{"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "extract_transcript", "arguments": {"url": "https://www.youtube.com/watch?v=9tOmppsiO2w"}}}' | uv run python mcp/youtube-transcript/server.py
```

### With Elf0 Workflows

The server integrates seamlessly with Elf0 workflows. Here's an example workflow configuration:

```yaml
version: "0.1"
description: "YouTube transcript analysis"
runtime: "langgraph"

llms:
  analyzer:
    type: openai
    model_name: gpt-4o-mini
    temperature: 0.3

workflow:
  type: sequential
  nodes:
    - id: extract_transcript
      kind: mcp
      config:
        server:
          command: ["uv", "run", "python", "mcp/youtube-transcript/server.py"]
          cwd: "/Users/benemson/Dropbox/devel/projects/ai/elf0"
        tool: "extract_transcript"
        parameters:
          url: "{input}"
          language: "en"
    
    - id: analyze_content
      kind: agent
      ref: analyzer
      config:
        prompt: |
          Analyze this YouTube transcript and provide key insights:
          
          {state.output}
      stop: true

  edges:
    - source: extract_transcript
      target: analyze_content
```

Run with Elf0:

```bash
uv run elf0 agent specs/content/youtube_analyzer.yaml --prompt "https://youtube.com/watch?v=example"
```

## Available Tools

### extract_transcript
- **Input**: `url` (YouTube URL), `language` (optional, default: "en")
- **Output**: Transcript text with metadata (word count, language, etc.)

### get_video_metadata  
- **Input**: `url` (YouTube URL)
- **Output**: Video title, channel, duration, description, view count, thumbnail

### validate_youtube_url
- **Input**: `url` (URL to validate)  
- **Output**: Boolean validation result

## Supported URL Formats

- `https://youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- Direct video IDs: `VIDEO_ID`

## Error Handling

The server handles common errors gracefully:
- Invalid URLs
- Private or deleted videos
- Missing transcripts
- Network failures

Errors are returned as JSON-RPC error responses with descriptive messages.