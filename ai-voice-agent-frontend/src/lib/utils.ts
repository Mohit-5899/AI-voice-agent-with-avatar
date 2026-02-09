/** Format a tool name for display: "book_appointment" -> "Book Appointment" */
export function formatToolName(name: string): string {
  return name
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/** Format a timestamp as relative time: "2s ago", "1m ago" */
export function formatRelativeTime(isoTimestamp: string): string {
  const diff = Date.now() - new Date(isoTimestamp).getTime();
  const seconds = Math.floor(diff / 1000);

  if (seconds < 5) return "just now";
  if (seconds < 60) return `${seconds}s ago`;
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  return `${Math.floor(minutes / 60)}h ago`;
}

/** Get a color class for a tool name */
export function getToolColor(toolName: string): string {
  const colors: Record<string, string> = {
    identify_user: "bg-blue-100 text-blue-800",
    fetch_slots: "bg-purple-100 text-purple-800",
    book_appointment: "bg-green-100 text-green-800",
    retrieve_appointments: "bg-amber-100 text-amber-800",
    cancel_appointment: "bg-red-100 text-red-800",
    modify_appointment: "bg-orange-100 text-orange-800",
    end_conversation: "bg-gray-100 text-gray-800",
  };
  return colors[toolName] || "bg-gray-100 text-gray-800";
}

/** Format JSON result for display */
export function formatResult(result: Record<string, unknown>): string {
  return JSON.stringify(result, null, 2);
}
