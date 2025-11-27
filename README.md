# Lead Scrapper

This project is a web scraping application with a FastAPI backend and a React frontend.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Node.js** (v18 or higher) & **npm**: [Download Node.js](https://nodejs.org/)
- **Python** (v3.13 or higher): [Download Python](https://www.python.org/)
- **uv** (Python package manager): [Download uv](https://github.com/astral-sh/uv) (Recommended)
  - You can install it via pip: `pip install uv`

## Installation

### 1. Backend Setup

The backend is built with FastAPI and uses `uv` for dependency management.

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   uv sync
   ```
   *Alternatively, if you are not using `uv`, you can create a venv manually and install dependencies listed in `pyproject.toml`.*

3. Install Playwright browsers (required for scraping):
   ```bash
   # If using uv
   uv run playwright install

   # If using standard pip/python
   playwright install
   ```

4. Environment Configuration:
   - Create a `.env` file in the `backend` directory if it doesn't exist.
   - Add necessary environment variables (e.g., API keys, database credentials) as required by the application.

### 2. Frontend Setup

The frontend is built with React and Vite.

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

## Running the Project

You will need to run the backend and frontend in separate terminal terminals.

### Start the Backend

1. Open a terminal and navigate to the `backend` directory.
2. Run the server:
   ```bash
   # If using uv
   uv run uvicorn app.main:app --reload

   # If using standard python
   python -m uvicorn app.main:app --reload
   ```
   The backend API will be available at `http://localhost:8000`.
   API Documentation is available at `http://localhost:8000/docs`.

### Start the Frontend

1. Open a new terminal and navigate to the `frontend` directory.
2. Start the development server:
   ```bash
   npm run dev
   ```
   The frontend application will be accessible at the URL shown in the terminal (usually `http://localhost:5173`).

## Project Structure

- **backend/**: FastAPI application, scraping logic, and data processing.
- **frontend/**: React application for the user interface.
