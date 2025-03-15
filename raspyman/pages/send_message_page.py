from __future__ import annotations

import typing as t
import time
import rio
from datetime import datetime
import urllib.parse

from .. import theme, utils, data_models
from ..components.message_composer import MessageComposer


class MessageRecord:
    """Represents a single message sent to a user."""
    
    def __init__(self, sender: str, text: str, timestamp: float = None):
        """
        Initialize a message record.
        
        Args:
            sender: Screen name of the sender (admin)
            text: Message text
            timestamp: Unix timestamp (default: current time)
        """
        self.sender = sender
        self.text = text
        self.timestamp = timestamp or time.time()
    
    def format_time(self) -> str:
        """Format the timestamp as a readable time string."""
        dt = datetime.fromtimestamp(self.timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")


@rio.page(
    name="Send Message",
    url_segment="send-message",  # URL will be /send-message?target_user=username
)
class SendMessagePage(rio.Component):
    """
    Page for sending administrative messages to users.
    
    This page provides a form to send one-way messages to online users.
    """
    
    # The user to send a message to
    target_user: str = ""
    
    # Current user (sender)
    current_user: str = ""  # Default sender name
    
    # Message input
    message_input: str = ""
    
    # States
    is_sending: bool = False
    send_error: bool = False
    send_success: bool = False
    
    def __post_init__(self) -> None:
        """Initialize the page and parse URL parameters."""
        # Get the target user from the URL query parameters
        if self.session.active_page_url:
            query_params = self.session.active_page_url.query
            if "target_user" in query_params:
                self.target_user = query_params["target_user"]
        
        # Get admin screen name from settings
        self.current_user = self.session[data_models.RasApiSettings].admin_screen_name
    
    @rio.event.on_mount
    async def on_mount(self) -> None:
        """Handle component mount."""
        # If no target user, navigate back to dashboard
        if not self.target_user:
            # We'll just display an error instead of automatic navigation
            # which might be causing the infinite loop
            pass
    
    def on_message_input_change(self, event: rio.MultiLineTextInputChangeEvent) -> None:
        """Handle message input changes."""
        self.message_input = event.text
        # Reset status when user starts typing a new message
        if self.send_success:
            self.send_success = False
    
    def on_back_pressed(self, _: rio.Event = None) -> None:
        """Handle back button press."""
        # Navigate to the user details page for this user
        encoded_screen_name = urllib.parse.quote(self.target_user)
        self.session.navigate_to(f"/user_details?screen_name={encoded_screen_name}")
    
    async def on_send_message(self, _: rio.Event = None) -> None:
        """Handle send button press."""
        # Check for empty messages and don't proceed if empty
        if not self.message_input.strip():
            # Show a temporary error for empty messages
            self.is_sending = False
            self.send_error = True
            self.send_success = False
            return
        
        self.is_sending = True
        self.send_error = False
        self.send_success = False
        
        # Send message via API
        success = await utils.send_instant_message(
            self.session,
            from_screen_name=self.current_user,
            to_screen_name=self.target_user,
            message_text=self.message_input
        )
        
        self.is_sending = False
        if success:
            # Clear input field on success
            self.message_input = ""
            self.send_success = True
        else:
            self.send_error = True
    
    def build(self) -> rio.Component:
        """Build the send message page UI."""
        # Show error if no target user
        if not self.target_user:
            return rio.Card(
                rio.Column(
                    rio.Icon(
                        "material/error_outline",
                        fill="danger",
                        min_width=3,
                        min_height=3,
                    ),
                    rio.Text(
                        "No recipient specified",
                        style=rio.TextStyle(
                            font_size=1.2,
                            font_weight="bold",
                        ),
                    ),
                    rio.Text(
                        "Redirecting back to dashboard...",
                        style=rio.TextStyle(
                            font_size=0.9,
                            italic=True,
                            fill=theme.TEXT_FILL_DARKER,
                        ),
                    ),
                    spacing=1,
                    align_x=0.5,
                    align_y=0.5,
                    margin=3,
                ),
                margin=2,
                align_x=0.5,
                align_y=0.5,
            )
        
        # Status message
        status_message = None
        if self.send_success:
            status_message = rio.Banner(
                f"Message successfully sent to {self.target_user} from {self.current_user}.",
                style="success",
                margin_bottom=1,
            )
        elif self.send_error:
            status_message = rio.Banner(
                f"Failed to send message to {self.target_user} from {self.current_user}. Please try again.",
                style="danger",
                margin_bottom=1,
            )
        
        # Create the main components list
        column_children = [
            # Header with simpler components
            rio.Row(
                rio.IconButton(
                    icon="material/arrow_back",
                    style="colored-text",
                    color="secondary",
                    on_press=self.on_back_pressed,
                    margin_right=1,
                ),
                rio.Text(
                    f"Send Message to {self.target_user}",
                    style=rio.TextStyle(
                        font_size=1.2,
                        font_weight="bold",
                    ),
                ),
                rio.Spacer(),
                margin=1,
                align_y=0.5,
            ),
            
            rio.Separator(),
            
            # Status message (only shown if there's a status)
            status_message if status_message else rio.Spacer(min_height=0.5),
            
            # Use the reusable message composer component
            MessageComposer(
                target_user=self.target_user,
            ),
            
            # Send button
            rio.Row(
                rio.Spacer(),
                rio.Button(
                    content=rio.Row(
                        rio.Icon(
                            "material/send",
                            fill=rio.Color.WHITE,
                            min_width=1.2,
                            min_height=1.2,
                        ),
                        rio.Text(
                            "Send Message" if not self.is_sending else "Sending...",
                            style=rio.TextStyle(
                                fill=rio.Color.WHITE,
                                font_weight="bold",
                            ),
                        ),
                        spacing=0.8,
                        align_y=0.5,
                        margin=0.5,
                    ) if not self.is_sending else rio.ProgressCircle(size=1.2),
                    on_press=self.on_send_message,
                    is_sensitive=not self.is_sending,  # Only disable when actively sending
                    style="major",
                    color="primary",
                    margin=1,
                ),
            ),
        ]
        
        # Main container
        return rio.Card(
            rio.Column(
                *column_children,
                grow_y=True,
                align_y=0,
            ),
            margin=1,
            grow_x=True,
            grow_y=True,
        ) 