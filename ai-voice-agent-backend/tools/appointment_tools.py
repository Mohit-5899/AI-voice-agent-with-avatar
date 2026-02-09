from datetime import date
from db.supabase_client import get_supabase
from tools.slot_generator import generate_all_slots


async def identify_user_by_phone(phone_number: str) -> dict:
    """Look up a user by phone number from existing appointments."""
    sb = get_supabase()
    result = (
        sb.table("appointments")
        .select("patient_name, phone_number")
        .eq("phone_number", phone_number)
        .limit(1)
        .execute()
    )
    if result.data:
        return {
            "found": True,
            "name": result.data[0]["patient_name"],
            "phone": phone_number,
        }
    return {"found": False, "phone": phone_number}


async def fetch_available_slots(preferred_date: str | None = None) -> list[dict]:
    """Get available appointment slots, optionally filtered by a specific date."""
    sb = get_supabase()
    today = date.today()
    all_slots = generate_all_slots(today)

    # Get all booked slots from today onwards
    booked = (
        sb.table("appointments")
        .select("appointment_date, appointment_time")
        .eq("status", "scheduled")
        .gte("appointment_date", today.isoformat())
        .execute()
    )

    # Build a set of booked (date, time) pairs for fast lookup
    booked_set = set()
    for row in booked.data:
        # appointment_time comes as "HH:MM:SS", we only need "HH:MM"
        time_str = row["appointment_time"][:5]
        booked_set.add((row["appointment_date"], time_str))

    # Filter out booked slots
    available = [s for s in all_slots if (s["date"], s["time"]) not in booked_set]

    # Optionally filter by preferred date
    if preferred_date:
        available = [s for s in available if s["date"] == preferred_date]

    return available


async def book_appointment(
    phone_number: str,
    patient_name: str,
    appointment_date: str,
    appointment_time: str,
    reason: str | None = None,
) -> dict:
    """Book a new appointment. Returns success status and appointment details."""
    sb = get_supabase()

    # Check if slot is still available (prevent double-booking)
    existing = (
        sb.table("appointments")
        .select("id")
        .eq("appointment_date", appointment_date)
        .eq("appointment_time", appointment_time)
        .eq("status", "scheduled")
        .execute()
    )
    if existing.data:
        return {
            "success": False,
            "error": f"Slot on {appointment_date} at {appointment_time} is already booked. Please choose another time.",
        }

    data = {
        "phone_number": phone_number,
        "patient_name": patient_name,
        "appointment_date": appointment_date,
        "appointment_time": appointment_time,
        "reason": reason or "General checkup",
    }
    result = sb.table("appointments").insert(data).execute()
    return {"success": True, "appointment": result.data[0]}


async def retrieve_appointments(phone_number: str) -> list[dict]:
    """Get all scheduled (active) appointments for a user."""
    sb = get_supabase()
    result = (
        sb.table("appointments")
        .select("*")
        .eq("phone_number", phone_number)
        .eq("status", "scheduled")
        .order("appointment_date")
        .execute()
    )
    return result.data


async def cancel_appointment(appointment_id: str) -> dict:
    """Cancel an appointment by setting its status to 'cancelled'."""
    sb = get_supabase()
    result = (
        sb.table("appointments")
        .update({"status": "cancelled"})
        .eq("id", appointment_id)
        .eq("status", "scheduled")
        .execute()
    )
    if result.data:
        return {"success": True, "cancelled": result.data[0]}
    return {"success": False, "error": "Appointment not found or already cancelled"}


async def modify_appointment(
    appointment_id: str,
    new_date: str | None = None,
    new_time: str | None = None,
) -> dict:
    """Modify an existing appointment's date and/or time."""
    sb = get_supabase()

    updates = {}
    if new_date:
        updates["appointment_date"] = new_date
    if new_time:
        updates["appointment_time"] = new_time

    if not updates:
        return {"success": False, "error": "No changes specified"}

    # Check if the new slot is available
    check_date = new_date
    check_time = new_time
    if check_date or check_time:
        # Get current appointment to fill in missing fields
        current = (
            sb.table("appointments")
            .select("appointment_date, appointment_time")
            .eq("id", appointment_id)
            .execute()
        )
        if not current.data:
            return {"success": False, "error": "Appointment not found"}

        check_date = check_date or current.data[0]["appointment_date"]
        check_time = check_time or current.data[0]["appointment_time"][:5]

        existing = (
            sb.table("appointments")
            .select("id")
            .eq("appointment_date", check_date)
            .eq("appointment_time", check_time)
            .eq("status", "scheduled")
            .neq("id", appointment_id)
            .execute()
        )
        if existing.data:
            return {
                "success": False,
                "error": f"Slot on {check_date} at {check_time} is already booked.",
            }

    result = (
        sb.table("appointments")
        .update(updates)
        .eq("id", appointment_id)
        .eq("status", "scheduled")
        .execute()
    )
    if result.data:
        return {"success": True, "updated": result.data[0]}
    return {"success": False, "error": "Appointment not found or already cancelled"}
