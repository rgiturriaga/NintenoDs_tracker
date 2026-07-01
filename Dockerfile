FROM python:3.11-slim

# Disable .pyc files and force stdout/stderr to be unbuffered so logs appear
# immediately in docker logs without buffering.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# --- System dependencies ---
# wget is a small tool; --no-install-recommends is fine for it.
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Firefox ESR is installed WITHOUT --no-install-recommends so that apt also
# pulls in all recommended packages. Firefox dynamically loads libraries like
# libasound2, libpulse0, libxt6, and font packages at startup. If they are
# missing it crashes immediately with 'Failed to decode response from marionette'.
RUN apt-get update && apt-get install -y \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

# --- Install geckodriver at build time (pre-pinned version) ---
# Baking the driver into the image avoids any network call at container startup.
ARG GECKODRIVER_VERSION=0.35.0
RUN wget -q \
    "https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz" \
    -O /tmp/geckodriver.tar.gz \
    && tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin/ \
    && rm /tmp/geckodriver.tar.gz \
    && chmod +x /usr/local/bin/geckodriver

# Point the scraper to the pre-installed driver, skipping webdriver_manager
ENV GECKODRIVER_PATH=/usr/local/bin/geckodriver

# --- Create a non-root user for runtime ---
# The application never needs root after the image is built.
# If an attacker escapes the process they land as an unprivileged user,
# not as root, which breaks most privilege-escalation paths.
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

# --- Python dependencies (installed as root into system Python) ---
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Application code (owned by appuser) ---
COPY --chown=appuser:appuser src/ ./src/

# Drop to non-root for all subsequent commands and at runtime
USER appuser
WORKDIR /app/src

CMD ["python", "bot.py"]
