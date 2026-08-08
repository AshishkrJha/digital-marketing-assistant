class LLMAPIError(Exception):
    """Raised when Gemini API call fails."""
    pass


class CRMSyncError(Exception):
    """Raised when CRM integration fails."""
    pass


class InvalidProjectAccess(Exception):
    """Raised when user doesn't have access to project."""
    pass


class InvalidResponseSubmission(Exception):
    """Raised when user can't submit a response."""
    pass


class ConversationNotFound(Exception):
    """Raised when conversation doesn't exist."""
    pass


class InvalidModerationAction(Exception):
    """Raised when invalid moderation action attempted."""
    pass
