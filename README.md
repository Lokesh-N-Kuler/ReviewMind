# ReviewMind – AI-Powered Code Review Agent with Persistent Memory

ReviewMind is a full-stack, production-minded AI code review platform built with **FastAPI**, **React**, **Monaco Editor**, **Groq AI**, and **Hindsight by Vectorize**.

Unlike conventional stateless code review tools, ReviewMind features **persistent agent memory**. It remembers previous code reviews, learns project-specific coding standards, recognizes recurring developer mistakes, and provides increasingly tailored and accurate reviews over time.

---

## Architecture Overview

```
+-------------------------------------------------------------------------+
|                              Frontend (React)                           |
|  Monaco Editor | 2-Panel Review UI | Project Studio | GitHub PR Review  |
+------------------------------------+------------------------------------+
                                     | HTTP / REST
                                     v
+-------------------------------------------------------------------------+
|                            Backend (FastAPI)                            |
|   Auth (JWT) | Project Manager | Static AST Analyzer | Review Engine    |
+------------------+------------------------------+-----------------------+
                   |                              |
         +---------v---------+          +---------v---------+
         |  PostgreSQL / DB  |          |  Groq AI Engine   |
         |  Application Data |          | Structured Review |
         +-------------------+          +-------------------+
                   |
         +---------v---------+
         | Hindsight Memory  |
         | Persistent Bank   |
         +-------------------+
```

### Separation of Responsibilities
* **PostgreSQL / SQLAlchemy**: Stores transactional application records: users, projects, memberships, review history, audit logs, and encrypted GitHub connections.
* **Hindsight by Vectorize**: Manages agent long-term memory: semantic recall, recurring bug patterns, confirmed standards, and developer preferences across individual project banks.
* **Groq API**: High-speed LLM inference with structured JSON output, guided by system guardrails, static AST findings, and recalled memories.

---

## Technology Stack

### Frontend
* **React 19** & **Vite**
* **Tailwind CSS v4** (Crisp minimal light theme default, optional dark mode)
* **Monaco Editor** (`@monaco-editor/react` with Python, JS, TS, Java, C++, SQL syntax highlighting & line jumping)
* **React Router DOM**
* **Axios** (JWT interceptor)
* **Lucide React** icons

### Backend
* **Python 3.13** & **FastAPI**
* **Pydantic v2** & **Pydantic-Settings**
* **SQLAlchemy 2.0** ORM
* **Alembic** database migrations
* **Bcrypt** password hashing & **PyJWT** authentication
* **Python AST** static code analyzer (detects SQL concatenation, eval, shell=True, hardcoded credentials)

### AI & Agent Memory
* **Groq API** (`llama-3.3-70b-versatile`, configurable through `.env` with model availability inspection)
* **Hindsight by Vectorize** (`hindsight-client` Python SDK with project bank isolation)

---

## Quick Start Guide

### 1. Prerequisites
* Python 3.11+
* Node.js v18+ & npm
* (Optional) Docker for running a local Hindsight server, or Hindsight Cloud credentials

### 2. Backend Setup

```bash
cd CodeReviewAgent/backend

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Edit `.env` with your credentials:
```env
DATABASE_URL=sqlite:///./reviewmind.db
JWT_SECRET_KEY=your-secure-random-jwt-key-32-chars-min
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
HINDSIGHT_BASE_URL=http://localhost:8888
HINDSIGHT_API_KEY=
```

Run database migrations:
```bash
alembic upgrade head
```

Start the FastAPI backend server:
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at: `http://localhost:8000/docs`

---

### 3. Frontend Setup

```bash
cd CodeReviewAgent/frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
The web application will open at: `http://localhost:3000` (or `http://localhost:5173`)

---

## Setting up Hindsight Persistent Memory

ReviewMind uses official Hindsight SDK methods (`create_bank`, `retain`, `recall`, `list_memories`).

### Option A: Local Self-Hosted Hindsight Server (Docker)
Run the official Hindsight container:
```bash
docker run -d --name hindsight -p 8888:8888 vectorizeio/hindsight:latest
```

