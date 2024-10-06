### Base Image
FROM python:3.12-slim

# Set the container working directory
WORKDIR /workdir

# Install pipx and Poetry directly for Python dependency management
RUN pip install --no-cache pipx && pipx install poetry

# Ensure that the PATH contains the directory for pipx-installed binaries
ENV PATH="/root/.local/bin:$PATH"

# Install Node.js for frontend build
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

# Copy the entire project (backend and frontend)
COPY . /workdir

# Install backend dependencies using Poetry
RUN poetry install --no-interaction --no-ansi

# Install frontend dependencies and build the frontend
RUN npm install --prefix /workdir/frontend && npm run build --prefix /workdir/frontend

# Optional: clean up unnecessary packages or files after the build
RUN rm -rf /workdir/frontend/node_modules
