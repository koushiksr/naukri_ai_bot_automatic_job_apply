FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for Playwright
RUN apt-get update && apt-get install -y \
    libgbm-dev libasound2 libnss3 libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser
RUN playwright install --with-deps chromium

# Copy application files
COPY . .

# Set environment variables for headless execution on Railway
ENV HEADLESS=True
ENV PYTHONUNBUFFERED=1

# Command to run the APScheduler to apply to jobs 24/7
CMD ["python", "main_scheduler.py"]
