from django.apps import AppConfig
from .pinecone_service import insert_embeddings


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        print("🔄 Checking Pinecone index and inserting embeddings if needed...")
        insert_embeddings()
