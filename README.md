# Legal AI Assistant - MVP Red Flags Review

A basic MVP implementation of the Legal AI Assistant platform focusing on automated contract risk assessment and red flags review.

## Project Structure

```
├── frontend/          # Next.js React application
│   ├── src/
│   │   ├── app/       # Next.js app router
│   │   └── components/ # React components
│   └── package.json
├── backend/           # FastAPI Python backend
│   ├── agents/        # Multi-agent architecture
│   │   ├── document_processor.py
│   │   ├── risk_analyzer.py
│   │   └── orchestrator.py
│   ├── main.py        # FastAPI main application
│   └── requirements.txt
├── claude.md          # Project overview
└── PRD.md            # Product requirements document
```

## Features (MVP)

- **Document Upload**: Support for PDF, DOCX, and TXT files
- **AI Analysis**: Automated legal risk assessment using Claude API
- **Side-by-Side Interface**: Original document and analysis results
- **Multi-Agent Architecture**: Modular processing pipeline

## Quick Start

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create environment file:
```bash
cp .env.example .env
```

4. Add your Anthropic API key to `.env`:
```
ANTHROPIC_API_KEY=your_key_here
```

5. Run the backend:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage

1. Open the frontend at `http://localhost:3000`
2. Upload a legal document (PDF, DOCX, or TXT)
3. Enter analysis instructions (e.g., "Please perform a red flags review")
4. Click "Analyze Document"
5. Review the results in the side-by-side interface

## Architecture

### Multi-Agent System

- **Document Processor**: Extracts text from uploaded files
- **Risk Analyzer**: Identifies legal risks using Claude API
- **Orchestrator**: Coordinates the workflow between agents

### Tech Stack

- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python, Anthropic Claude API
- **Document Processing**: PyPDF2, python-docx

## Next Steps

This MVP provides the foundation for the red flags review feature. Future enhancements:

1. Enhanced UI with interactive issue management
2. Advanced multi-agent coordination with LangGraph
3. Template generation capabilities
4. Document comparison features
5. User authentication and file management

## Development Notes

- Backend runs on port 8000
- Frontend runs on port 3000
- CORS is configured for local development
- API key required for Anthropic Claude access