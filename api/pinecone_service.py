import psycopg2
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from django.conf import settings  # Ensure settings contain database credentials

# ✅ Initialize Pinecone (New API)
from pinecone import Pinecone, ServerlessSpec

pc = Pinecone(api_key=settings.PINECONE_API_KEY)
PINECONE_DIMENSIONS = 437
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
    cursor.execute("SELECT product_id, vendor_id, brand, name, description, category_id, sub_category_id FROM product")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    data = []
    for row in rows:
        product_id, vendor_id, brand, name, description, category_id, sub_category_id = row
        metadata = {
            "vendor_id": vendor_id,
            "brand": brand,
            "name": name,
            "description": description if description else "",
            "category_id": category_id,
            "sub_category_id": sub_category_id
        }
        text = f"{brand} {name} {category_id} {sub_category_id} {description}"
        data.append({"id": str(product_id), "text": text, "metadata": metadata})  # Ensure ID is a string
    
    return data


# ✅ Compute TF-IDF Vectors
def compute_tfidf_vectors():
    product_data = fetch_products()
    texts = [p["text"] for p in product_data]

    vectorizer = TfidfVectorizer(stop_words="english", max_features=PINECONE_DIMENSIONS)
    vectors = vectorizer.fit_transform(texts).toarray()

    # 🔥 Fix: Ensure vectors have exactly 437 dimensions
    if vectors.shape[1] < PINECONE_DIMENSIONS:
        # ✅ Pad with zeros if dimensions are less than 437
        padded_vectors = np.pad(vectors, ((0, 0), (0, PINECONE_DIMENSIONS - vectors.shape[1])), mode='constant')
    else:
        # ✅ Truncate if dimensions exceed 437
        padded_vectors = vectors[:, :PINECONE_DIMENSIONS]

    assert padded_vectors.shape[1] == PINECONE_DIMENSIONS, f"Expected {PINECONE_DIMENSIONS}, got {padded_vectors.shape[1]}"

    # ✅ Convert for Pinecone
    pinecone_vectors = [(p["id"], padded_vectors[i].tolist(), p.get("metadata", {})) for i, p in enumerate(product_data)]
    return pinecone_vectors


# ✅ Insert Embeddings (Only If Empty)
def insert_embeddings():
    if index_name in pc.list_indexes().names():
        vectors = compute_tfidf_vectors()
        pinecone_vectors = [{"id": v[0], "values": v[1], "metadata": v[2]} for v in vectors]
        index.upsert(vectors=pinecone_vectors)
        print("✅ Embeddings inserted into Pinecone!")


# ✅ Find Related Products
def get_related_products(product_id, top_k=5):
    """Find related products using Pinecone similarity search."""
    product_id = str(product_id)  # Ensure ID is a string
    
    # ✅ Get TF-IDF vector for given product
    fetch_response = index.fetch([str(product_id)])  # Fetch response from Pinecone

    # Extract the query vector correctly
    if str(product_id) in fetch_response.vectors:
        query_vector = fetch_response.vectors[str(product_id)].values
    else:
        print(f"❌ Product ID {product_id} not found in Pinecone!")
        return []

    # ✅ Search for Similar Products
    search_results = index.query(vector=query_vector, top_k=top_k+1, include_metadata=True)

    # ✅ Filter out the searched product itself and collect metadata
    related_products = [
        {"id": match["id"], "metadata": match.get("metadata", {})} 
        for match in search_results["matches"] 
        if match["id"] != product_id
    ]

    # ✅ Return top_k results (excluding the searched product)
    return related_products[:top_k]
