
import os
from pathlib import Path
from uuid import uuid5, uuid4, NAMESPACE_URL

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    FilterSelector,
    PayloadSchemaType,
)


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

QDRANT_PATH = BASE_DIR / "qdrant_storage"

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

PROFILE_COLLECTION = "candidate_profile"
JD_COLLECTION = "job_descriptions"

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

VECTOR_SIZE = 384

_embedding_model = None
_qdrant_client = None


# ============================================================
# MODEL AND QDRANT CLIENT
# ============================================================

def get_embedding_model():

    global _embedding_model

    if _embedding_model is None:
        _embedding_model = SentenceTransformer(
            EMBEDDING_MODEL_NAME
        )

    return _embedding_model


def get_qdrant_client():

    global _qdrant_client

    if _qdrant_client is None:

        if QDRANT_URL:
            # Connect to Qdrant Cloud
            if not QDRANT_API_KEY:
                raise ValueError(
                    "QDRANT_API_KEY is required when QDRANT_URL is configured."
                )

            _qdrant_client = QdrantClient(
                url=QDRANT_URL,
                api_key=QDRANT_API_KEY,
                timeout=30,
            )

        else:
            # Local development fallback
            _qdrant_client = QdrantClient(
                path=str(QDRANT_PATH)
            )

    return _qdrant_client


# ============================================================
# PROFILE PROCESSING
# ============================================================

def format_value(value):

    if isinstance(value, list):
        return ", ".join(str(item) for item in value)

    if isinstance(value, dict):
        return ", ".join(
            f"{key}: {format_value(val)}"
            for key, val in value.items()
        )

    return str(value)


def profile_to_documents(profile):

    documents = []

    for section, value in profile.items():

        if isinstance(value, list):

            for index, item in enumerate(value):

                if isinstance(item, dict):
                    details = "\n".join(
                        f"{key}: {format_value(val)}"
                        for key, val in item.items()
                    )
                else:
                    details = format_value(item)

                documents.append({
                    "id": f"{section}-{index}",
                    "category": section,
                    "text": f"Category: {section}\n{details}",
                })

        elif isinstance(value, dict):

            details = "\n".join(
                f"{key}: {format_value(val)}"
                for key, val in value.items()
            )

            documents.append({
                "id": section,
                "category": section,
                "text": f"Category: {section}\n{details}",
            })

        else:

            documents.append({
                "id": section,
                "category": section,
                "text": f"Category: {section}\n{value}",
            })

    return documents


# ============================================================
# COLLECTION MANAGEMENT
# ============================================================

def ensure_collection(collection_name):

    client = get_qdrant_client()

    if not client.collection_exists(collection_name):

        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )

def ensure_jd_session_index():

    client = get_qdrant_client()

    collection_info = client.get_collection(JD_COLLECTION)

    if "session_id" not in collection_info.payload_schema:

        client.create_payload_index(
            collection_name=JD_COLLECTION,
            field_name="session_id",
            field_schema=PayloadSchemaType.KEYWORD,
            wait=True,
        )

        print("Created Qdrant payload index: session_id")

def create_collection(reset=False):

    client = get_qdrant_client()

    if client.collection_exists(PROFILE_COLLECTION):

        if not reset:
            return

        client.delete_collection(PROFILE_COLLECTION)

    ensure_collection(PROFILE_COLLECTION)


# ============================================================
# CANDIDATE PROFILE INGESTION
# ============================================================

def index_profile(profile):

    documents = profile_to_documents(profile)

    if not documents:
        raise ValueError("Candidate profile is empty.")

    model = get_embedding_model()
    client = get_qdrant_client()

    create_collection(reset=True)

    texts = [
        document["text"]
        for document in documents
    ]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
    )

    points = []

    for document, embedding in zip(documents, embeddings):

        point_id = str(
            uuid5(
                NAMESPACE_URL,
                f'{document["id"]}:{document["text"]}',
            )
        )

        points.append(
            PointStruct(
                id=point_id,
                vector=embedding.tolist(),
                payload={
                    "text": document["text"],
                    "category": document["category"],
                    "source": "candidate_profile",
                },
            )
        )

    client.upsert(
        collection_name=PROFILE_COLLECTION,
        points=points,
        wait=True,
    )

    return len(points)


# ============================================================
# CANDIDATE PROFILE RETRIEVAL
# ============================================================

def retrieve_context(query, top_k=4):

    model = get_embedding_model()
    client = get_qdrant_client()

    if not client.collection_exists(PROFILE_COLLECTION):
        raise RuntimeError(
            "Candidate profile collection not found. "
            "Run ingest_profile.py first."
        )

    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    results = client.query_points(
        collection_name=PROFILE_COLLECTION,
        query=query_embedding,
        limit=top_k,
        with_payload=True,
    ).points

    context = []

    for result in results:

        payload = result.payload or {}

        context.append(
            f'[Category: {payload.get("category", "Unknown")}]\n'
            f'{payload.get("text", "")}'
        )

    return "\n\n".join(context)


# ============================================================
# JOB DESCRIPTION INGESTION
# ============================================================

def index_job_description(chunks, session_id):

    if not chunks:
        raise ValueError("No JD chunks available for indexing.")

    model = get_embedding_model()
    client = get_qdrant_client()

    ensure_collection(JD_COLLECTION)

    # Required for filtering JD chunks by session_id
    ensure_jd_session_index()

    # Remove the previous JD for this session, if any
    # Delete the previous JD belonging to this session
    client.delete(
        collection_name=JD_COLLECTION,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id),
                    )
                ]
            )
        ),
        wait=True,
    )

    embeddings = model.encode(
        chunks,
        normalize_embeddings=True,
    )

    points = []

    for index, (chunk, embedding) in enumerate(
        zip(chunks, embeddings)
    ):

        points.append(
            PointStruct(
                id=str(uuid4()),
                vector=embedding.tolist(),
                payload={
                    "text": chunk,
                    "source": "job_description",
                    "session_id": session_id,
                    "chunk_index": index,
                },
            )
        )

    client.upsert(
        collection_name=JD_COLLECTION,
        points=points,
        wait=True,
    )

    return len(points)


# ============================================================
# JOB DESCRIPTION RETRIEVAL
# ============================================================

def retrieve_jd_context(query, session_id, top_k=5):

    model = get_embedding_model()
    client = get_qdrant_client()

    if not client.collection_exists(JD_COLLECTION):
        return ""

    query_embedding = model.encode(
        query,
        normalize_embeddings=True,
    ).tolist()

    results = client.query_points(
        collection_name=JD_COLLECTION,
        query=query_embedding,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="session_id",
                    match=MatchValue(value=session_id),
                )
            ]
        ),
        limit=top_k,
        with_payload=True,
    ).points

    context = []

    for result in results:

        payload = result.payload or {}

        context.append(
            payload.get("text", "")
        )

    return "\n\n".join(context)


# ============================================================
# CONNECTION TEST
# ============================================================

def test_qdrant_connection():

    client = get_qdrant_client()

    collections = client.get_collections()

    print("Qdrant connection successful!")

    print("Available collections:")

    for collection in collections.collections:
        print(f"- {collection.name}")


# ============================================================
# CLIENT CLEANUP
# ============================================================

def close_qdrant_client():

    global _qdrant_client

    if _qdrant_client is not None:

        _qdrant_client.close()

        _qdrant_client = None
