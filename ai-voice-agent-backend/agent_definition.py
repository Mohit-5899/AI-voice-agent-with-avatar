import json
import logging
from livekit.agents import Agent, RunContext
from livekit.agents.llm import function_tool
from tools import appointment_tools
from models import ToolCallEvent
from config import SYSTEM_PROMPT, TOOL_CALL_TOPIC, CALL_SUMMARY_TOPIC

logger = logging.getLogger("appointment-agent")


class AppointmentAgent(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    async def on_enter(self):
        """Called when agent starts. Generate initial greeting."""
        self.session.generate_reply()

    async def _publish_tool_event(self, context: RunContext, event: ToolCallEvent):
        """Publish a tool call event to the frontend via data channel."""
        try:
            room = context.session.room
            if room and room.local_participant:
                await room.local_participant.publish_data(
                    payload=event.model_dump_json().encode("utf-8"),
                    reliable=True,
                    topic=TOOL_CALL_TOPIC,
                )
        except Exception as e:
            logger.warning(f"Failed to publish tool event: {e}")

    # ---- Tool 1: Identify User ----
    @function_tool
    async def identify_user(self, context: RunContext, phone_number: str):
        """Identify a user by their phone number. Call this when the user provides their
        phone number at the start of the conversation.

        Args:
            phone_number: The user's phone number (e.g., +1234567890)
        """
        args = {"phone_number": phone_number}
        await self._publish_tool_event(
            context, ToolCallEvent.now("identify_user", "started", args)
        )
        result = await appointment_tools.identify_user_by_phone(phone_number)
        await self._publish_tool_event(
            context, ToolCallEvent.now("identify_user", "completed", args, result)
        )
        return json.dumps(result)

    # ---- Tool 2: Fetch Slots ----
    @function_tool
    async def fetch_slots(self, context: RunContext, preferred_date: str = ""):
        """Fetch available appointment slots. Optionally filter by a specific date.

        Args:
            preferred_date: Optional date in YYYY-MM-DD format to filter slots
        """
        args = {"preferred_date": preferred_date}
        await self._publish_tool_event(
            context, ToolCallEvent.now("fetch_slots", "started", args)
        )
        result = await appointment_tools.fetch_available_slots(preferred_date or None)
        result_summary = {"slots": result[:10], "total_available": len(result)}
        await self._publish_tool_event(
            context, ToolCallEvent.now("fetch_slots", "completed", args, result_summary)
        )
        return json.dumps(result_summary)

    # ---- Tool 3: Book Appointment ----
    @function_tool
    async def book_appointment(
        self,
        context: RunContext,
        phone_number: str,
        patient_name: str,
        appointment_date: str,
        appointment_time: str,
        reason: str = "",
    ):
        """Book a new appointment for the user. Confirm the details with the patient before calling this.

        Args:
            phone_number: The user's phone number
            patient_name: The patient's full name
            appointment_date: Date in YYYY-MM-DD format
            appointment_time: Time in HH:MM format (24-hour)
            reason: Reason for the appointment
        """
        args = {
            "phone_number": phone_number,
            "patient_name": patient_name,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "reason": reason,
        }
        await self._publish_tool_event(
            context, ToolCallEvent.now("book_appointment", "started", args)
        )
        result = await appointment_tools.book_appointment(
            phone_number, patient_name, appointment_date, appointment_time, reason or None
        )
        await self._publish_tool_event(
            context, ToolCallEvent.now("book_appointment", "completed", args, result)
        )
        return json.dumps(result, default=str)

    # ---- Tool 4: Retrieve Appointments ----
    @function_tool
    async def retrieve_appointments(self, context: RunContext, phone_number: str):
        """Retrieve all scheduled appointments for a user.

        Args:
            phone_number: The user's phone number
        """
        args = {"phone_number": phone_number}
        await self._publish_tool_event(
            context, ToolCallEvent.now("retrieve_appointments", "started", args)
        )
        result = await appointment_tools.retrieve_appointments(phone_number)
        result_summary = {"appointments": result, "count": len(result)}
        await self._publish_tool_event(
            context,
            ToolCallEvent.now("retrieve_appointments", "completed", args, result_summary),
        )
        return json.dumps(result_summary, default=str)

    # ---- Tool 5: Cancel Appointment ----
    @function_tool
    async def cancel_appointment(self, context: RunContext, appointment_id: str):
        """Cancel an existing appointment. Confirm with the patient before calling this.

        Args:
            appointment_id: The UUID of the appointment to cancel
        """
        args = {"appointment_id": appointment_id}
        await self._publish_tool_event(
            context, ToolCallEvent.now("cancel_appointment", "started", args)
        )
        result = await appointment_tools.cancel_appointment(appointment_id)
        await self._publish_tool_event(
            context, ToolCallEvent.now("cancel_appointment", "completed", args, result)
        )
        return json.dumps(result, default=str)

    # ---- Tool 6: Modify Appointment ----
    @function_tool
    async def modify_appointment(
        self,
        context: RunContext,
        appointment_id: str,
        new_date: str = "",
        new_time: str = "",
    ):
        """Modify an existing appointment's date and/or time. Confirm with the patient before calling this.

        Args:
            appointment_id: The UUID of the appointment to modify
            new_date: New date in YYYY-MM-DD format (optional)
            new_time: New time in HH:MM format (optional)
        """
        args = {
            "appointment_id": appointment_id,
            "new_date": new_date,
            "new_time": new_time,
        }
        await self._publish_tool_event(
            context, ToolCallEvent.now("modify_appointment", "started", args)
        )
        result = await appointment_tools.modify_appointment(
            appointment_id, new_date or None, new_time or None
        )
        await self._publish_tool_event(
            context, ToolCallEvent.now("modify_appointment", "completed", args, result)
        )
        return json.dumps(result, default=str)

    # ---- Tool 7: End Conversation ----
    @function_tool
    async def end_conversation(self, context: RunContext, summary: str):
        """End the conversation and provide a summary of what was accomplished.
        Call this when the user says goodbye or indicates they are done.

        Args:
            summary: A brief summary of what was accomplished in this conversation
        """
        args = {"summary": summary}
        await self._publish_tool_event(
            context, ToolCallEvent.now("end_conversation", "started", args)
        )

        # Publish summary on dedicated topic for frontend summary display
        try:
            room = context.session.room
            if room and room.local_participant:
                await room.local_participant.publish_data(
                    payload=json.dumps({"summary": summary}).encode("utf-8"),
                    reliable=True,
                    topic=CALL_SUMMARY_TOPIC,
                )
        except Exception as e:
            logger.warning(f"Failed to publish call summary: {e}")

        await self._publish_tool_event(
            context,
            ToolCallEvent.now("end_conversation", "completed", args, {"summary": summary}),
        )
        return json.dumps({"message": "Conversation ended", "summary": summary})
