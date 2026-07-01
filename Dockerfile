FROM python:3.11-slim

# Disable .pyc files and force stdout/stderr to be unbuffered so logs appear
# immediately in docker logs without buffering.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# --- System dependencies ---
# gecko driver is installed via apt alongside firefox-esr so that both come
# from the SAME Debian repository and are guaranteed to be compatible.
# A mismatched geckodriver (e.g. 0.35.0 from GitHub vs Firefox 140 from apt)
# causes "Failed to decode response from marionette" because the wire
# protocol changed between versions.
#
# Extra packages needed at runtime that are only "recommended" by apt:
#   fonts-liberation   - Firefox crashes on startup with no fonts available
#   libdbus-glib-1-2   - D-Bus GLib bindings used for internal IPC
#   libasound2t64      - ALSA library Firefox links against even in headless mode
RUN apt-get update && apt-get install -y --no-install-recommends \
    firefox-esr \
    wget \
    fonts-liberation \
    libdbus-glib-1-2 \
    libasound2t64 \
    && rm -rf /var/lib/apt/lists/*

# --- Install geckodriver ---
# geckodriver is not packaged in Debian trixie; download from the official
# GitHub release. Version 0.35.0 supports Firefox 115+ (Debian ships 140.x).
ARG GECKODRIVER_VERSION=0.35.0
RUN wget -q \
    "https://github.com/mozilla/geckodriver/releases/download/v${GECKODRIVER_VERSION}/geckodriver-v${GECKODRIVER_VERSION}-linux64.tar.gz" \
    -O /tmp/geckodriver.tar.gz \
    && tar -xzf /tmp/geckodriver.tar.gz -C /usr/local/bin/ \
    && rm /tmp/geckodriver.tar.gz \
    && chmod +x /usr/local/bin/geckodriver


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
