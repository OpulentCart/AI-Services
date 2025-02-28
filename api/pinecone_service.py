import psycopg2
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from django.conf import settings  # Ensure settings contain database credentials
from sentence_transformers import SentenceTransformer

# ✅ Initialize Pinecone (New API)
from pinecone import Pinecone, ServerlessSpec

# ✅ Initialize the model globally
model = SentenceTransformer('all-mpnet-base-v2')  # Using your requested model

pc = Pinecone(api_key=settings.PINECONE_API_KEY)
PINECONE_DIMENSIONS = 768
index_name = "related-products"

# ✅ Create Index if Not Exists
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=PINECONE_DIMENSIONS,  # Ensure this matches TF-IDF output
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")  # Adjust region as needed
    )
    print("✅ Pinecone Index Created!")

# ✅ Connect to Pinecone Index
index = pc.Index(name=index_name)


# ✅ PostgreSQL Connection
def get_postgres_connection():
    return psycopg2.connect(
        dbname=settings.DATABASES["default"]["NAME"],
        user=settings.DATABASES["default"]["USER"],
        password=settings.DATABASES["default"]["PASSWORD"],
        host=settings.DATABASES["default"]["HOST"],
        port=settings.DATABASES["default"]["PORT"],
    )


# ✅ Fetch Data from PostgreSQL
def fetch_products():
    conn = get_postgres_connection()
    cursor = conn.cursor()
    
    # ✅ Optimized Query with LEFT JOIN and COALESCE
    query = """
    SELECT 
    p.product_id, 
    p.vendor_id, 
    p.brand, 
    p.name, 
    p.description, 
    COALESCE(c.name, 'Unknown') AS category_name, 
    COALESCE(sc.name, 'Unknown') AS sub_category_name
FROM product p
LEFT JOIN sub_category sc ON p.sub_category_id = sc.sub_category_id
LEFT JOIN category c ON sc.category_id = c.category_id;

    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    data = []
    for row in rows:
        product_id, vendor_id, brand, name, description, category_name, sub_category_name = row
        
        metadata = {
            "vendor_id": vendor_id,
            "brand": brand,
            "name": name,
            "description": description if description else "",
            "category": category_name,
            "sub_category": sub_category_name,

        }
        
        # ✅ Use category and subcategory names instead of IDs
        text = f"{brand} {name} {category_name} {sub_category_name} {description}"
        
        data.append({"id": str(product_id), "text": text, "metadata": metadata})  # Ensure ID is a string
    
    return data

# ✅ Compute TF-IDF Vectors
def compute_mpnet_embeddings():
    product_data = fetch_products()
    texts = [p["text"] for p in product_data]

    # ✅ Generate dense embeddings using MPNet
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

    # ✅ Convert for Pinecone
    pinecone_vectors = [(p["id"], embeddings[i].tolist(), p["metadata"]) for i, p in enumerate(product_data)]
    return pinecone_vectors


# ✅ Insert Embeddings into Pinecone
def insert_embeddings():
    if index_name in pc.list_indexes().names():
        vectors = compute_mpnet_embeddings()
        pinecone_vectors = [{"id": v[0], "values": v[1], "metadata": v[2]} for v in vectors]
        index.upsert(vectors=pinecone_vectors)
        print("✅ MPNet Embeddings inserted into Pinecone!")

# ✅ Find Related Products
import psycopg2
import json

def get_related_products(product_id, top_k=5):
    """Find related products using Pinecone similarity search and fetch details from PostgreSQL."""
    product_id = str(product_id)  # Ensure ID is a string
    
    # ✅ Get TF-IDF vector for given product
    fetch_response = index.fetch([product_id])  # Fetch response from Pinecone

    # Extract the query vector correctly
    if product_id in fetch_response.vectors:
        query_vector = fetch_response.vectors[product_id].values
    else:
        print(f"❌ Product ID {product_id} not found in Pinecone!")
        return []

    # ✅ Search for Similar Products
    search_results = index.query(vector=query_vector, top_k=top_k+1, include_metadata=False)

    # ✅ Filter out the searched product itself
    related_products_data = [
        {"id": match["id"], "score": match["score"]}  # Include similarity score
        for match in search_results["matches"]
        if match["id"] != product_id
    ][:top_k]

    if not related_products_data:
        return []

    related_product_ids = [p["id"] for p in related_products_data]

    # ✅ Fetch product details from PostgreSQL
    conn = psycopg2.connect(
         dbname=settings.DATABASES["default"]["NAME"],
        user=settings.DATABASES["default"]["USER"],
        password=settings.DATABASES["default"]["PASSWORD"],
        host=settings.DATABASES["default"]["HOST"],
        port=settings.DATABASES["default"]["PORT"],
    )
    cursor = conn.cursor()

    query = f"""
        SELECT product_id, name, brand, price, main_image
        FROM product
        WHERE product_id IN ({','.join(['%s'] * len(related_product_ids))})
    """
    cursor.execute(query, related_product_ids)
    products = cursor.fetchall()

    # ✅ Convert to JSON format
    related_products = []
    for row in products:
        product_id = str(row[0])  # Convert ID to string for consistency
        related_products.append({
            "id": product_id,
            "name": row[1],
            "brand": row[2],
            "price": row[3],
            "main_image": row[4],
            "similarity_score": next((p["score"] for p in related_products_data if p["id"] == product_id), None)
        })

    cursor.close()
    conn.close()
    related_products.sort(key=lambda x: x["similarity_score"], reverse=True)

    return related_products
