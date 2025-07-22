#=======================================================================================
# Adaptación de herramienta para el obtener un correo con sus  archivos adjuntos y que soporte charset diferentes a UTF-8.
# (daba error con algunos correos enviados desde windows que no usan utf-8)
# Se baso en las clases del GMail Toolkit del paquete langchain-comunity
# (https://github.com/langchain-ai/langchain-community/blob/main/libs/community/langchain_community/tools/gmail/get_message.py)
#=======================================================================================
import email
from typing import Dict, Optional, Type
import base64

from langchain_core.callbacks import CallbackManagerForToolRun
from pydantic import BaseModel, Field

from langchain_community.tools.gmail.base import GmailBaseTool
from langchain_community.tools.gmail.utils import clean_email_body

class SearchArgsSchema(BaseModel):
    """Input for GetMessageTool."""

    message_id: str = Field(
        ...,
        description="The unique ID of the email message, retrieved from a search.",
    )
    must_save_attachments: bool = Field(
        ...,
        description="True for save attachments",
    )
    attachments_root_path: str = Field(
        ...,
        description="Root folder for save attachments(whitout message_id), None if not must save attachments",
    )


class GmailGetMessageWithAttachments(GmailBaseTool):  # type: ignore[override, override]
    """
    Tool that gets a message and save attachments
    the attachments are saved in a root folder, within a subfolder with same name as ID

    Args:
        message_id: ID from GMail
        must_save_attachments: True for save attachments
        attachments_root_path: root folder for save attachments (whitout message_id)
        run_manager: Optional, not send
    """

    name: str = "get_gmail_message_with_attachments"
    description: str = (
        """Use this tool to fetch an email with attachments by message ID
        Returns the thread ID, snippet, body, subject, sender, date, attachments."""
    )
    args_schema: Type[SearchArgsSchema] = SearchArgsSchema

    def _run(
        self,
        message_id: str,
        must_save_attachments: bool = False,
        attachments_root_path: str = "./attachments",
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> Dict:
        """Run the tool."""
        query = (
            self.api_resource.users()
            .messages()
            .get(userId="me", format="raw", id=message_id)
        )
        message_data = query.execute()
        raw_message = base64.urlsafe_b64decode(message_data["raw"])

        email_msg = email.message_from_bytes(raw_message)

        from email.utils import parsedate_to_datetime

        subject = email_msg["Subject"]
        sender = email_msg["From"]
        date = parsedate_to_datetime(email_msg["Date"]).strftime("%Y-%m-%d %H:%M:%S")

        message_body = ""
        attachments = []
        if email_msg.is_multipart():
            for part in email_msg.walk():
                ctype = part.get_content_type()
                cdispo = str(part.get("Content-Disposition"))
                if "attachment" in cdispo:
                    file_name=part.get_filename()
                    attachments.append({"file_name":file_name,
                                        "content_type":part.get_content_type()})
                    if must_save_attachments:
                        self._save_file(attachments_root_path+"/"+message_id, file_name, part.get_payload())
                elif not message_body and ctype == "text/plain" and "attachment" not in cdispo:
                    message_body = part.get_payload(decode=True).decode(part.get_content_charset())  # type: ignore[union-attr]
        else:
            message_body = email_msg.get_payload(decode=True).decode(part.get_content_charset())  # type: ignore[union-attr]

        body = clean_email_body(message_body)
        
        return {
            "id": message_id,
            "threadId": message_data["threadId"],
            "snippet": message_data["snippet"],
            "body": body,
            "subject": subject,
            "sender": sender,
            "date": date,
            "attachments": attachments,
        }
        
    def _save_file(self, folder: str, file_name: str, base64_content: str):
        import os
        from pathlib import Path

        # Convert the base64 content to bytes
        content_bytes = base64.b64decode(base64_content)

        # Create the folder if it doesn't exist
        folder_path = Path(folder)
        folder_path.mkdir(parents=True, exist_ok=True)

        # Save the file
        file_path = folder_path / file_name
        with open(file_path, 'wb') as f:
            f.write(content_bytes)
