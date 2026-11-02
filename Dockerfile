# The teashop web app: Django served by gunicorn.  Caddy (compose.yaml)
# sits in front and terminates HTTPS.
FROM python:3.15-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN groupadd --system --gid 10001 teashop \
    && useradd --system --uid 10001 --gid teashop --home-dir /app --no-create-home teashop

WORKDIR /app

# The ops agent's checks (apps/ops) reach the server over SSH, with a key
# limited to a few fixed commands (deploy/server/ops/).
RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Exact, hash-checked versions so every deploy installs the same packages.
COPY requirements.lock .
RUN pip install --require-hashes -r requirements.lock

COPY . .

# Static files are collected at build time.  The settings need these values
# to load; they are placeholders used only by this step.
RUN DJANGO_ENV=production DJANGO_SECRET_KEY=build-only DATABASE_URL=sqlite:////tmp/build.sqlite3 \
    python manage.py collectstatic --noinput \
    && rm -f /tmp/build.sqlite3 \
    && mkdir -p /app/var/media \
    && chown -R teashop:teashop /app/var

ARG GIT_SHA=local
ENV GIT_SHA=${GIT_SHA} \
    DJANGO_ENV=production

USER teashop
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=4).status == 200 else 1)"]

CMD ["gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "3", \
     "--access-logfile", "-", \
     "--no-control-socket", \
     "--forwarded-allow-ips", "*"]
