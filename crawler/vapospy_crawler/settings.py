BOT_NAME = "vapospy_crawler"

SPIDER_MODULES = ["vapospy_crawler.spiders"]
NEWSPIDER_MODULE = "vapospy_crawler.spiders"

ROBOTSTXT_OBEY = True

# Identify the bot honestly and give the site owner a way to reach out.
# vapospy.com's robots.txt currently allows all crawling.
USER_AGENT = "vapospy-clone-bot/0.1 (+mailto:asmarakirana55@gmail.com)"

# Politeness: throttle instead of hammering the site.
DOWNLOAD_DELAY = 0.5
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 4
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 0.5
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

RETRY_TIMES = 3
HTTPCACHE_ENABLED = False

# Safety net for the generic same-domain discovery crawl -- caps how deep it
# can wander from the homepage in case of any other link trap besides the
# known locale-switcher one already filtered out in the spider.
DEPTH_LIMIT = 6

ITEM_PIPELINES = {
    "vapospy_crawler.pipelines.CsvExportPipeline": 100,
    "vapospy_crawler.pipelines.PostgresPipeline": 200,
}

# Postgres connection used by PostgresPipeline (override via env vars if needed).
import os  # noqa: E402

PG_DSN = {
    "host": os.environ.get("VAPOSPY_PG_HOST", "localhost"),
    "port": os.environ.get("VAPOSPY_PG_PORT", "5433"),
    "dbname": os.environ.get("VAPOSPY_PG_DB", "vapospy_clone"),
    "user": os.environ.get("VAPOSPY_PG_USER", "vapospy"),
    "password": os.environ.get("VAPOSPY_PG_PASSWORD", "vapospy"),
}

# Set to False to skip the DB pipeline (e.g. CSV-only dry runs).
PG_ENABLED = os.environ.get("VAPOSPY_PG_ENABLED", "1") == "1"

LOG_LEVEL = "INFO"
# Logs to stdout/stderr by default (visible in CI). For local runs, redirect
# the shell command to a file yourself if you want a persistent log:
#   scrapy crawl vapospy > ../output/crawl.log 2>&1

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
