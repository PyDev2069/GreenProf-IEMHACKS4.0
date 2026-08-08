# ─────────────────────────────────────────────────────────────
# Stage 1 — dependency builder
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# System deps needed to compile any C-extension wheels (bcrypt, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --prefix=/install --no-cache-dir -r requirements.txt


# ─────────────────────────────────────────────────────────────
# Stage 2 — production image
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Non-root user for security
RUN groupadd --gid 1001 greenproof \
 && useradd  --uid 1001 --gid greenproof --shell /bin/bash --create-home greenproof

# Copy app source
COPY --chown=greenproof:greenproof . .

# Persistent volume for SQLite DB (swap for Postgres in prod)
RUN mkdir -p /app/instance && chown greenproof:greenproof /app/instance
VOLUME ["/app/instance"]

USER greenproof

EXPOSE 5000

# Gunicorn as the production WSGI server
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "run:app"]