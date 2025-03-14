from __future__ import annotations

import typing as t
import asyncio
import rio

from .. import theme, utils, data_models
from ..components.message_composer import MessageComposer


@rio.page(
    name="User Details",
    url_segment="user_details",  # Simple static URL with no parameters
)
class UserDetailsPage(rio.Component):
    """
    Page for viewing details about a specific online user in Retro AIM Server.
    
    This page provides detailed information about a user, including:
    - Account details
    - Active sessions
    - Connection information
    """
    
    # Screen name will be passed via query parameter
    screen_name: str = ""
    
    # User and sessions data
    user: t.Optional[data_models.User] = None
    sessions: t.List[data_models.Session] = []
    
    # Notification banner state
    banner_text: str = ""
    banner_style: t.Literal["success", "danger", "info", "warning"] = "info"
    
    # Loading and error states
    is_loading: bool = False
    has_error: bool = False
    
    def __post_init__(self) -> None:
        """
        Initialize the page and parse URL parameters.
        """
        # Get the screen name from the URL query parameters
        if self.session.active_page_url:
            query_params = self.session.active_page_url.query
            if "screen_name" in query_params:
                self.screen_name = query_params["screen_name"]
    
    @rio.event.on_populate
    async def on_populate(self) -> None:
        """
        Load user details when the page is populated.
        """
        if self.screen_name:
            await self.load_user_details()
        else:
            self.has_error = True
            self.banner_text = "No screen name provided. Cannot load user details."
            self.banner_style = "danger"
    
    @rio.event.on_page_change
    async def on_page_change(self) -> None:
        """
        Reload user details when the page changes.
        
        This handles the case when the URL parameters change while on the same page.
        """
        # Get the screen name from the URL query parameters
        old_screen_name = self.screen_name
        if self.session.active_page_url:
            query_params = self.session.active_page_url.query
            if "screen_name" in query_params:
                self.screen_name = query_params["screen_name"]
            else:
                self.screen_name = ""
                
        # Reload if the screen name changed
        if self.screen_name != old_screen_name:
            if self.screen_name:
                await self.load_user_details()
            else:
                self.has_error = True
                self.banner_text = "No screen name provided. Cannot load user details."
                self.banner_style = "danger"
    
    async def load_user_details(self) -> None:
        """
        Load detailed information about the user and their sessions.
        """
        self.is_loading = True
        self.has_error = False
        self.banner_text = ""
        
        # Launch concurrent fetches for user details and sessions
        user_details_task = asyncio.create_task(
            utils.fetch_user_details(self.session, self.screen_name)
        )
        
        user_sessions_task = asyncio.create_task(
            utils.fetch_user_sessions(self.session, self.screen_name)
        )
        
        # Wait for both tasks to complete
        await asyncio.gather(user_details_task, user_sessions_task)
        
        # Process results
        self.user = user_details_task.result()
        
        # Get user sessions - if fetch_user_sessions fails, fall back to filtering from all sessions
        user_sessions = user_sessions_task.result()
        if user_sessions is not None:
            self.sessions = user_sessions
        else:
            # Fallback: fetch all sessions and filter
            all_sessions = await utils.fetch_sessions(self.session)
            if all_sessions:
                self.sessions = [s for s in all_sessions if s.screen_name.lower() == self.screen_name.lower()]
        
        self.is_loading = False
        
        # Set error state if either fetch failed
        if self.user is None:
            self.has_error = True
            self.banner_text = f"Failed to load user details for {self.screen_name}. The user may not exist."
            self.banner_style = "danger"
        elif not self.sessions:
            # The user exists but has no active sessions
            self.banner_text = f"User {self.screen_name} is not currently online."
            self.banner_style = "warning"
    
    # Proper button event handlers
    async def on_refresh_pressed(self, _event=None) -> None:
        """Handle refresh button press."""
        await self.load_user_details()
    
    async def on_back_to_users_pressed(self, _event=None) -> None:
        """Handle back to users button press."""
        self.session.navigate_to("/users")
        
    async def on_update_user_status(self, _event=None) -> None:
        """
        Handle the update user status button press.
        
        This functionality is currently disabled.
        """
        # This functionality is disabled in this version
        pass
    
    async def on_reset_password(self, _event=None) -> None:
        """
        Handle reset password button press.
        
        Shows a dialog to reset the user's password.
        """
        if not self.user:
            return
            
        # Create a dialog for password reset
        new_password = ""
        
        def build_dialog_content() -> rio.Component:
            return rio.Column(
                rio.Text(
                    text=f"Reset Password for {self.screen_name}",
                    style="heading2",
                    margin_bottom=1,
                ),
                rio.TextInput(
                    new_password,
                    label="New Password",
                    is_secret=True,
                    on_change=on_change_password,
                ),
                rio.Row(
                    rio.Button(
                        "Reset Password",
                        on_press=lambda: dialog.close(True),
                        color="primary",
                    ),
                    rio.Button(
                        "Cancel",
                        on_press=lambda: dialog.close(False),
                        style="minor",
                    ),
                    spacing=1,
                    align_x=1,
                ),
                spacing=1,
                align_y=0,
                align_x=0.5,
            )
        
        def on_change_password(ev: rio.TextInputChangeEvent) -> None:
            nonlocal new_password
            new_password = ev.text
        
        # Show the dialog
        dialog = await self.session.show_custom_dialog(
            build=build_dialog_content,
            modal=True,
        )
        
        # Wait for the user's decision
        result = await dialog.wait_for_close()
        
        if result and new_password:
            # User confirmed password reset
            success = await utils.reset_user_password(self.session, self.screen_name, new_password)
            
            if success:
                self.banner_text = f"Password for '{self.screen_name}' reset successfully"
                self.banner_style = "success"
            else:
                self.banner_text = f"Failed to reset password for '{self.screen_name}'"
                self.banner_style = "danger"
    
    async def on_delete_user(self, _event=None) -> None:
        """
        Handle delete user button press.
        
        Shows a confirmation dialog before deleting the user.
        """
        if not self.user:
            return
            
        # Show confirmation dialog
        result = await self.session.show_yes_no_dialog(
            title="Confirm Delete",
            text=f"Are you sure you want to delete user '{self.screen_name}'? This action cannot be undone.",
            yes_text="Delete",
            no_text="Cancel",
            yes_color="danger",
        )
        
        if result:
            # User confirmed deletion
            success = await utils.delete_user(self.session, self.screen_name)
            
            if success:
                # Navigate back to users page on successful deletion
                self.session.navigate_to("/users")
            else:
                self.banner_text = f"Failed to delete user '{self.screen_name}'"
                self.banner_style = "danger"
    
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
    
    def build_stat_card(self, title: str, value: str, icon: str, color: rio.ColorSet = "primary") -> rio.Component:
        """
        Create a stat card component for displaying user statistics.
        
        Args:
            title: The title of the statistic
            value: The value to display
            icon: The icon to display
            color: The color theme for the card
            
        Returns:
            A card component displaying the statistic
        """
        return rio.Card(
            rio.Column(
                rio.Row(
                    rio.Icon(
                        icon,
                        fill=color,
                        min_width=1.5,
                        min_height=1.5,
                    ),
                    rio.Text(
                        title,
                        style=rio.TextStyle(
                            font_size=0.9,
                            font_weight="bold",
                            fill=theme.TEXT_FILL_DARKER,
                        ),
                    ),
                    spacing=0.5,
                    align_x=0,
                    align_y=0.5,
                ),
                rio.Text(
                    value,
                    style="heading3",
                ),
                spacing=0.5,
                margin=1,
            ),
            grow_x=True,
            corner_radius=0.8,
        )
    
    def build(self) -> rio.Component:
        """
        Build the user details page UI.
        """
        # Banner for notifications
        banner = rio.Banner(
            text=self.banner_text,
            style=self.banner_style,
        ) if self.banner_text else None
        
        # Show loading indicator while data is being fetched
        if self.is_loading:
            error_content = rio.Column(
                rio.ProgressCircle(None),
                rio.Text(
                    f"Loading details for {self.screen_name}...",
                    style=rio.TextStyle(
                        italic=True,
                        fill=theme.TEXT_FILL_DARKER,
                    ),
                ),
                spacing=1,
                align_x=0.5,
                align_y=0.5,
                grow_y=True,
            )
            
            # Create column with or without banner
            if banner:
                return rio.Column(banner, error_content, spacing=1, grow_y=True)
            else:
                return rio.Column(error_content, spacing=1, grow_y=True)
        
        # If there was an error or user not found
        if self.has_error or self.user is None:
            error_content = rio.Column(
                rio.Icon(
                    "material/error",
                    fill="danger",
                    min_width=3,
                    min_height=3,
                ),
                rio.Text(
                    f"User '{self.screen_name}' not found",
                    style="heading2",
                ),
                spacing=1,
                align_x=0.5,
                align_y=0.5,
                grow_y=True,
            )
            
            # Create column with or without banner
            if banner:
                return rio.Column(banner, error_content, spacing=1, grow_y=True)
            else:
                return rio.Column(error_content, spacing=1, grow_y=True)
        
        # Prepare user info display
        user_type = "ICQ" if self.user.is_icq else "AIM"
        status_text = "Active"
        if self.user.suspended_status:
            status_text = {
                "deleted": "Deleted",
                "expired": "Expired",
                "suspended": "Suspended",
                "suspended_age": "Suspended (Age)",
            }.get(self.user.suspended_status, "Unknown")
        
        confirmed_text = "Yes" if self.user.confirmed else "No"
        
        # Stat cards section
        stat_cards = rio.Grid(
            [
                self.build_stat_card(
                    "User Type", 
                    user_type, 
                    "material/person:fill",
                ),
                self.build_stat_card(
                    "Status", 
                    status_text, 
                    "material/info",
                    "secondary" if status_text == "Active" else "danger",
                ),
                self.build_stat_card(
                    "Confirmed", 
                    confirmed_text, 
                    "material/verified",
                    "success" if self.user.confirmed else "warning",
                ),
            ],
            row_spacing=1,
            column_spacing=1,
        )
        
        # Session information
        sessions_section = rio.Column(
            rio.Text(
                "Active Sessions",
                style="heading2",
            ),
            margin_top=1,
        )
        
        if not self.sessions:
            sessions_section.add(
                rio.Text(
                    "No active sessions found for this user.",
                    style=rio.TextStyle(
                        italic=True,
                        fill=theme.TEXT_FILL_DARKER,
                    ),
                )
            )
        else:
            # For each session, add a card with info
            for session in self.sessions:
                online_time = self.format_time(session.online_seconds)
                idle_time = self.format_time(session.idle_seconds) if session.idle_seconds > 0 else "Not idle"
                away_message = session.away_message if session.away_message else "No away message"
                
                session_card = rio.Card(
                    rio.Column(
                        rio.Row(
                            rio.Icon(
                                "material/login",
                                fill="primary",
                                min_width=1.5,
                                min_height=1.5,
                            ),
                            rio.Text(
                                f"Session ID: {session.id}",
                                style=rio.TextStyle(
                                    font_weight="bold",
                                ),
                            ),
                            align_x=0,
                            spacing=0.5,
                        ),
                        rio.Text(
                            f"IP Address: {session.remote_addr}:{session.remote_port}",
                        ),
                        rio.Text(
                            f"Online Time: {online_time}",
                        ),
                        rio.Text(
                            f"Idle Time: {idle_time}",
                        ),
                        rio.Separator(margin_y=0.5),
                        rio.Text(
                            "Away Message:",
                            style=rio.TextStyle(
                                font_weight="bold",
                            ),
                        ),
                        rio.Text(
                            away_message,
                            style=rio.TextStyle(
                                italic=True,
                            ),
                        ),
                        spacing=0.5,
                        margin=1,
                    ),
                    grow_x=True,
                    margin_top=1,
                    corner_radius=0.8,
                )
                sessions_section.add(session_card)
        
        # Build the main layout
        main_content = rio.Column(
            rio.Row(
                rio.Text(
                    f"User Details: {self.screen_name}",
                    style="heading1",
                ),
                rio.Spacer(),
                # Back to Users button
                rio.Tooltip(
                    rio.IconButton(
                        icon="material/arrow_back",
                        color="secondary",
                        style="colored-text",
                        on_press=self.on_back_to_users_pressed,
                        min_size=2.2,
                    ),
                    "Back to Users",
                ),
                # Edit User button (disabled)
                rio.Tooltip(
                    rio.IconButton(
                        icon="material/edit",
                        color="primary",
                        style="colored-text",
                        on_press=self.on_update_user_status,
                        min_size=2.2,
                        is_sensitive=False,
                    ),
                    "Editing User Account Status isn't available in this version of RAS",
                ),
                # Reset Password button
                rio.Tooltip(
                    rio.IconButton(
                        icon="material/password",
                        color="secondary",
                        style="colored-text",
                        on_press=self.on_reset_password,
                        min_size=2.2,
                    ),
                    "Reset Password",
                ),
                # Delete User button
                rio.Tooltip(
                    rio.IconButton(
                        icon="material/delete",
                        color="danger",
                        style="colored-text",
                        on_press=self.on_delete_user,
                        min_size=2.2,
                    ),
                    "Delete User",
                ),
                # Refresh button
                rio.Tooltip(
                    rio.IconButton(
                        icon="material/refresh",
                        color="secondary",
                        style="colored-text",
                        on_press=self.on_refresh_pressed,
                        min_size=2.2,
                    ),
                    "Refresh",
                ),
                align_y=0.5,
                spacing=0.5,
                margin_bottom=2,
            ),
            
            # Profile information
            rio.Text(
                "Profile Information",
                style="heading2",
            ),
            stat_cards,
            
            # Email information if available
            rio.Card(
                rio.Column(
                    rio.Row(
                        rio.Icon(
                            "material/mail",
                            fill="primary",
                            min_width=1.5,
                            min_height=1.5,
                        ),
                        rio.Text(
                            "Email Address",
                            style=rio.TextStyle(
                                font_size=0.9,
                                font_weight="bold",
                                fill=theme.TEXT_FILL_DARKER,
                            ),
                        ),
                        spacing=0.5,
                        align_x=0,
                        align_y=0.5,
                    ),
                    rio.Text(
                        self.user.email_address if self.user.email_address else "No email address provided",
                        style=rio.TextStyle(
                            font_size=1.1,
                        ),
                    ),
                    spacing=0.5,
                    margin=1,
                ),
                grow_x=True,
                margin_top=1,
                corner_radius=0.8,
            ),
            
            # Profile content if available
            rio.Card(
                rio.Column(
                    rio.Row(
                        rio.Icon(
                            "material/article",
                            fill="primary",
                            min_width=1.5,
                            min_height=1.5,
                        ),
                        rio.Text(
                            "Profile",
                            style=rio.TextStyle(
                                font_size=0.9,
                                font_weight="bold",
                                fill=theme.TEXT_FILL_DARKER,
                            ),
                        ),
                        spacing=0.5,
                        align_x=0,
                        align_y=0.5,
                    ),
                    rio.ScrollContainer(
                        rio.Webview(
                            content=self.user.profile if self.user.profile else "<p>No profile information available.</p>",
                            resize_to_fit_content=True,
                        ) if self.user.profile else rio.Text(
                            "No profile information available.",
                            style=rio.TextStyle(
                                italic=True,
                            ),
                        ),
                        scroll_y="auto",
                        min_height=10,
                    ),
                    spacing=0.5,
                    margin=1,
                ),
                grow_x=True,
                margin_top=1,
                corner_radius=0.8,
                min_width=50
            ),
            
            # Message composer section - only show if user is online
            *([MessageComposer(
                target_user=self.screen_name,
            )] if self.sessions else []),
            
            # Sessions information
            sessions_section,
            
            # Add some padding at the bottom
            rio.Spacer(min_height=2),
            
            spacing=1,
            align_x=0,
            align_y=0,
            grow_y=True,
        )
        
        # Create the final layout with or without the banner
        if banner:
            return rio.Column(banner, main_content, spacing=1, grow_y=True)
        else:
            return main_content 