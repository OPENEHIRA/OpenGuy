"""
bot_exceptions.py - Custom exceptions for bot error handling and recovery.
"""


class BotException(Exception):
    """Base exception for all bot-related errors."""
    
    def __init__(self, message: str, error_code: str = "UNKNOWN", user_safe: bool = False):
        """
        Initialize bot exception.
        
        Args:
            message: Error message
            error_code: Machine-readable error code
            user_safe: Whether this message is safe to show to user
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.user_safe = user_safe
    
    def get_user_message(self) -> str:
        """Get safe message to show user."""
        if self.user_safe:
            return self.message
        return "⚠️ An error occurred. Please try again or contact support."


class HardwareException(BotException):
    """Hardware connection or operation errors."""
    
    def __init__(self, message: str, user_safe: bool = True):
        super().__init__(message, error_code="HARDWARE_ERROR", user_safe=user_safe)


class CommandParseException(BotException):
    """Natural language parsing errors."""
    
    def __init__(self, message: str):
        super().__init__(message, error_code="PARSE_ERROR", user_safe=True)


class ValidationException(BotException):
    """Input validation errors."""
    
    def __init__(self, message: str):
        super().__init__(message, error_code="VALIDATION_ERROR", user_safe=True)


class RateLimitException(BotException):
    """User exceeded rate limit."""
    
    def __init__(self, wait_seconds: int):
        message = f"⏳ Too many commands. Wait {wait_seconds}s before trying again."
        super().__init__(message, error_code="RATE_LIMIT", user_safe=True)
        self.wait_seconds = wait_seconds


class SafetyException(BotException):
    """Safety violation (e.g., command too dangerous)."""
    
    def __init__(self, message: str):
        super().__init__(message, error_code="SAFETY_VIOLATION", user_safe=True)


class ExecutorException(BotException):
    """Robot executor errors."""
    
    def __init__(self, message: str):
        super().__init__(message, error_code="EXECUTOR_ERROR", user_safe=True)


class TwilioException(BotException):
    """Twilio API errors."""
    
    def __init__(self, message: str):
        super().__init__(message, error_code="TWILIO_ERROR", user_safe=False)
