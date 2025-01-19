# Use the official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for playwright
RUN apt-get update && apt-get install -y wget curl xvfb libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxcomposite1 libxrandr2 libgbm-dev libpangocairo-1.0-0 libxdamage1 libxkbcommon0 libasound2 libxshmfence-dev libwayland-server0 libwayland-client0

# Install playwright and browsers
RUN pip install playwright && playwright install

# Copy application code
COPY . .

# Install Python dependencies
RUN pip install -r requirements.txt

# Expose a port (if needed for the bot; otherwise optional)
EXPOSE 8000

# Run the bot
CMD ["python", "bot.py"]
