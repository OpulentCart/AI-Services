from rest_framework.response import Response
from rest_framework.decorators import api_view
from .pinecone_service import insert_embeddings, get_related_products
from .models import Product

# ✅ Insert Embeddings API
@api_view(['POST'])
def insert_embeddings_api(request):
    insert_embeddings()
    return Response({"message": "✅ Embeddings inserted into Pinecone!"})


# ✅ Get Related Products API
@api_view(['GET'])
def related_products_api(request, product_id):
    related_products = get_related_products(product_id)

    if not related_products:
        return Response({"message": "No related products found!"}, status=404)

    return Response({"related_products": related_products})
