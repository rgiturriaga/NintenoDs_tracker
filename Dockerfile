FROM python:3.11-slim

# Disable .pyc files and force stdout/stderr to be unbuffered so logs appear
# immediately in docker logs without buffering.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# --- Create a non-root user for runtime ---
RUN groupadd -r appuser && useradd -r -g appuser -m appuser

# --- Python dependencies ---
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Application code ---
COPY --chown=appuser:appuser src/ ./src/

USER appuser
WORKDIR /app/src

CMD ["python", "bot.py"]
