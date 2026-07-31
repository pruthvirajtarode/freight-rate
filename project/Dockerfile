# Multi-stage build for FreightAI

# Stage 1: Build Backend
FROM python:3.10-slim AS backend

WORKDIR /app

# Install system dependencies for compiling specific ML libraries if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend, frontend and data code
COPY backend/ /app/backend/
COPY data/ /app/data/
COPY frontend/ /app/frontend/

# Stage 2: Final Image (combines backend and frontend serving if desired)
# For this assessment, we'll just run the backend API from the container.
# The frontend can be served via Nginx in a separate container, 
# or by mounting it to a static server.

FROM backend AS final

WORKDIR /app/backend

# Expose FastAPI port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
