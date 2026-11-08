from app.memory.manager import MemoryManager
from app.memory.retriever import MemoryRetriever
from app.memory.storage import MemoryStorage
from app.memory.prompt import PromptBuilder
from app.memory.working_memory import WorkingMemory
from app.memory.scheduler import MemoryLifecycleScheduler
from app.memory.persona import UserPersonaEngine
from app.services.conversation import ConversationService
from app.services.llm import LLMService


working_memory = WorkingMemory()
retriever = MemoryRetriever(working_memory=working_memory)
persona_engine = UserPersonaEngine()

memory_manager = MemoryManager(
    retriever=retriever,
    storage=MemoryStorage(),
    prompt_builder=PromptBuilder(),
    working_memory=working_memory,
    conversation_service=ConversationService(),
    llm_service=LLMService(),
)

lifecycle_scheduler = MemoryLifecycleScheduler(working_memory=working_memory)