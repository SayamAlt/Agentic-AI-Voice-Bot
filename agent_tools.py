import logging
import sqlite3
from livekit.agents import llm, Agent, RunContext

import google_auth

logger = logging.getLogger(__name__)

class AgentTools(Agent):
    def __init__(self, *, instructions: str, chat_ctx: llm.ChatContext):
        super().__init__(instructions=instructions, chat_ctx=chat_ctx)
        self.calendar_service = google_auth.get_calendar_service()
        self.gmail_service = google_auth.get_gmail_service()
        self._init_db()

    def _init_db(self):
        try:
            self.conn = sqlite3.connect('notes.db', check_same_thread=False)
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT UNIQUE,
                    content TEXT
                )
            ''')
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize SQLite notes DB: {e}")

    # Note tool
    @llm.function_tool()
    async def create_note(
        self,
        ctx: RunContext,
        title: str,
        content: str
    ) -> str:
        """Create a new note.

        Args:
            title: Title of the note
            content: Content/body of the note
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
            self.conn.commit()
            return f"Note created successfully with title '{title}'."
        except sqlite3.IntegrityError:
            return f"A note with the title '{title}' already exists. Please choose a different title or edit the existing one."
        except Exception as e:
            logger.error(f"Error creating note: {e}")
            return f"Failed to create note: {str(e)}"

    @llm.function_tool()
    async def read_all_notes(self, ctx: RunContext) -> str:
        """List all notes."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT title, content FROM notes")
            rows = cursor.fetchall()
            if not rows:
                return "No notes found."
            
            output = []
            for title, content in rows:
                preview = content[:50] + '...' if len(content) > 50 else content
                output.append(f"Title: {title}, Preview: {preview}")
            return "\n".join(output)
        except Exception as e:
            logger.error(f"Error reading notes: {e}")
            return f"Failed to read notes: {str(e)}"

    @llm.function_tool()
    async def delete_note(
        self,
        ctx: RunContext,
        title: str
    ) -> str:
        """Delete a note by title.

        Args:
            title: The exact title of the note to delete
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM notes WHERE LOWER(title) = LOWER(?)", (title,))
            if cursor.rowcount == 0:
                return f"Note with title '{title}' not found."
            self.conn.commit()
            return f"Note '{title}' deleted successfully."
        except Exception as e:
            logger.error(f"Error deleting note: {e}")
            return f"Failed to delete note: {str(e)}"

    @llm.function_tool()
    async def edit_note(
        self,
        ctx: RunContext,
        title: str,
        new_content: str
    ) -> str:
        """Edit/append to a note by title.

        Args:
            title: The exact title of the note to edit
            new_content: The new content to append or replace
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT content FROM notes WHERE LOWER(title) = LOWER(?)", (title,))
            row = cursor.fetchone()
            if not row:
                return f"Note with title '{title}' not found."
            
            old_content = row[0]
            updated_content = f"{old_content}\n{new_content}"
            cursor.execute("UPDATE notes SET content = ? WHERE LOWER(title) = LOWER(?)", (updated_content, title))
            self.conn.commit()
            return f"Note '{title}' updated successfully by appending new content."
        except Exception as e:
            logger.error(f"Error editing note: {e}")
            return f"Failed to edit note: {str(e)}"

    # Google Calendar tool
    @llm.function_tool()
    async def create_meeting(
        self,
        ctx: RunContext,
        title: str,
        date: str,
        time_start: str,
        time_end: str,
        guests: list[str]
    ) -> str:
        """Create a calendar meeting.

        Args:
            title: Meeting title
            date: Date in YYYY-MM-DD format
            time_start: Start time in HH:MM:SS format (24-hour)
            time_end: End time in HH:MM:SS format (24-hour)
            guests: List of guest email addresses
        """
        try:
            if not self.calendar_service:
                return "Calendar service not available."
            
            attendees = [{'email': email} for email in guests]
            start_datetime = f"{date}T{time_start}-00:00"
            end_datetime = f"{date}T{time_end}-00:00"
            
            event = {
                'summary': title,
                'start': {'dateTime': start_datetime, 'timeZone': 'UTC'},
                'end': {'dateTime': end_datetime, 'timeZone': 'UTC'},
                'attendees': attendees
            }
            
            created_event = self.calendar_service.events().insert(calendarId='primary', body=event).execute()
            return f"Meeting '{title}' created successfully at {start_datetime}."
        except Exception as e:
            logger.error(f"Error creating meeting: {e}")
            return f"Failed to create meeting: {str(e)}"

    @llm.function_tool()
    async def fetch_all_meetings(self, ctx: RunContext) -> str:
        """Fetch upcoming calendar meetings."""
        try:
            import datetime
            if not self.calendar_service:
                return "Calendar service not available."
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = self.calendar_service.events().list(
                calendarId='primary', timeMin=now, maxResults=10, singleEvents=True, orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            
            if not events:
                return "No upcoming meetings found."
            
            output = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                summary = event.get('summary', 'No Title')
                attendees = [a.get('email') for a in event.get('attendees', [])]
                output.append(f"Meeting '{summary}' at {start} with {', '.join(attendees) if attendees else 'no guests'}.")
            return "\n".join(output)
        except Exception as e:
            logger.error(f"Error fetching meetings: {e}")
            return f"Failed to fetch meetings: {str(e)}"

    @llm.function_tool()
    async def delete_meeting(
        self,
        ctx: RunContext,
        title: str
    ) -> str:
        """Delete a calendar meeting by title.

        Args:
            title: The exact title of the meeting to delete
        """
        try:
            import datetime
            if not self.calendar_service:
                return "Calendar service not available."
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = self.calendar_service.events().list(
                calendarId='primary', timeMin=now, maxResults=50, singleEvents=True, orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            
            for event in events:
                if event.get('summary', '').lower() == title.lower():
                    self.calendar_service.events().delete(calendarId='primary', eventId=event['id']).execute()
                    return f"Meeting '{title}' deleted successfully."
            
            return f"Meeting '{title}' not found."
        except Exception as e:
            logger.error(f"Error deleting meeting: {e}")
            return f"Failed to delete meeting: {str(e)}"

    @llm.function_tool()
    async def edit_meeting(
        self,
        ctx: RunContext,
        title: str,
        new_title: str = "",
        new_date: str = ""
    ) -> str:
        """Edit a calendar meeting.

        Args:
            title: The exact title of the meeting to edit
            new_title: New title for the meeting, or empty string if unchanged
            new_date: New date in YYYY-MM-DD format, or empty string if unchanged
        """
        try:
            import datetime
            if not self.calendar_service:
                return "Calendar service not available."
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = self.calendar_service.events().list(
                calendarId='primary', timeMin=now, maxResults=50, singleEvents=True, orderBy='startTime'
            ).execute()
            events = events_result.get('items', [])
            
            for event in events:
                if event.get('summary', '').lower() == title.lower():
                    if new_title:
                        event['summary'] = new_title
                    if new_date:
                        old_start = event['start'].get('dateTime', '')
                        if 'T' in old_start:
                            time_part = old_start.split('T')[1]
                            event['start']['dateTime'] = f"{new_date}T{time_part}"
                        old_end = event['end'].get('dateTime', '')
                        if 'T' in old_end:
                            time_part = old_end.split('T')[1]
                            event['end']['dateTime'] = f"{new_date}T{time_part}"
                            
                    self.calendar_service.events().update(calendarId='primary', eventId=event['id'], body=event).execute()
                    return f"Meeting '{title}' updated successfully."
                    
            return f"Meeting '{title}' not found."
        except Exception as e:
            logger.error(f"Error editing meeting: {e}")
            return f"Failed to edit meeting: {str(e)}"

    # Gmail tool
    @llm.function_tool()
    async def read_all_emails(self, ctx: RunContext) -> str:
        """Read recent emails from Gmail."""
        try:
            if not self.gmail_service:
                return "Gmail service not available."
            results = self.gmail_service.users().messages().list(userId='me', maxResults=5).execute()
            messages = results.get('messages', [])
            
            if not messages:
                return "No recent emails found."
            
            output = []
            for msg in messages:
                msg_full = self.gmail_service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['Subject', 'From']).execute()
                headers = msg_full.get('payload', {}).get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                snippet = msg_full.get('snippet', '')
                output.append(f"From: {sender}, Subject: {subject}, Snippet: {snippet}")
                
            return "\n".join(output)
        except Exception as e:
            logger.error(f"Error reading emails: {e}")
            return f"Failed to read emails: {str(e)}"

    @llm.function_tool()
    async def create_draft(
        self,
        ctx: RunContext,
        recipient: str,
        subject: str,
        body: str
    ) -> str:
        """Create an email draft.

        Args:
            recipient: Email address of the recipient
            subject: Subject of the email
            body: Body of the email
        """
        try:
            import base64
            from email.message import EmailMessage
            
            if not self.gmail_service:
                return "Gmail service not available."
                
            message = EmailMessage()
            message.set_content(body)
            message['To'] = recipient
            message['Subject'] = subject
            
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {'message': {'raw': encoded_message}}
            
            draft = self.gmail_service.users().drafts().create(userId='me', body=create_message).execute()
            return f"Draft created successfully for '{recipient}' with subject '{subject}'."
        except Exception as e:
            logger.error(f"Error creating draft: {e}")
            return f"Failed to create draft: {str(e)}"