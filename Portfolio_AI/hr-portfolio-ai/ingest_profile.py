
from candidate_profile import profile
from rag import index_profile, close_qdrant_client


if __name__ == "__main__":

    print("Starting candidate profile ingestion...")

    try:
        count = index_profile(profile)

        print(f"Successfully indexed {count} profile chunks.")
        print("Candidate profile is now stored in Qdrant.")

    finally:
        close_qdrant_client()
