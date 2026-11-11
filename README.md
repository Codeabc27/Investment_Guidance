# InvestWise AI

## Multi-Agent LLM-Based System for Goal-Oriented Investment Guidance

InvestWise AI is a student-focused Generative AI project that provides personalized and explainable investment guidance based on financial goals, investment horizon, financial profile, and risk tolerance.

> **Disclaimer:** For educational and academic purposes only. This system does not provide professional financial advice or guarantee investment returns.

## Features

- User registration and login
- Financial profile and investment goals
- Risk assessment
- Multi-agent AI analysis
- Gemini-powered explanations and chat
- Market research
- Portfolio allocation suggestions
- Investment projections
- What-if scenario analysis
- Recommendation validation
- Dashboard and analysis history

## Multi-Agent Workflow

```text
User
 ↓
Investment Goal
 ↓
Financial Profile
 ↓
Risk Assessment
 ↓
Goal Agent
 ↓
Financial Agent
 ↓
Market Research Agent
 ↓
Risk Agent
 ↓
Portfolio Agent
 ↓
Scenario Agent
 ↓
Validation Agent
 ↓
Final Guidance
```

Python performs deterministic financial calculations. Gemini is used for reasoning, explanation, market context, and chat.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | Flask, HTML, CSS, JavaScript |
| Backend | FastAPI |
| Database | SQLite |
| AI | Google Gemini |
| Calculations | Python |
| Charts | Plotly / JavaScript |
| Authentication | JWT |
| Server | Uvicorn |

## Project Structure

```text
CODE/
├── BACKEND/
│   └── app/
│       ├── api/
│       ├── agents/
│       ├── services/
│       ├── schemas/
│       ├── database/
│       └── main.py
├── FRONTEND/
│   ├── templates/
│   └── static/
├── DATA_BASE/
├── .env
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## Environment

Create `.env` in the `CODE` folder:

```env
APP_NAME=Investment Guidance AI
DEBUG=true

JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=YOUR_SUPPORTED_GEMINI_MODEL
GEMINI_FALLBACK_MODEL=YOUR_SUPPORTED_FALLBACK_MODEL

BACKEND_URL=http://127.0.0.1:8000
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=true
SECRET_KEY=your-flask-secret
```

Never upload `.env` or API keys to GitHub.

## Installation

From the `CODE` folder:
```cmd
pip install uv
```cmd
uv sync
.venv\Scripts\activate
```

Install the dependencies defined in `pyproject.toml`.

## Run Backend

```cmd
cd BACKEND
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend: `http://127.0.0.1:8000`

API documentation: `http://127.0.0.1:8000/docs`

## Run Frontend

Open another Command Prompt:

```cmd
cd FRONTEND
uv run app.py
```

Frontend: `http://127.0.0.1:5000`

## User Flow

```text
Register / Login
      ↓
Dashboard
      ↓
Create Investment Goal
      ↓
Financial Profile
      ↓
Risk Assessment
      ↓
AI Analysis
      ↓
Recommendation
      ↓
Scenario Analysis
      ↓
AI Chat
      ↓
History
```

## AI Chat

The chat uses Gemini to answer questions using the user's goal, financial profile, and latest analysis.

Gemini is used for reasoning, explanations, market context, and conversational assistance. Financial calculations are handled by Python.

## What-If Analysis

Users can change assumptions such as monthly contribution or investment horizon and compare projected outcomes.

## Responsible AI

The system:

- Does not guarantee investment returns.
- Shows important assumptions.
- Uses validation before final guidance.
- Does not expose private chain-of-thought.
- Treats market information as time-sensitive.
- Provides an educational-use disclaimer.

## Academic Purpose

InvestWise AI demonstrates the practical use of:

- Generative AI
- Large Language Models
- Multi-Agent Systems
- Financial analysis
- Risk assessment
- Scenario simulation
- FastAPI
- Flask
- SQLite

## Future Enhancements

- Additional financial data providers
- Advanced portfolio optimization
- More asset classes
- Personalized alerts
- Mobile application
- Advanced scenario simulation

## License

This project is developed for academic and educational purposes.
