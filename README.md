# InvestWise AI

InvestWise AI is an educational investment-planning application built with a
Flask frontend, a FastAPI backend, deterministic financial calculations, and
Gemini-generated explanations.

> **Disclaimer:** This project is for educational purposes only. Its projections
> and allocation examples are illustrative, are not professional financial
> advice, and do not guarantee returns.

## Features

- User registration, login, and token-based authentication.
- Financial profiles, investment goals, and risk assessments.
- Multi-agent analysis and what-if investment projections.
- Contextual chat and Gemini-generated explanations.
- SQLite persistence with Alembic-managed schema migrations.

Python performs financial projections; Gemini provides explanations and
conversational responses. Portfolio allocations and scenario assumptions are
simplified examples, not optimized investment advice.

## Quick start

See the [CODE project README](CODE/README.md) for prerequisites, configuration,
database setup, API details, and the complete development instructions.

In brief, from the repository root:

1. Follow the project README to install `uv` and create `CODE/.env` from
   `CODE/.env.example`. Set your own Gemini API key and a randomly generated
   secret key; never commit `.env` or credentials.
2. Install dependencies and apply database migrations:

   ```powershell
   Set-Location CODE
   uv sync
   uv run alembic -c BACKEND\alembic.ini upgrade head
   ```

3. Start the backend and frontend in separate terminals, following the run
   instructions in [CODE/README.md](CODE/README.md).

## Limitations

- This is an educational project, not a financial-advice or trading system.
- Market context can be unavailable or inaccurate; independently verify
  time-sensitive information.
- SQLite and in-memory request limiting are intended for local or small-scale
  use, not multi-instance production deployment.
- Development server settings must not be exposed publicly.

## License

No project license file is present. Unless a license is added, reuse and
redistribution permissions are not specified.