### Option B: Hindsight Cloud
1. Register for an account at [Vectorize Hindsight](https://vectorize.io).
2. Set in `backend/.env`:
```env
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
HINDSIGHT_API_KEY=your_hindsight_api_key
```

*Note: If Hindsight is not running or credentials are missing, ReviewMind displays an honest diagnostic indicator and does not simulate or fake memory results.*

---

## Running the Automated Test Suite

A comprehensive test suite verifies API health, user auth, project management, AST static analysis, review workflows, and Hindsight project isolation:

```bash
cd CodeReviewAgent/backend
.\venv\Scripts\pytest -v
```

---

## Repeatable Persistent Memory Demonstration

To observe ReviewMind's learning lifecycle:

```bash
cd CodeReviewAgent/backend
.\venv\Scripts\python demo_memory_learning.py
```

### The Demonstration Workflow:
1. **First Review (Unlearned State)**:
   The developer submits code with SQL concatenation (`query = "SELECT * FROM users WHERE id = " + user_id`).
   ReviewMind identifies SQL injection via AST and AI, recommends parameterized queries, and the developer accepts the fix.
   The validated lesson is retained into the project's Hindsight memory bank.
2. **Second Review (Learning Applied)**:
   The developer submits another function in the same project using string concatenation.
   ReviewMind recalls the previously established convention from Hindsight and flags the issue with explicit memory attribution:
   *`"Recalled from Project Memory (Hindsight): Team Rule: In E-Commerce Core, never use string concatenation..."`*
3. **Third Review**:
   ReviewMind verifies full adherence to project conventions.

---

## API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status |
| `GET` | `/api/health/diagnostics` | Inspects DB, Groq availability, and Hindsight connection |
| `POST` | `/api/auth/register` | Register new user account |
| `POST` | `/api/auth/login` | Authenticate and obtain JWT access token |
| `GET` | `/api/auth/me` | Fetch authenticated user profile |
| `POST` | `/api/projects` | Create a new software project and Hindsight bank |
| `GET` | `/api/projects` | List projects accessible to user |
| `GET` | `/api/projects/{id}` | Get project details and coding standards |
| `POST` | `/api/reviews` | Submit source code for full AI & memory review |
| `POST` | `/api/reviews/quick` | Instant sandbox code review without project setup |
| `GET` | `/api/reviews` | List review history with project & severity filters |
| `POST` | `/api/reviews/{id}/feedback` | Record developer feedback and retain into Hindsight |
| `GET` | `/api/memory/status` | Check Hindsight server connectivity |
| `GET` | `/api/memory/{project_id}` | Retrieve retained memories for a project |
| `POST` | `/api/memory/{project_id}/retain` | Manually teach a rule/convention to Hindsight |
| `POST` | `/api/memory/{project_id}/recall` | Test semantic recall from Hindsight |
| `POST` | `/api/github/connect-token` | Securely store encrypted GitHub token |
| `GET` | `/api/github/repositories` | List accessible repositories |
| `GET` | `/api/github/repositories/{owner}/{repo}/pull-requests` | List open PRs |
| `POST` | `/api/github/pull-requests/review` | Analyze PR diff with ReviewMind |
| `POST` | `/api/github/reviews/{id}/publish` | Publish developer-approved review to GitHub |

---

## Security & Privacy Considerations

1. **No Code Execution**: Submitted source code is parsed with static AST and LLM reasoning. Code is **never executed** on the host.
2. **Prompt Injection Shielding**: Source code is strictly treated as passive data in system prompts, neutralizing attempted prompt injection attacks embedded inside user code.
3. **Credential Protection**:
   * Passwords are encrypted with salt using pure `bcrypt`.
   * GitHub personal access tokens are stored encrypted using key-derived cipher streams and never returned in plain text over the API.
   * Private API keys (`GROQ_API_KEY`, `HINDSIGHT_API_KEY`, `JWT_SECRET_KEY`) are kept on the server and never exposed to the frontend.
4. **Explicit GitHub Publishing**: ReviewMind requires explicit developer confirmation before publishing any comment to a GitHub PR thread.
