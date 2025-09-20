# test_vectors.py
from vector_store import DroneCommandVectorStore
import os

def test_search():
    store = DroneCommandVectorStore()
    
    # First check if the vector store exists, if not create it
    if not os.path.exists("./drone_commands_db"):
        print("Creating vector database from tello.txt...")
        num_chunks = store.create_from_tello_commands("tello.txt")
        print(f"Vector database created with {num_chunks} command chunks")
    
    test_queries = [
        "How do I make the drone takeoff?",
        "I want the drone to move forward",
        "How do I make the drone rotate?",
        "Can the drone flip?"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: {query}")
        results = store.similarity_search(query, k=5)
        print("Results:")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result}")

if __name__ == "__main__":
    test_search()