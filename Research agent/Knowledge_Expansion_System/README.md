# Knowledge Expansion System

A sophisticated system that ingests various types of content (PDFs, videos, audio, websites) and processes them using LLMs to build an intelligent, queryable knowledge base.

## Features

- Multi-format content ingestion (PDF, video, audio, web)
- Automatic content summarization using LLMs
- Zettelkasten-style knowledge database with nodes and tags
- Intelligent duplicate detection and information linking
- Natural language querying interface
- Knowledge expansion through LLM integration

## Project Structure

```
Knowledge_Expansion_System/
├── src/
│   ├── ingestion/      # Content ingestion and processing
│   ├── database/       # Zettelkasten database implementation
│   ├── llm/           # LLM integration and processing
│   └── api/           # API endpoints and interface
├── tests/             # Test suite
├── data/
│   ├── raw/          # Raw ingested content
│   └── processed/    # Processed and structured data
└── docs/             # Documentation
```

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your API keys and configuration

## Usage

[Documentation to be added as the project develops]

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## License

MIT License 