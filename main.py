import asyncio
import logging
from dotenv import load_dotenv
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli, llm, AgentSession
from livekit.plugins import openai, silero

from agent_tools import AgentTools

load_dotenv()
logger = logging.getLogger("voice-agent")

async def entrypoint(ctx: JobContext):
    # Initialize the system prompt and tools
    initial_ctx = llm.ChatContext()
    initial_ctx.add_message(
        role="system",
        content=(
            "You are an Agentic AI Voice Bot created using the LiveKit framework. "
            "Your interface with users will be voice. "
            "You can manage the user's Google Keep, Calendar, and Gmail using the provided tools. "
            "Keep your responses short and concise, suitable for voice conversation. "
            "Avoid using unpronounceable punctuation or markdown."
        ),
    )

    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Initialize the AgentTools (which inherits from Agent in 1.x)
    agent = AgentTools(
        instructions="You are an Agentic AI Voice Bot. Manage notes, calendar, and email based on user commands.",
        chat_ctx=initial_ctx,
    )

    # Build the AgentSession with VAD, STT, LLM, and TTS
    session = AgentSession(
        vad=silero.VAD.load(),
        stt=openai.STT(),
        llm=openai.LLM(model="gpt-4o"),
        tts=openai.TTS(),
    )

    # Start the session in the connected room
    await session.start(agent=agent, room=ctx.room)

    # Greet the user using the session.say interface
    await asyncio.sleep(1)
    session.say("Hi there! I am your AI voice assistant. I can help you manage your Google Notes, Calendar, and Gmail. What would you like to do?", allow_interruptions=True)

if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))