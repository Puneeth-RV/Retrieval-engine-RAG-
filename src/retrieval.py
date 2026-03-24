# retrieval.py
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import VectorStoreIndex
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
import json
import os
import zipfile
import sys
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
        embed_model=embed_model
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

def process_all_queries():
    """
    Process all queries from Queries.json and create individual JSON files
    """
    print("🚀 Starting mock competition query processing...")
    
    # Read the queries file
    with open(config.QUERIES_FILE, 'r', encoding='utf-8') as f:
        queries_data = json.load(f)
    
    queries_data = queries_data[:100]
    print(f"📝 Found {len(queries_data)} queries to process")
    
    # Ensure outputs directory exists
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    
    # Process each query
    for i, query_item in enumerate(queries_data):
        query_num = query_item["query_num"]
        query_text = query_item["query"]
        
        print(f"Processing query {i+1}/{len(queries_data)}: {query_text[:50]}...")
        
        # Get source files for this query
        source_files = retrieve_source_files(query_text)
        
        # Create the output JSON structure
        output_data = {
            "query": query_text,
            "response": source_files
        }
        
        # Save individual JSON file
        output_filename = f"query_{query_num}.json"
        output_path = os.path.join(config.OUTPUT_DIR, output_filename)
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=4)
    
    print(f"✅ All {len(queries_data)} query files created in {config.OUTPUT_DIR}")

def create_submission_zip():
    """
    Create the final submission zip file
    """
    print("📦 Creating submission zip file...")
    
    # Ensure submissions directory exists
    os.makedirs(config.SUBMISSION_DIR, exist_ok=True)
    
    zip_filename = f"PS04_{config.TEAM_NAME}.zip"
    zip_path = os.path.join(config.SUBMISSION_DIR, zip_filename)
    
    # Create zip file with all JSON files from outputs directory
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for json_file in os.listdir(config.OUTPUT_DIR):
            if json_file.endswith('.json'):
                json_path = os.path.join(config.OUTPUT_DIR, json_file)
                zipf.write(json_path, json_file)
    
    print(f"✅ Submission zip created: {zip_path}")

if __name__ == "__main__":
    # Process all queries and create submission
    process_all_queries()
    create_submission_zip()
    print("🎉 Mock competition submission ready!")