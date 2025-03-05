from django.urls import path
from .views import insert_embeddings_api, related_products_api,insert_product_embeddings_api,update_product_embeddings_api,delete_product_embeddings_api

urlpatterns = [
    path('related-products/<str:product_id>/', related_products_api, name="related-products"),
    path('products/<int:product_id>/embeddings/insert/',insert_product_embeddings_api),
    path('products/<int:product_id>/embeddings/update/',update_product_embeddings_api),
    path('products/<int:product_id>/embeddings/delete/',delete_product_embeddings_api),
]
