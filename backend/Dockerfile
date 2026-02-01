# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements-utf8.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Expose port and start
EXPOSE 8000
CMD ["python", "main.py"]
