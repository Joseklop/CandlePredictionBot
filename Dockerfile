# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables to prevent Python from writing .pyc files to disk and to buffer stdout and stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && \
    apt-get install -y build-essential gfortran && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Set the working directory
WORKDIR /app

# Copy the project files
COPY . /app

# Install dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-root

# Expose the port that the app runs on
EXPOSE 8000

# Run the application
CMD ["poetry", "run", "python", "main.py"]
