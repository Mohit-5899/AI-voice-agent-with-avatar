import logging
from dotenv import load_dotenv
from livekit.agents import (
    AgentSession,
    JobContext,
    JobProcess,
    MetricsCollectedEvent,
    WorkerOptions,
    cli,
    metrics,
)
from livekit.plugins import deepgram, cartesia, anthropic, silero, tavus
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from agent_definition import AppointmentAgent
from config import TAVUS_REPLICA_ID, TAVUS_PERSONA_ID

load_dotenv()
logger = logging.getLogger("voice-agent")


def prewarm(proc: JobProcess):
    """Pre-load the VAD model for faster startup."""
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    """Main entry point for each voice agent session."""
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=anthropic.LLM(model="claude-sonnet-4-20250514"),
        tts=cartesia.TTS(model="sonic"),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
    )

    # Tavus avatar: captures agent audio, renders lip-synced video
    if TAVUS_REPLICA_ID and TAVUS_PERSONA_ID:
        try:
            avatar = tavus.AvatarSession(
                replica_id=TAVUS_REPLICA_ID,
                persona_id=TAVUS_PERSONA_ID,
            )
            await avatar.start(session, room=ctx.room)
            logger.info("Tavus avatar started successfully")
        except Exception as e:
            logger.warning(f"Tavus avatar failed to start (continuing without avatar): {e}")

    # Metrics logging
    usage_collector = metrics.UsageCollector()

    @session.on("metrics_collected")
    def _on_metrics(ev: MetricsCollectedEvent):
        metrics.log_metrics(ev.metrics)
        usage_collector.collect(ev.metrics)

    async def log_usage():
        summary = usage_collector.get_summary()
        logger.info(f"Usage: {summary}")

    ctx.add_shutdown_callback(log_usage)

    # Start the session with the appointment agent
    await session.start(
        agent=AppointmentAgent(),
        room=ctx.room,
    )


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        )
    )
