### Base Image
FROM python:3.12-slim AS backend

# Set the container working directory
WORKDIR /workdir

# Install pipx and Poetry directly
RUN pip install --no-cache pipx && pipx install poetry

# Ensure that the PATH contains the directory for pipx-installed binaries
ENV PATH="/root/.local/bin:$PATH"

# Copy all project files (backend and frontend)
COPY . /workdir

# Install backend dependencies using Poetry
RUN poetry install --no-interaction --no-ansi

### Frontend Stage
FROM node:18-alpine AS frontend

# Set the working directory for the frontend
WORKDIR /workdir/frontend

# Copy the entire project and switch to the frontend directory
COPY . /workdir

# Install frontend dependencies
RUN npm install --prefix frontend

# Build the frontend
RUN npm run build --prefix frontend

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



# Expose the backend port
# EXPOSE 8000

## Expose necessary ports (e.g., for your backend)??? ermmm
#EXPOSE 8000
## Command to run the backend, and you can serve static files from here if needed
#CMD ["poetry", "run", "python", "main.py"]

# Command to run the backend and the frontend dev server using a simple shell script
# CMD ["sh", "-c", "cd frontend && npm run dev & poetry run python main.py"]
