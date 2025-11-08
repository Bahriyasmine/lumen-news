import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('lumen_news')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Schedule the scraper task
app.conf.beat_schedule = {
    # Scrape every 15 minutes
    "scrape-news-every-15-mins": {
        "task": "apps.scraper.tasks.scrape_news_fast",
        "schedule": crontab(minute="*/15"),
    },

    # Embedding task runs every 20 mins, slightly after scraping
    "generate-embeddings-every-20-mins": {
        "task": "apps.scraper.tasks.generate_embeddings",
        "schedule": crontab(minute="*/20"),
    },
}

app.conf.timezone = 'UTC'
# 🔥 Run the scraper once immediately when Celery Beat starts
#@app.on_after_configure.connect
#def trigger_first_scrape(sender, **kwargs):
#    sender.send_task('apps.scraper.tasks.scrape_realtime_news')