import pinecone
import uuid
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
            # The new Pinecone client (v3+) is initialized this way.
            # The 'environment' is now handled by the project settings in your Pinecone account.
            pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
            self.index_name = index_name
            self.index = pc.Index(self.index_name)
            print("Pinecone index loaded.")
        except Exception as e:
            print(f"Failed to initialize Pinecone or connect to index: {e}")
            self.index = None

    def store_memory(self, bot_name: str, memory_text: str, memory_vector: list):
        """Stores a memory vector for a specific bot."""
        if self.index is None: return

        # pinecone.utils.random_id() is deprecated. Use uuid instead.
        memory_id = f"{bot_name}-{str(uuid.uuid4())}"

        # The upsert format has changed in v3+. It now takes a list of dictionaries.
        self.index.upsert(
            vectors=[{'id': memory_id, 'values': memory_vector, 'metadata': {"bot": bot_name, "text": memory_text}}],
            namespace=bot_name
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