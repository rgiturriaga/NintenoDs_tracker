FROM python:3.11-slim

# --- System dependencies ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    firefox-esr \
    wget \
    && rm -rf /var/lib/apt/lists/*

# --- Install geckodriver (pre-pinned version avoids a network call at runtime) ---
ARG GECKODRIVER_VERSION=0.35.0
RUN wget -q \
    "https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz" \
    -O /tmp/geckodriver.tar.gz \
    && tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin/ \
    && rm /tmp/geckodriver.tar.gz \
    && chmod +x /usr/local/bin/geckodriver

# Point the scraper to the pre-installed driver, skipping webdriver_manager downloads
ENV GECKODRIVER_PATH=/usr/local/bin/geckodriver

# --- Python dependencies ---
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Application code ---
COPY src/ ./src/

# .env is NOT copied into the image intentionally.
# Inject secrets at runtime via: docker run --env-file .env ...

WORKDIR /app/src

CMD ["python", "bot.py"]
