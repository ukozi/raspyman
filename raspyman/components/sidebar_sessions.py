from __future__ import annotations

import typing as t
import rio
import urllib.parse

from .. import theme, utils, data_models
from ..components.message_composer import MessageComposer

class SidebarSessions(rio.Component):
    """
    A component that displays active sessions in the sidebar.
    
    This component fetches and displays a list of active user sessions
    in the RAS admin sidebar.
    """
    
    # Sessions list and state
    sessions: t.List[data_models.Session] = []
    
    # Loading and error states
    is_loading: bool = False
    has_error: bool = False
    is_expanded: bool = True  # Default to expanded
    
    # Popup state
    popup_visible: bool = False
    target_user: str = ""
    
    @rio.event.on_populate
    async def on_populate(self) -> None:
        """
        Load the list of sessions when the component is populated.
        """
        await self.load_sessions()
    
    # We'll periodically refresh the sessions list
    @rio.event.periodic(interval=30)
    async def refresh_sessions(self) -> None:
        """
        Periodically refresh the sessions list.
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
        else:
            self.sessions = sessions
    
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
    
    def toggle_expanded(self, _: rio.PointerEvent) -> None:
        """Toggle the expanded state of the sessions list."""
        self.is_expanded = not self.is_expanded
    
    def on_user_clicked(self, screen_name: str) -> None:
        """Toggle the message composer popup when a user's send icon is clicked."""
        # If it's already visible for this user, hide it, otherwise show it
        if self.popup_visible and self.target_user == screen_name:
            self.popup_visible = False
            self.target_user = ""
        else:
            self.target_user = screen_name
            self.popup_visible = True
        self.force_refresh()
    
    def on_popup_close(self) -> None:
        """Close the message composer popup."""
        self.popup_visible = False
        self.target_user = ""
        self.force_refresh()
    
    def on_message_sent(self, from_user: str, to_user: str, message: str) -> None:
        """Handle message sent event."""
        # Close the popup after successful message sending
        self.popup_visible = False
        self.force_refresh()
    
    def build(self) -> rio.Component:
        """
        Build the sessions component UI.
        """
        # Text and icon colors
        text_color = rio.Color.WHITE
        inactive_text = rio.Color.from_hex("#cccccc")
        
        # Header with session count and toggle button
        header = rio.Row(
            rio.Icon(
                "material/person_raised_hand:fill",  # Changed icon
                min_width=1.2,
                min_height=1.2,
                fill=inactive_text,
            ),
            rio.Text(
                f"Online Users ({len(self.sessions)})",  # Changed title
                style=rio.TextStyle(
                    font_size=1.1,
                    font_weight="normal",
                    fill=inactive_text,
                ),
            ),
            rio.Spacer(),
            rio.Icon(
                "material/expand_more" if self.is_expanded else "material/expand_less",
                min_width=1.2,
                min_height=1.2,
                fill=inactive_text,
            ),
            spacing=0.6,
            align_x=0,
            align_y=0.5,
            margin=0.5,
        )
        
        # Wrapper for the header to make it clickable
        header_clickable = rio.PointerEventListener(
            content=header,
            on_press=self.toggle_expanded,
        )
        
        # Create the sessions list
        sessions_list = rio.Column(
            spacing=0.3,
            align_x=0,
            margin_x=0.5,
        )
        
        # Add each session to the list
        for session in self.sessions:
            # Get the screen name
            screen_name = session.screen_name.strip()
            
            # URL encode the screen name for the link to user details
            encoded_screen_name = urllib.parse.quote(screen_name)
            
            # Create the user info part that links to user details
            user_info = rio.Link(
                target_url=f"/user_details?screen_name={encoded_screen_name}",
                content=rio.Row(
                    rio.Icon(
                        "material/person:fill",
                        min_width=1.0,
                        min_height=1.0,
                        fill=inactive_text,
                    ),
                    rio.Text(
                        screen_name,
                        style=rio.TextStyle(
                            font_size=0.9,
                            fill=inactive_text,
                        ),
                    ),
                    spacing=0.4,
                    align_x=0,
                    align_y=0.5,
                    grow_x=True,
                ),
            )
            
            # Create a row with user info and send button
            user_row = rio.Row(
                # User info section (links to user details)
                user_info,
                rio.Spacer(),
                # Chat icon button with direct lambda
                rio.Popup(
                    anchor=rio.IconButton(
                        icon="material/send",
                        size=1,
                        style="colored-text",
                        color=inactive_text,
                        on_press=lambda screen_name=screen_name: self.on_user_clicked(screen_name),
                    ),
                    content=rio.Card(
                        content=rio.Column(
                            rio.Row(
                                rio.Spacer(),
                                rio.IconButton(
                                    icon="material/close",
                                    size=1.2,
                                    style="colored-text",
                                    color="danger",
                                    on_press=self.on_popup_close,
                                ),
                                spacing=0.5,
                                align_y=0,
                            ),
                            MessageComposer(
                                target_user=screen_name,
                                on_message_sent=lambda from_user, to_user, message, screen_name=screen_name: self.on_message_sent(from_user, to_user, message),
                            ),
                            spacing=0.5,
                            align_x=0,
                            margin=1,
                        ),
                    ),
                    is_open=self.popup_visible and self.target_user == screen_name,
                    position="center",
                    color="hud",
                ),
                spacing=2,
                margin_y=0.2,
            )
            
            sessions_list.add(user_row)
        
        # If the list is empty, show a message
        if not self.sessions:
            no_sessions_text = "No users online" if not self.is_loading else "Loading users..."  # Updated text
            sessions_list.add(
                rio.Text(
                    no_sessions_text,
                    style=rio.TextStyle(
                        font_size=0.9,
                        fill=inactive_text,
                        italic=True,
                    ),
                    margin_y=0.3,
                    margin_left=0.2,
                )
            )
        
        # Main container with header and collapsible content
        main_content = rio.Column(
            header_clickable,
            # Use a Switcher to animate the expansion/collapse
            rio.Switcher(
                sessions_list if self.is_expanded else None,
                transition_time=0.25,
            ),
            margin_top=2,
            spacing=1,
            align_x=0,
            align_y=0,
        )
        
        # Return the main content without any overlay
        return main_content 