# ----------------------------------------------------------------
# -- Base Image for all ADK Backend Services (Standard Setup) --
# ----------------------------------------------------------------

# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
# Note: The path is relative to the build context (project root).
COPY services/backend/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the local 'src' directory to the container at /app/src
COPY services/backend/src ./src

# Copy the credentials into the image at /app/credentials
COPY credentials ./credentials

# Set PYTHONPATH to include the src directory
ENV PYTHONPATH=/app

# The command to run the application will be provided by docker-compose.yml
# e.g., CMD ["python", "src/orchestrator.py"]
