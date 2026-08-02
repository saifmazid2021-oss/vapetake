FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scrapy.cfg .
COPY vapospy_crawler ./vapospy_crawler

# DATABASE_URL is provided by the platform (Railway/Render) or passed via
# `docker run -e DATABASE_URL=...`. Runs once and exits -- schedule it with
# the platform's cron feature or the GitHub Actions workflow in
# .github/workflows/crawl.yml.
CMD ["scrapy", "crawl", "vapospy"]
