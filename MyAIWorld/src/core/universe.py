import pinecone
from discord.ext import commands
from src.config import PINECONE_API_KEY, PINECONE_ENVIRONMENT

class UniverseClient(commands.Cog):
    """
    Client for interacting with the Pinecone vector database,
    which serves as the long-term memory for the bots.
    """
    def __init__(self, bot, index_name="my-ai-world"):
        self.bot = bot
        if not all([PINECONE_API_KEY, PINECONE_ENVIRONMENT]):
            print("WARNING: Pinecone credentials not set. Long-term memory will be disabled.")
            self.index = None
            return
            
        try:
            pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
            self.index_name = index_name
            self.index = None
            self._initialize_index()
        except Exception as e:
            print(f"Failed to initialize Pinecone: {e}")
            self.index = None

    def _initialize_index(self):
        """Initializes the Pinecone index, creating it if it doesn't exist."""
        if self.index_name not in pinecone.list_indexes():
            print(f"Creating Pinecone index '{self.index_name}'...")
            # Dimension must match the embedding model. 768 is common for sentence-transformers.
            pinecone.create_index(self.index_name, dimension=768, metric="cosine")
        
        self.index = pinecone.Index(self.index_name)
        print("Pinecone index loaded.")

    def store_memory(self, bot_name: str, memory_text: str, memory_vector: list):
        """Stores a memory vector for a specific bot."""
        if self.index is None: return

        # Using a UUID for a unique memory ID
        memory_id = f"{bot_name}-{pinecone.utils.random_id()}"
        
        self.index.upsert(
            vectors=[(memory_id, memory_vector, {"bot": bot_name, "text": memory_text})],
            namespace=bot_name # Use namespaces to separate memories per bot
        )
        print(f"Stored memory for {bot_name}.")

    def recall_memories(self, bot_name: str, query_vector: list, top_k: int = 5):
        """Recalls the most relevant memories for a bot based on a query vector."""
        if self.index is None: return []

        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            namespace=bot_name,
            include_metadata=True
        )
        
        return [match['metadata']['text'] for match in results['matches']]

async def setup(bot):
    """Adds the universe client to the bot."""
    bot.universe_client = UniverseClient(bot)
    await bot.add_cog(bot.universe_client)