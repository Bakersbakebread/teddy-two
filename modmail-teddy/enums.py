from enum import Enum, IntEnum


class MessageType(Enum):
    """Enum for messge type, used in channel name"""

    REPORT = ("Report", "[REP]")
    SUGGESTION = ("Suggestion", "[SUG]")


class ThreadStatus(Enum):
    """Status of thread"""

    NEW = ("New", "📫")
    ACTIVE = ("Active", "📤")
    CLOSED = ("Closed", "🔒")
