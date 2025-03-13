from __future__ import annotations

import typing as t
from typing import Optional
import rio

from .. import theme, utils, data_models
from ..components.crud_list import CRUDList

@rio.page(
    name="Sessions",
    url_segment="sessions",
)
class SessionsPage(rio.Component):
    """
    Page for managing active user sessions in Retro AIM Server.
    
    This page provides a view of active sessions, allowing administrators to:
    - View a list of all active sessions
    - Kick users (terminate their sessions)
    """
    
    # Sessions list and state
    sessions: t.List[data_models.Session] = []
    
    # Notification banner state
    banner_text: str = ""
    banner_style: t.Literal["success", "danger", "info", "warning"] = "success"
    
    # Loading and error states
    is_loading: bool = False
    has_error: bool = False
    
    @rio.event.on_populate
    async def on_populate(self) -> None:
        """
        Load the list of sessions when the page is populated.
        """
        await self.load_sessions()
    
    async def load_sessions(self) -> None:
        """
        Load the list of active sessions from the RAS API.
        """
        self.is_loading = True
        self.has_error = False
        
        # Fetch sessions from the API
        sessions = await utils.fetch_sessions(self.session)
        
        self.is_loading = False
        if sessions is None:
            self.has_error = True
            self.banner_text = "Failed to load sessions. Check API connection."
            self.banner_style = "danger"
        else:
            self.sessions = sessions
            
            # Clear any previous banner if successful
            if self.banner_text and self.banner_style == "danger":
                self.banner_text = ""
    
    async def on_kick_session(self, session: data_models.Session) -> None:
        """
        Kick a user session.
        
        Args:
            session: The session to kick
        """
        # Show disabled state for this feature (not supported in early versions of RAS)
        await self.session.show_info_dialog(
            title="Feature Not Available", 
            text="The ability to kick individual sessions is not available in this version of Retro AIM Server. This will be added in a future release.", 
            ok_text="OK",
        )
    
    def format_time(self, seconds: float) -> str:
        """
        Format time in seconds into a human-readable string.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string (e.g., "2h 30m" or "45s")
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
    
    def build(self) -> rio.Component:
        """
        Build the sessions page UI.
        """
        # Add description property to sessions for display
        for session in self.sessions:
            # Format online time and idle time
            online_time = self.format_time(session.online_seconds)
            idle_time = self.format_time(session.idle_seconds) if session.idle_seconds > 0 else "Not idle"
            
            # Add IP:port
            remote = f"{session.remote_addr}:{session.remote_port}"
            
            # Add away message if present
            away_info = f" • Away: {session.away_message}" if session.away_message else ""
            
            # Set description
            setattr(session, "display_description", 
                    f"{'ICQ' if session.is_icq else 'AIM'} • Online: {online_time} • {idle_time} • {remote}{away_info}")
        
        # Define the action buttons for each session
        action_buttons = [
            {
                "icon": "material/logout",
                "color": "danger",  # Make it visually distinct
                "tooltip": "Kicking sessions is not supported in this version of RAS",
                "callback": self.on_kick_session,
                "is_sensitive": False,  # Now this will properly disable the button
            },
        ]
        
        # Create a description text (without the title)
        description = rio.Text(
            "Monitor all active user sessions. View connection details, online time, and idle status.",
            style=rio.TextStyle(
                font_size=1.1,
                fill=theme.TEXT_FILL_DARKER,
                italic=True,
            ),
            margin_bottom=1,
        )
        
        # Create the CRUD list with configurations for sessions
        sessions_list = CRUDList[data_models.Session](
            # Data and state
            items=self.sessions,
            is_loading=self.is_loading,
            has_error=self.has_error,
            error_message="Failed to load sessions. Check API connection.",
            
            # Banner state
            banner_text=self.banner_text,
            banner_style=self.banner_style,
            
            # List configuration
            title="Active Sessions",  # Move title here
            create_item_text="",
            create_item_description="",
            create_item_icon="",
            
            # Item display configuration
            item_key_attr="id",
            item_text_attr="screen_name",
            item_description_attr="display_description",
            item_icon="material/login",
            item_icon_default_color="primary",
            
            # Callbacks
            on_create_item=None,  # No create for sessions
            on_refresh=self.load_sessions,
            
            # Action buttons
            action_buttons=action_buttons,
        )
        
        # Return the final layout
        return rio.Column(
            description,
            sessions_list,
            spacing=0,
            align_y=0,
            grow_x=True,
            grow_y=True,
        ) 