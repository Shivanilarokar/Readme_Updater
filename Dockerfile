# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn

# Expose port 8000 for Azure Web App
EXPOSE 8000

# Command to run FastAPI app
CMD ["uvicorn", "Fastweb:app", "--host", "0.0.0.0", "--port", "8000"]
