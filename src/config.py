# Data Paths - WHERE TO FIND THE FILES
DATA_PATH = "./data/test_train"  # dataset path

# Embedding Model - OPTIMIZED FOR PERFORMANCE
EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"  # 3x faster than large model with minimal quality loss

# Qdrant Database 
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLLECTION_NAME = "Aura_engine"

# Chunking 
CHUNK_SIZE = 512             # The size of each text chunk. You will experiment with this.
CHUNK_OVERLAP = 50           # How much chunks overlap. Helps avoid splitting ideas in half.

# Retrieval Settings - HOW MANY RESULTS TO GET
TOP_K = 5                    # Number of top results to retrieve for a query

# BATCHING OPTIMIZED FOR 16GB RAM - NEW SETTING
BATCH_SIZE = 2000            # Increased batch size - your 16GB RAM can handle larger batches

# Performance Optimization Settings - NEW
MAX_WORKERS = 4              # Utilize your 4 cores effectively
SHOW_PROGRESS = True         # Enable progress bars