import typing as t
from dataclasses import dataclass
from datetime import datetime
import rio


@dataclass(frozen=True)
class PageLayout:
    """
    Class to represent the layout of a page on the website.

    ## Attributes:

    `device`: The device the layout is for. Can be either "desktop" or "mobile".


    """

    device: t.Literal["desktop", "mobile"]


@dataclass
class User:
    """
    Class to represent a user account in Retro AIM Server.
    """
    id: str
    screen_name: str
    is_icq: bool
    suspended_status: t.Optional[str] = None
    profile: t.Optional[str] = None
    email_address: t.Optional[str] = None
    confirmed: bool = False
    
    @property
    def display_description(self) -> str:
        """
        Get a formatted description for display in the UI.
        
        Returns:
            A string with user type and status information
        """
        # User type indicator
        user_type = "ICQ" if self.is_icq else "AIM"
        
        # Determine the status display
        status_text = "Active"
        
        if self.suspended_status:
            if self.suspended_status == "deleted":
                status_text = "Deleted"
            elif self.suspended_status == "expired":
                status_text = "Expired"
            elif self.suspended_status == "suspended":
                status_text = "Suspended"
            elif self.suspended_status == "suspended_age":
                status_text = "Suspended (Age)"
        
        return f"{user_type} • {status_text}"


@dataclass
class Session:
    """
    Class to represent an active user session in Retro AIM Server.
    """
    id: str
    screen_name: str
    online_seconds: float
    away_message: str
    idle_seconds: float
    is_icq: bool
    remote_addr: str
    remote_port: int
    

@dataclass
class ChatRoom:
    """
    Class to represent a chat room in Retro AIM Server.
    """
    name: str
    create_time: str
    participants: t.List[dict]
    creator_id: t.Optional[str] = None
    

@dataclass
class Category:
    """
    Class to represent a directory category in Retro AIM Server.
    """
    id: int
    name: str
    

@dataclass
class Keyword:
    """
    Class to represent a directory keyword in Retro AIM Server.
    """
    id: int
    name: str
    category_id: int = 0


class RasApiSettings(rio.UserSettings):
    """
    User settings for RAS API configuration.
    
    ## Attributes:
    
    `api_url`: The URL of the RAS API endpoint.
    `last_connected`: When the API was last successfully connected to.
    """
    section_name = "api"  # Settings will be stored in the "api" section
    
    api_url: str = "http://localhost:5000"  # Default to a common local API port
    last_connected: t.Optional[str] = None  # ISO timestamp of last successful connection
    
    def __post_init__(self) -> None:
        """Ensure the API URL is properly initialized and persisted."""
        # Only set default URL if current value is missing or invalid
        if not self.api_url or self.api_url == "http://localhost:500":
            self.api_url = "http://localhost:5000"
        
        # Mark the instance as modified to ensure it's persisted
        # This forces Rio to save these values to persistent storage
        self._mark_as_modified()