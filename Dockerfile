### Base Image
FROM python:3.12-slim AS backend

# Set the container working directory
WORKDIR /workdir

# Install pipx and Poetry directly
RUN pip install --no-cache pipx && pipx install poetry

# Ensure that the PATH contains the directory for pipx-installed binaries
ENV PATH="/root/.local/bin:$PATH"

# Copy all backend project files
COPY . /workdir

# Install backend dependencies using Poetry
RUN poetry install --no-interaction --no-ansi

### Frontend Stage
FROM node:18-alpine AS frontend

# Set the working directory for the frontend
WORKDIR /workdir/frontend

# Copy only the frontend directory (this prevents duplication in the path)
COPY ./frontend /workdir/frontend

# Install frontend dependencies
RUN npm install

# Build the frontend
RUN npm run build

### Final Stage
FROM python:3.12-slim

# Set the working directory
WORKDIR /workdir

# Copy the built frontend from the frontend stage
COPY --from=frontend /workdir/frontend/dist /workdir/frontend/build

# Copy the entire project (backend and frontend) from the backend stage
COPY --from=backend /workdir /workdir

# Install backend dependencies in the final stage to ensure everything is in place
RUN poetry install --no-interaction --no-ansi