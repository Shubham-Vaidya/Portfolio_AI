
from rag import retrieve_context, close_qdrant_client


if __name__ == "__main__":

    try:
        query = "What programming languages does the candidate know?"

        print("Query:", query)

        context = retrieve_context(query, top_k=4)

        print("\nRetrieved Context:")
        print(context)

    finally:
        close_qdrant_client()
