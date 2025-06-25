# YouTube Transcript MCP Server

A minimal Model Context Protocol (MCP) server for extracting YouTube video transcripts and metadata, designed for integration with Elf0 workflows.

## Features

- **Extract transcripts** from YouTube videos with language support
- **Get video metadata** including title, channel, duration, view count
- **Validate YouTube URLs** for proper format checking
- **Simple integration** with Elf0 MCP workflows

## Installation

```bash
cd mcp/youtube-transcript
uv sync
```

## Usage

### Standalone Testing

```bash
# Test the MCP server directly
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | uv run python server.py
```

### With Elf0 Workflows

Create a workflow YAML file:

```yaml
version: "0.1"
description: "YouTube transcript analysis"
runtime: "langgraph"

llms:
  analyzer:
    type: anthropic
    model_name: claude-3-5-haiku-latest
    temperature: 0.3

workflow:
  type: custom_graph
  nodes:
    - id: extract_transcript
      kind: mcp
      config:
        server:
          command: ["uv", "run", "python", "mcp/youtube-transcript/server.py"]
        tool: "extract_transcript"
        parameters:
          url: "${state.input}"
          language: "en"
    
    - id: analyze_content
      kind: agent
      ref: analyzer
      config:
        prompt: |
          Analyze this YouTube transcript and provide key insights:
          
          {output}
      stop: true

  edges:
    - source: extract_transcript
      target: analyze_content
```

Run with Elf0:

```bash
uv run elf0 agent youtube_analyzer.yaml --prompt "https://youtube.com/watch?v=example"
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