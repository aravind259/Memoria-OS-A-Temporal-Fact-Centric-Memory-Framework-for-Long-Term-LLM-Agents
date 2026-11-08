from app.db.database import SessionLocal
from app.db.models import Conversation


class ConversationService:

    def save(self, user_message: str, ai_response: str):

        db = SessionLocal()

        try:
            conversation = Conversation(
                user_message=user_message,
                ai_response=ai_response
            )

            db.add(conversation)
            db.commit()

        finally:
            db.close()