# Use a lightweight Python image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y libnss3 wget && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Playwright dependencies
RUN apt-get install -y wget curl xvfb && \
    apt-get clean

# Install Playwright and Browsers
RUN pip install playwright && playwright install

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application files
COPY . .

# Expose port if needed
EXPOSE 8000

# Set the entry point for your application
CMD ["python", "bot.py"]
