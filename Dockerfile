# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy only requirements first (for better caching)
COPY Requirements.txt .

# Install all dependencies
RUN pip install --no-cache-dir -r Requirements.txt

# Now copy the full project
COPY . /app

# Expose port 8000 for Azure Web App
EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "Fastweb:app", "--host", "0.0.0.0", "--port", "8000"]
