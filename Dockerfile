# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables to prevent Python from writing .pyc files and to ensure real-time output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /usr/src/app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y gcc portaudio19-dev libffi-dev && \
    apt-get install -y build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt ./

# Install the latest pip
RUN pip install --upgrade pip

# Install any needed packages specified in requirements.txt with retries and increased timeout
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt || \
    (sleep 10 && pip install --default-timeout=100 --no-cache-dir -r requirements.txt) || \
    (sleep 20 && pip install --default-timeout=100 --no-cache-dir -r requirements.txt)

# Copy the rest of the application code into the container
COPY . .

# Expose ports for Streamlit and FastAPI
EXPOSE 8501
EXPOSE 8000

# Start both Streamlit and FastAPI
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port 8000 & streamlit run app.py --server.port 8501 --server.address 0.0.0.0"]
