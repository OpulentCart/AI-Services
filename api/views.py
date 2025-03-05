from rest_framework.response import Response
from rest_framework.decorators import api_view
from .pinecone_service import insert_embeddings, get_related_products
from .models import Product
from rest_framework import status
from .pinecone_service import (
    insert_embeddings_product,
    update_embeddings_product,
    delete_embeddings_product,
    insert_embeddings,
    get_related_products
)

# Insert Single Product Embeddings API
@api_view(['POST'])
def insert_product_embeddings_api(request, product_id):
    try:
        insert_embeddings_product(product_id)
        return Response({
            "message": f"✅ Embeddings inserted for product {product_id} into Pinecone!",
            "product_id": str(product_id)
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Update Single Product Embeddings API
@api_view(['PUT'])
def update_product_embeddings_api(request, product_id):
    try:
        update_embeddings_product(product_id)
        return Response({
            "message": f"✅ Embeddings updated for product {product_id} in Pinecone!",
            "product_id": str(product_id)
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Delete Single Product Embeddings API
@api_view(['DELETE'])
def delete_product_embeddings_api(request, product_id):
    try:
        delete_embeddings_product(product_id)
        return Response({
            "message": f"✅ Embeddings deleted for product {product_id} from Pinecone!",
            "product_id": str(product_id)
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
