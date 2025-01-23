# Knowledge Expansion System

A sophisticated Zettelkasten-style knowledge management system that helps users organize, analyze, and expand their knowledge base using modern AI technologies.

## Features

### Core Functionality
- **Zettelkasten Database**: Neo4j-based graph database for storing interconnected notes
- **Content Processing**: Automatic summarization and key concept extraction
- **Semantic Analysis**: Detects new information vs. existing knowledge
- **Relationship Management**: Automatic linking of related concepts and ideas

### Content Management
- **Multi-Format Support**: Process various content types (PDF, web pages, text)
- **Bulk Upload**: Process multiple files simultaneously with progress tracking
- **Web Scraping**: Extract content from URLs with configurable depth and domain restrictions
- **Batch Processing**: Advanced controls for managing large-scale content ingestion

### AI Integration
- **Multiple LLM Support**:
  - OpenAI (GPT-4, GPT-3.5)
  - Anthropic (Claude)
  - DeepSeek
  - Local models via Ollama
- **Performance Monitoring**: Track latency, throughput, and costs
- **Custom Templates**: Create and manage prompt templates
- **Fallback Handling**: Automatic model switching based on error rates

### Search & Discovery
- **Natural Language Queries**: Intuitive search using everyday language
- **Advanced Filters**: Search by tags, keywords, source types
- **Graph Visualization**: Interactive network view of knowledge connections
- **Semantic Search**: Find content based on meaning, not just keywords

### Analytics & Metrics
- **Content Analysis**: Track new vs. existing information
- **Processing Metrics**: Monitor batch operations and performance
- **Cost Tracking**: Track token usage and associated costs
- **Error Analysis**: Detailed error tracking and analysis

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Database**: Neo4j
- **AI Integration**: OpenAI, Anthropic, DeepSeek, Ollama
- **Content Processing**: Various Python libraries for text processing

### Frontend
- **Framework**: React with TypeScript
- **UI Components**: Chakra UI
- **Visualization**: React Force Graph
- **State Management**: React Hooks

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+
- Neo4j Database
- (Optional) Ollama for local LLM support

### Backend Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Knowledge_Expansion_System.git
   cd Knowledge_Expansion_System
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Start the backend server:
   ```bash
   uvicorn src.api.main:app --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

The application will be available at `http://localhost:3000`

## Usage

### Basic Operations
1. **Adding Content**:
   - Upload files through the UI
   - Provide URLs for web scraping
   - Use bulk upload for multiple items

2. **Searching**:
   - Use natural language queries
   - Apply filters for specific content types
   - Explore through graph visualization

3. **Managing LLMs**:
   - Configure preferred models
   - Set up fallback behavior
   - Monitor performance and costs

### Advanced Features
1. **Batch Processing**:
   - Configure batch sizes
   - Set error thresholds
   - Monitor progress in real-time

2. **Template Management**:
   - Create custom prompt templates
   - Manage variables and parameters
   - Track template usage

3. **Analytics**:
   - View processing metrics
   - Analyze content relationships
   - Monitor system performance

## API Documentation

### Content Management

```bash
# Upload a single file
POST /upload/file
Content-Type: multipart/form-data
{
    "file": binary,
    "title": string (optional)
}

# Bulk upload files
POST /upload/bulk
Content-Type: multipart/form-data
{
    "files": binary[]
}

# Start web scraping
POST /scrape/start
{
    "urls": ["https://example.com"],
    "max_depth": 2,
    "follow_links": true,
    "same_domain_only": true
}
```

### Search & Query

```bash
# Search nodes
GET /search?keywords=machine+learning&tags=AI&source_type=pdf&only_new=true

# Get graph visualization data
GET /graph?max_nodes=100&min_confidence=0.5

# Natural language query
POST /query
{
    "query": "Find all notes about machine learning algorithms",
    "include_sources": true
}
```

### LLM Configuration

```bash
# Get supported LLM providers
GET /llm/providers

# Get available models for a provider
GET /llm/models/{provider}

# Configure LLM settings
POST /llm/configure
{
    "provider": "openai",
    "model_name": "gpt-4-turbo-preview",
    "api_key": "your-api-key",
    "temperature": 0.7,
    "max_tokens": 1000,
    "streaming": true
}
```

### Template Management

```bash
# Create prompt template
POST /llm/templates
{
    "name": "Concept Analysis",
    "description": "Analyze and extract key concepts",
    "template": "Analyze the following text:\n{text}\n\nExtract key concepts and their relationships.",
    "variables": ["text"],
    "model_name": "gpt-4-turbo-preview",
    "temperature": 0.7
}

# List templates
GET /llm/templates
```

## Troubleshooting Guide

### Common Issues

1. **Neo4j Connection Issues**
   ```
   Error: Failed to connect to Neo4j database
   ```
   - Check if Neo4j is running
   - Verify connection credentials in `.env`
   - Ensure Neo4j ports (7687, 7474) are not blocked

2. **LLM API Errors**
   ```
   Error: Authentication failed for LLM provider
   ```
   - Verify API key in `.env`
   - Check API key permissions
   - Ensure correct provider is configured

3. **File Upload Issues**
   ```
   Error: File upload failed - Invalid file type
   ```
   - Check supported file formats
   - Verify file size limits
   - Ensure proper file permissions

4. **Frontend Connection Issues**
   ```
   Error: Failed to connect to backend API
   ```
   - Verify backend server is running
   - Check CORS configuration
   - Confirm API endpoint URLs

### Performance Optimization

1. **Slow Processing**
   - Adjust batch size in configuration
   - Enable caching for frequently accessed data
   - Optimize database queries

2. **Memory Issues**
   - Configure proper chunk sizes for large files
   - Enable streaming for large responses
   - Monitor and adjust resource limits

### Debug Mode

Enable debug mode for detailed logging:
```bash
# Backend
export DEBUG=true
uvicorn src.api.main:app --reload --log-level debug

# Frontend
npm start -- --verbose
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Neo4j for graph database capabilities
- OpenAI, Anthropic, and DeepSeek for AI models
- Ollama for local model support
- React and Chakra UI for frontend components 