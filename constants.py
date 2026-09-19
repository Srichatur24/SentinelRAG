# clearence levels
CLASSIFICATION_LEVELS = ["Public", "Internal", "Confidential", "Restricted"]

# mogodb constants
MONGO_CLIENT = 'mongodb://pragyaan-mongo:27017/'
DATABASE_NAME = 'sentinelrag'
USERS_COLLECTION = 'users'

# openai constants
EMBEDDING_MODEL = "text-embedding-3-small"
AGENT_MODEL = "gpt-5-nano"

# chroma constants
CHROMA_PATH = "./chroma_store"
CHROMA_COLLECTION_NAME = "sentinelrag_documents"

K = 8