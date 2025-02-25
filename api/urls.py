from django.urls import path
from .views import insert_embeddings_api, related_products_api

urlpatterns = [
    path('related-products/<str:product_id>/', related_products_api, name="related-products"),
]
