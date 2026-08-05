# VerifAI

> 🚀 **Autonomous Multi-Agent Research & Fact Verification Platform**

---

## Project Highlights
VerifAI is a comprehensive, production-ready backend and frontend architecture demonstrating a multi-agent orchestrated research pipeline. 

### Features
- **Autonomous multi-agent workflow**: A seamless pipeline of specialized AI agents executing sequentially.
- **Intelligent query decomposition**: Breaks complex queries into distinct, verifiable factual sub-claims.
- **Evidence collection**: Retrieves structured evidence from the web for each sub-claim.
- **AI-powered claim verification**: Evaluates the veracity of sub-claims strictly against retrieved evidence.
- **Contradiction detection**: Analyzes verified claims to identify logical inconsistencies between them.
- **Structured research report generation**: Synthesizes the entire workflow into a cohesive, evidence-backed report.
- **REST API**: Exposes the research workflow through a clean, programmatic interface.

### Problem Statement
Large language models are prone to hallucination and lack traceability when generating direct answers to complex research queries. They confidently output plausible but incorrect information, making them unsuitable for rigorous fact-checking or academic research.

### Objectives
VerifAI replaces single-pass generation with a rigorously orchestrated, evidence-first research pipeline. Users submit research questions, and the system produces citation-backed reports with explainable confidence scoring, relying entirely on verifiable web evidence rather than internal LLM knowledge.

---

## Architecture Overview

VerifAI utilizes **LangGraph** to manage agent execution and state transitions robustly, while a **FastAPI** backend exposes a clean REST API. A **React** frontend provides a professional dashboard interface.

### Workflow

1. **Planner**
   ↓
2. **Research**
   ↓
3. **Verification**
   ↓
4. **Contradiction**
   ↓
5. **Report**

---

## Technology Stack

### Frontend
- **Framework**: React, TypeScript, Vite
- **Styling**: Tailwind CSS
- **Linting**: oxlint

### Backend
- **Framework**: FastAPI, Uvicorn
- **Validation**: Pydantic v2
- **Infrastructure**: In-Memory Job Store

### AI
- **Orchestration**: LangGraph
- **LLM Provider**: OpenRouter (configured for strict JSON outputs)
- **Search API**: Tavily

---

## Deployment

### Folder Structure

```text
verifai/
├── backend/
│   ├── app/
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
└── README.md
```

### Installation

Clone the repository:
```bash
git clone https://github.com/yourusername/verifai.git
cd verifai
```

### Environment Variables

Copy the `.env.example` file in the `backend/` directory to `.env` and fill in your keys:

```text
OPENROUTER_API_KEY=your_openrouter_api_key
TAVILY_API_KEY=your_tavily_api_key
LLM_PROVIDER=openrouter
LLM_MODEL=openai/gpt-4o
```

### Running Locally

**Backend Setup:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```
*(Note: `--workers 1` is strictly required for the in-memory JobStore)*

**Frontend Setup:**
```bash
cd frontend
npm install
npm run dev
```

### Deployment Instructions

VerifAI is designed to be easily deployed to modern cloud providers:
- **Backend**: Can be deployed to services like Render, Heroku, or AWS Elastic Beanstalk using standard Python WSGI/ASGI configurations.
- **Frontend**: Can be statically built (`npm run build`) and hosted on Vercel, Netlify, or AWS S3.

### API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Returns backend application health status. |
| `POST` | `/research` | Accepts a research query, creates a job, starts the LangGraph pipeline asynchronously, and returns the `job_id`. |
| `GET` | `/research/{job_id}` | Returns current pipeline execution status (Planner -> Research -> Verification -> Contradiction -> Report). |
| `GET` | `/research/{job_id}/result` | Retrieves the completed `ResearchReport`. Returns `202` while running, `200` upon completion, and structured `500` errors on failure. |

---

## Screenshots

*(Placeholder for future deployment screenshots)*

---

## Known Limitations

VerifAI is built with a highly stringent fact-checking pipeline designed to prioritize correctness and trustworthiness above all else. 

- **Strict Evidence Validation**: VerifAI intentionally performs strict evidence validation. When verifying claims, the AI agents are bound entirely to the evidence retrieved by the research phase. 
- **Validation Rejection**: Responses that fail strict internal JSON or UUID structural validation are rejected rather than producing unreliable reports. The pipeline fails-safe rather than displaying hallucinated or unverified data.
- **Model Compatibility**: Currently, the strict formatting constraints function best on heavyweight models. Compatibility with additional lightweight LLMs will improve in future releases. This behavior prioritizes correctness and trustworthiness.

---

## Current Status

- **Backend**: 🟢 Deployment Ready
- **Frontend**: 🟢 Deployment Ready
- **OpenRouter Integration**: 🟢 Architecture Verified
- **Testing Status**: 🟢 Documentation Complete

---

## Roadmap

Future improvements planned for VerifAI include:
- Better lightweight model compatibility
- Streaming execution
- PDF export
- DOCX export
- Authentication
- Research history
- Team collaboration
- Additional providers
- Docker deployment
- Kubernetes deployment
- Performance optimization

---

## Contributors
Developed as an autonomous AI multi-agent hackathon submission.

## License
MIT License

## Acknowledgements
- LangChain / LangGraph community
- OpenRouter
- Tavily
