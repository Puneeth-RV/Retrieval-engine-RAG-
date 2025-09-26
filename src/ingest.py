# src/ingest.py
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
import src.config as config

def process_massive_dataset():
    print("Step 1: Initializing the embedding model.")
    embed_model = HuggingFaceEmbedding(model_name=config.EMBED_MODEL_NAME)
    
    print("Step 2: Connecting to Qdrant vector database.")
    client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=config.QDRANT_COLLECTION_NAME
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)


    # Get the list of all files first
    print(f"Step 3: Scanning for files in {config.DATA_PATH}...")
    file_paths = []
    for root, dirs, files in os.walk(config.DATA_PATH):
        for file in files:
            if file.endswith(('.txt', '.json')):
                full_path = os.path.join(root, file)
                file_paths.append(full_path)

    print(f"Found {len(file_paths)} files to process.")
    
    # BATCHING - 5000 files at a time
    batch_size = 5000 
    text_splitter = SentenceSplitter(chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP)

    for i in range(0, len(file_paths), batch_size):
        batch_files = file_paths[i:i + batch_size]

        documents = SimpleDirectoryReader(
            input_files=batch_files
        ).load_data()
        
        nodes = text_splitter.get_nodes_from_documents(documents)
        
        # Create index for this batch
        index = VectorStoreIndex(
            nodes,
            storage_context=storage_context,
            embed_model=embed_model,
            show_progress=True
        )
        print(f"Completed batch {i//batch_size + 1}")

    print("All data has been ingested into Qdrant!")

if __name__ == "__main__":
    process_massive_dataset()