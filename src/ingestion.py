# src/ingestion.py
import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from llama_index.core import SimpleDirectoryReader, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from tqdm import tqdm
import src.config as config

def optimize_windows_performance():
    """Increase process priority for better performance"""
    try:
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x00008000)
        print("Process priority optimized")
    except:
        print("Could not adjust process priority (continuing anyway)")

def process_massive_dataset():
    optimize_windows_performance()
    
    print("Starting Data Ingestion Process on Dell Latitude 5410")
    print("=" * 50)
    
    start_time = time.time()
    
    # Step 1: Initialize embedding model
    print("Step 1: Initializing the embedding model...")
    embed_model = HuggingFaceEmbedding(model_name=config.EMBED_MODEL_NAME)
    
    # Step 2: Connect to Qdrant
    print("Step 2: Connecting to Qdrant vector database...")
    client = QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT)
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=config.QDRANT_COLLECTION_NAME
    )
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Step 3: Scan for files
    print("Step 3: Scanning for files...")
    file_paths = []
    for root, dirs, files in os.walk(config.DATA_PATH):
        for file in files:
            if file.endswith(('.txt', '.json', '.pdf')):
                full_path = os.path.join(root, file)
                file_paths.append(full_path)

    print(f"Found {len(file_paths)} files to process.")
    
    if len(file_paths) == 0:
        print("No files found! Check your DATA_PATH configuration.")
        return

    # Step 4: Batching with optimized size
    batch_size = getattr(config, 'BATCH_SIZE', 2000)  # Use config value or default to 2000
    text_splitter = SentenceSplitter(chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP)
    
    total_batches = (len(file_paths) + batch_size - 1) // batch_size
    total_nodes_processed = 0
    total_docs_processed = 0
    
    print(f"Step 4: Processing {len(file_paths)} files in {total_batches} batches (batch size: {batch_size})")
    print("Starting batch processing...")
    
    # Main processing loop with progress tracking
    for batch_num in range(total_batches):
        batch_start_time = time.time()
        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, len(file_paths))
        batch_files = file_paths[start_idx:end_idx]
        
        print(f"Batch {batch_num + 1}/{total_batches}: Processing {len(batch_files)} files...")
        
        try:
            # Load documents for this batch
            documents = SimpleDirectoryReader(input_files=batch_files).load_data()
            total_docs_processed += len(documents)
            
            # Create nodes for this batch
            nodes = text_splitter.get_nodes_from_documents(documents)
            total_nodes_processed += len(nodes)
            
            # Create index for this batch
            index = VectorStoreIndex(
                nodes,
                storage_context=storage_context,
                embed_model=embed_model,
                show_progress=True
            )
            
            batch_time = time.time() - batch_start_time
            files_per_second = len(batch_files) / batch_time
            
            # Calculate ETA
            elapsed_time = time.time() - start_time
            batches_remaining = total_batches - (batch_num + 1)
            eta_seconds = (elapsed_time / (batch_num + 1)) * batches_remaining if batch_num > 0 else 0
            
            print(f"Batch {batch_num + 1} completed: {len(documents)} docs -> {len(nodes)} chunks "
                  f"({batch_time:.1f}s, {files_per_second:.1f} files/sec)")
            print(f"Progress: {total_docs_processed} docs, {total_nodes_processed} chunks | "
                  f"ETA: {eta_seconds/3600:.1f} hours remaining")
            print("-" * 40)
            
            # Clean up memory
            del documents
            del nodes
            
        except Exception as e:
            print(f"Error in batch {batch_num + 1}: {e}")
            print("Skipping batch and continuing...")
            continue

    total_time = time.time() - start_time
    print("=" * 50)
    print("Data ingestion completed successfully!")
    print(f"Summary:")
    print(f"- Total files processed: {len(file_paths)}")
    print(f"- Total documents: {total_docs_processed}")
    print(f"- Total chunks created: {total_nodes_processed}")
    print(f"- Total time: {total_time/3600:.2f} hours")
    print(f"- Collection: {config.QDRANT_COLLECTION_NAME}")
    print("=" * 50)

if __name__ == "__main__":
    process_massive_dataset()