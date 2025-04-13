# manage_vectors.py
from vector_store import DroneCommandVectorStore
import argparse

def main():
    parser = argparse.ArgumentParser(description="Manage drone command vector database")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild the vector database")
    parser.add_argument("--file", type=str, default="tello.txt", help="Path to tello commands file")
    
    args = parser.parse_args()
    
    store = DroneCommandVectorStore()
    
    if args.rebuild:
        print(f"Rebuilding vector database from {args.file}...")
        num_chunks = store.create_from_tello_commands(args.file)
        print(f"Vector database created with {num_chunks} command chunks")
    else:
        # Show statistics about the database
        if store.vector_store:
            count = len(store.vector_store.get()["ids"])
            print(f"Vector database contains {count} command chunks")
        else:
            print("Vector database not found")

if __name__ == "__main__":
    main()