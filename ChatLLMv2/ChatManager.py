import logging
import sqlalchemy.orm as so
from uuid import uuid4
from .ChatRecord import ChatRecord


logger = logging.getLogger(__name__)


class ChatManager:

    def __init__(self,
                 database_session: so.Session,
                 chatId: str = str(uuid4()),
                 ) -> None:
        logger.info("Initializing ChatManager")

        logger.debug("Checking Database Table Existance")
        try:
            self.dbSession = database_session
            self.dbSession.query(ChatRecord).first()
        except:
            error = "Database does not exist or incomplete, exiting"
            logger.error(error)
            raise Exception(error)

        logger.debug(f"Check Database for {chatId=}")
        existingChat = self.dbSession.query(ChatRecord).filter(ChatRecord.chatId == chatId).first()

        if existingChat is not None:
            logger.info(f"Found ChatID: {chatId} in database. Using existing.")
            self.chat = existingChat
            return

        logger.info(f"ChatID: {chatId} not found in database. Initlizing new chat")
        self.chat = ChatRecord()
        self.chat.chatId = chatId
        self.dbSession.add(self.chat)
        self.dbSession.commit()
