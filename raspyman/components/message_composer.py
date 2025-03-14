from __future__ import annotations

import typing as t
import rio
import time
from datetime import datetime

from .. import theme, utils, data_models


class MessageComposer(rio.Component):
    """
    A reusable component for composing and sending messages to users.
    
    This component provides a form for sending one-way administrative messages
    to users without requiring a full page.
    """
    
    # The user to send a message to
    target_user: str
    
    # Message input
    message_input: str = ""
    
    # States
    is_sending: bool = False
    send_error: bool = False
    send_success: bool = False
    
    # Optional callback when a message is sent successfully
    on_message_sent: t.Optional[t.Callable[[str, str, str], None]] = None
    
    def __post_init__(self) -> None:
        """Initialize the component."""
        # Get admin screen name from settings
        self.current_user = self.session[data_models.RasApiSettings].admin_screen_name
    
    def on_message_input_change(self, event: rio.MultiLineTextInputChangeEvent) -> None:
        """Handle message input changes."""
        self.message_input = event.text
        # Reset status when user starts typing a new message
        if self.send_success:
            self.send_success = False
    
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
        
        # Get the latest admin screen name before sending
        self.current_user = self.session[data_models.RasApiSettings].admin_screen_name
        
        # Send message via API
        success = await utils.send_instant_message(
            self.session,
            from_screen_name=self.current_user,
            to_screen_name=self.target_user,
            message_text=self.message_input
        )
        
        self.is_sending = False
        if success:
            # Call the optional callback if provided
            if self.on_message_sent:
                self.on_message_sent(self.current_user, self.target_user, self.message_input)
                
            # Clear input field on success
            self.message_input = ""
            self.send_success = True
        else:
            self.send_error = True
    
    def build(self) -> rio.Component:
        """Build the message composer UI."""
        # Get the latest admin screen name every time the component renders
        self.current_user = self.session[data_models.RasApiSettings].admin_screen_name
        
        # Status message
        status_message = None
        if self.send_success:
            status_message = rio.Banner(
                f"Message successfully sent to {self.target_user} from {self.current_user}.",
                style="success",
            )
        elif self.send_error:
            status_message = rio.Banner(
                f"Failed to send message to {self.target_user} from {self.current_user}. Please try again.",
                style="danger",
            )
        
        # Main container
        return rio.Card(
            rio.Column(
                # Title - simpler than the page version
                rio.Text(
                    f"Send Message to {self.target_user}",
                    style=rio.TextStyle(
                        font_size=1.1,
                        font_weight="bold",
                    ),
                    margin_bottom=0.5,
                ),
                
                # Status message (only shown if there's a status)
                status_message if status_message else rio.Spacer(min_height=0.5),
                
                # Message composer
                rio.Column(
                    rio.MultiLineTextInput(
                        text=self.message_input,
                        label="Type your message here...",
                        on_change=self.on_message_input_change,
                        on_confirm=self.on_send_message,
                        grow_x=True,
                        min_height=5,  # Slightly smaller than the page version
                    ),
                    spacing=1,
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
                        margin_top=0.5,
                    ),
                ),
                
                spacing=0.5,
                margin=1,
            ),
            margin=0,
        )
