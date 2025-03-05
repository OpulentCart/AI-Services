import os
from celery import Celery
from recommendations.pinecone_service import insert_embeddings

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recommendations.settings')

app = Celery('recommendations')

# Load task modules from all registered Django app configs
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks in each installed app
app.autodiscover_tasks(["recommendations"])

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
