
# AI-Powered Recommendation Engine Documentation

## 1. Introduction

In the modern e-commerce landscape, personalized recommendations play a crucial role in enhancing user experience, increasing engagement, and boosting sales. This document details the implementation of an AI-powered recommendation system that provides *Related Products*, *You May Also Like*, and *Suggested for You* recommendations.

## 2. System Architecture

### 2.1 Components

- *PostgreSQL Database:* Stores product and user interaction data.
- *Pinecone Vector Database:* Stores and retrieves product embeddings for similarity-based recommendations.
- *Django Backend:* Exposes APIs to fetch and serve recommendations.
- *RESTful API:* Provides endpoints for fetching recommendations.
- *Machine Learning Algorithms:* Used for collaborative filtering and similarity-based recommendations.

### 2.2 Technologies Used

- *Django REST Framework (Python) for API development*
- *PostgreSQL for structured data storage*
- *Pinecone for vector storage and retrieval*
- *Collaborative Filtering (ALS/SVD) for personalized recommendations*
- *Sentence Transformer (all-mpnet-base-v2) for product embeddings*

## 3. Recommendation Techniques

The recommendation engine uses a hybrid approach combining:

- *Content-based filtering:* Uses product descriptions, brands, and embeddings to recommend similar items.
- *Collaborative filtering:* Analyzes user interactions to find similar users and recommend products based on their preferences.
- *Weighted interaction scoring:* Assigns different scores to user actions for better personalization.

## 4. Weighting System for User Interactions

| User Interaction Type | Weight |
| --------------------- | ------ |
| View                  | 1      |
| Click                 | 2      |
| Add to Cart           | 3      |
| Purchase              | 5      |
| Rating Given          | 4      |
| Wishlist              | 4      |

The weights help prioritize actions that indicate stronger intent.

## 5. Database & Vector Storage

### 5.1 PostgreSQL Tables

*Products Table:*

| Column      | Type    | Description       |
| ----------- | ------- | ----------------- |
| product\_id | INT     | Unique identifier |
| name        | TEXT    | Product name      |
| brand       | TEXT    | Product brand     |
| price       | DECIMAL | Product price     |
| main\_image | TEXT    | Image URL         |

*User Interactions Table:*

| Column      | Type      | Description               |
| ----------- | --------- | ------------------------- |
| user\_id    | INT       | User identifier           |
| product\_id | INT       | Product identifier        |
| interaction | TEXT      | Type of interaction       |
| timestamp   | TIMESTAMP | When interaction occurred |

### 5.2 Pinecone Vector Storage

- Stores product embeddings generated from *Sentence Transformers*.
- Enables fast similarity search for related products.

## 6. APIs and Workflows

### 6.1 Related Products API

- Uses *Pinecone* to fetch similar products based on embeddings.

python
@api_view(['GET'])
def related_products(request, product_id):
    query_result = index.query(id=str(product_id), top_k=10)
    products = [match['id'] for match in query_result['matches']]
    return Response({'related_products': get_product_details(products)})


### 6.2 You May Also Like API

- Uses collaborative filtering on *weighted user interactions* to recommend products.

python
@api_view(['GET'])
def you_may_also_like(request, user_id):
    user_history = get_user_interactions(user_id)
    recommendations = generate_collaborative_recommendations(user_history)
    return Response({'recommended_products': recommendations})


### 6.3 Suggested for You API

- Fetches user’s recent interactions and finds similar products from *Pinecone*.

python
@api_view(['GET'])
def generate_recommendations(request, user_id):
    recent_products = get_recent_interactions(user_id)
    recommendations = {}
    for product_id in recent_products:
        similar_products = get_similar_products(product_id)
        for product in similar_products:
            recommendations[product['id']] = max(recommendations.get(product['id'], 0), product['score'])
    product_details = get_product_details(recommendations.keys())
    return Response({'recommended_products': sorted(product_details, key=lambda x: x['hybrid_score'], reverse=True)[:10]})


## 7. Implementation Details

### 7.1 Setting Up PostgreSQL

- Create database tables using Django migrations.
- Populate with initial product data.

### 7.2 Indexing Data in Pinecone

- Generate *product embeddings* using *Sentence Transformers*.
- Store embeddings in Pinecone.

### 7.3 Running the API

sh
# Start Django server
python manage.py runserver


### 7.4 API Endpoints

| Endpoint                               | Method | Description                  |
| -------------------------------------- | ------ | ---------------------------- |
| `/api/related-products/<product_id>/`  | GET    | Fetches related products     |
| /api/hybrid/\<user\_id>/\<product\_id> | GET    | Personalized recommendations |
| `/api/recommendations/<user_id>/`      | GET    | Suggestions based on history |

## 8. Final Thoughts

This AI-powered recommendation system enhances user engagement by providing personalized product suggestions. Future improvements can include *real-time updates*, *multi-modal recommendations*, and *A/B testing* for better performance optimization.

### *Next Steps*

- Deploy system to *AWS*.
- Implement *real-time user feedback* to improve recommendations.
- Extend to *multi-category recommendations* for diverse product types.

