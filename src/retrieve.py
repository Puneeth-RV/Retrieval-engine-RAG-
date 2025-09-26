# retrive.py
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import src.config as config

def retrieve_source_files(query):
    """
    This function takes a query, searches the vector database,
    and returns a list of source filenames.
    """

    # Connect to qdrant
    client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    vector_store = QdrantVectorStore(client=client, collection_name=config.QDRANT_COLLECTION_NAME)

    # Initialize the embedding model
    embed_model = HuggingFaceEmbedding(model_name=config.EMBED_MODEL_NAME)
    
    # Load the index FROM THE VECTOR STORE, explicitly providing the embed_model
    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embed_model  # This is the crucial line you're missing
    )

    # Perform retrieval - get top K results based on config
    retriever = index.as_retriever(similarity_top_k=config.TOP_K)
    retrieved_nodes = retriever.retrieve(query)
    
    # Extract source filenames from the metadata of each node
    source_files = []
    for node in retrieved_nodes:
        file_name = node.metadata.get("file_name", "unknown")
        # Avoid duplicates
        if file_name not in source_files:
            source_files.append(file_name)
    
    return source_files

def create_output_json(query, query_id, output_dir="./outputs"):
    """
    Creates the required JSON output for a single query and saves it to a file.
    """
    # Get the source files for the query
    source_files = retrieve_source_files(query)
    
    # JSON output structure 
    output_data = {
        "query": query,
        "response": source_files  # This is the list of filenames
    }
    
    # Ensure the output directory exists
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Save to a file named <query_id>.json
    output_filename = f"{query_id}.json"
    output_path = os.path.join(output_dir, output_filename)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=4)
    
    print(f"Output saved to {output_path}")
    return output_data

if __name__ == "__main__":
    test_query = "ESPN's TOP 10 ALL-TIME ATHLETES starting with letter a"
    test_id = "test_1"
    
    result = create_output_json(test_query, test_id)
    print("Result:", result)

    # <doc_id>-<secondary_id>_<source_name>_<query_or_title>_<chunk_size_or_index>.json