# Use a lightweight Python image
FROM python:3.10-slim

# Update package sources and install system dependencies
RUN apt-get update && \
    apt-get install -y wget curl xvfb libnss3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Playwright dependencies and browsers
RUN pip install playwright && playwright install

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application files
COPY . .

# Expose port if needed
EXPOSE 8000

# Set the entry point for your application
CMD ["python", "bot.py"]
