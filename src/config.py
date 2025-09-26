# Data Paths - WHERE TO FIND THE FILES
DATA_PATH = "./data/test_train"  # dataset path

# Embedding Model 
EMBED_MODEL_NAME = "BAAI/bge-large-en-v1.5"

# Qdrant Database 
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLLECTION_NAME = "my_retrieval_engine"

# Chunking 
CHUNK_SIZE = 512             # The size of each text chunk. You will experiment with this.
CHUNK_OVERLAP = 50           # How much chunks overlap. Helps avoid splitting ideas in half.

# Retrieval Settings - HOW MANY RESULTS TO GET
TOP_K = 5                    # Number of top results to retrieve for a query