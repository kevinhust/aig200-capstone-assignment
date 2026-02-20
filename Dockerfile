# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY src/ ./src/
COPY models/ ./models/

# Expose the port the app runs on (Cloud Run defaults to 8080)
EXPOSE 8080

# Define environment variables
ENV SLEEPINSIGHT_API_KEY=prod-key-98765
ENV PYTHONPATH=/app

# Run main.py when the container launches
CMD ["sh", "-c", "uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
