from __future__ import annotations

import typing as t
import datetime
import rio
import asyncio

from .. import theme
from .. import data_models
from .. import utils
from ..components import StatCard

@rio.page(
    name="Dashboard",
    url_segment="dashboard",
)
class DashboardPage(rio.Component):
    """
    Main dashboard for the RAS Admin interface.
    """
    
    # States for statistics
    active_sessions: int = 0
    chat_rooms: int = 0
    total_users: int = 0
    version_info: str = "Unknown"
    
    # Stats loading indicators
    loading_sessions: bool = True
    loading_chats: bool = True
    loading_users: bool = True
    loading_version: bool = True
    
    # Error states
    has_error_sessions: bool = False
    has_error_chats: bool = False
    has_error_users: bool = False
    has_error_version: bool = False
    
    # Timeout tracking
    _timeout_task = None
    is_loading_timeout: bool = False
    
    def on_api_url_change(self, event: rio.TextInputChangeEvent) -> None:
        """Handle API URL input changes."""
        settings = self.session[data_models.RasApiSettings]
        
        # Ensure the URL is valid
        new_url = event.text
        if new_url == "http://localhost:500":
            new_url = "http://localhost:5000"
        
        settings.api_url = new_url
        
    def on_admin_name_change(self, event: rio.TextInputChangeEvent) -> None:
        """Handle admin screen name input changes."""
        settings = self.session[data_models.RasApiSettings]
        settings.admin_screen_name = event.text

    def on_admin_name_confirm(self, _: rio.TextInputEvent) -> None:
        """Handle admin screen name confirm (Enter key press)."""
        # Just save the settings like pressing the Save button
        self.on_save_admin_name()
        
    def on_save_admin_name(self, _: rio.Event = None) -> None:
        """Save the admin screen name to user settings."""
        settings = self.session[data_models.RasApiSettings]
        
        # Mark as modified and re-attach to save
        if hasattr(settings, '_mark_as_modified'):
            settings._mark_as_modified()
        
        # Update timestamp
        settings.last_connected = datetime.datetime.now().isoformat()
        
        # Re-attach settings to session to ensure they're saved
        self.session.attach(settings)
        
        # Force a UI refresh to show the updated screen name immediately
        self.force_refresh()

    def on_api_url_confirm(self, event: rio.TextInputConfirmEvent) -> None:
        """Save API URL to session when confirmed (Enter key)."""
        settings = self.session[data_models.RasApiSettings]
        
        # Ensure the URL is valid
        new_url = event.text
        if new_url == "http://localhost:500":
            # Fix the typo automatically
            new_url = "http://localhost:5000"
        
        settings.api_url = new_url
        settings.last_connected = datetime.datetime.now().isoformat()
        # Explicitly mark the settings as modified
        if hasattr(settings, '_mark_as_modified'):
            settings._mark_as_modified()
        # Re-attach settings to ensure they're saved
        self.session.attach(settings)
        
        # Set all cards to loading state to provide immediate visual feedback
        self.loading_sessions = True
        self.loading_chats = True
        self.loading_users = True
        self.loading_version = True
        
        # Reset any previous error states
        self.has_error_sessions = False
        self.has_error_chats = False
        self.has_error_users = False
        self.has_error_version = False
        
        # Cancel any existing timeout
        self._cancel_timeout()
        
        # Force a UI refresh to show loading states immediately
        self.force_refresh()
        
        # Set a timeout to clear loading states after 5 seconds if they're still active
        self._timeout_task = self.session.create_task(self._set_loading_timeout(5))
        
        # Refresh stats after URL change
        self.load_stats()
        
    def on_save_api_settings(self) -> None:
        """Save API settings when the save button is clicked."""
        settings = self.session[data_models.RasApiSettings]
        
        # Get the current value from the TextInput and ensure it's explicitly saved
        api_url = settings.api_url
        
        # Fix any incorrect URL
        if not api_url or api_url == "http://localhost:500":
            api_url = "http://localhost:5000"
        
        # Set it again to ensure it's marked as updated
        settings.api_url = api_url 
        settings.last_connected = datetime.datetime.now().isoformat()
        
        # Explicitly mark the settings as modified to ensure persistence
        if hasattr(settings, '_mark_as_modified'):
            settings._mark_as_modified()
        
        # Re-attach settings to ensure they're saved
        self.session.attach(settings)
        
        # Set all cards to loading state to provide immediate visual feedback
        self.loading_sessions = True
        self.loading_chats = True
        self.loading_users = True
        self.loading_version = True
        
        # Reset any previous error states
        self.has_error_sessions = False
        self.has_error_chats = False
        self.has_error_users = False
        self.has_error_version = False
        
        # Cancel any existing timeout
        self._cancel_timeout()
        
        # Force a UI refresh to show loading states immediately
        self.force_refresh()
        
        # Set a timeout to clear loading states after 5 seconds if they're still active
        self._timeout_task = self.session.create_task(self._set_loading_timeout(5))
        
        # Refresh stats after URL change
        self.load_stats()
    
    def _cancel_timeout(self):
        """Cancel any existing timeout task."""
        if self._timeout_task and not self._timeout_task.done():
            self._timeout_task.cancel()
            self._timeout_task = None
    
    async def load_stats(self) -> None:
        """Load all statistics from the API."""
        try:
            # Cancel any existing timeout task
            self._cancel_timeout()
            
            # Set a new timeout to handle cases where API calls don't complete
            self._timeout_task = self.session.create_task(self._set_loading_timeout(5))
            
            # Make API calls in parallel
            stats_tasks = [
                self._load_active_sessions(),
                self._load_chat_rooms(),
                self._load_total_users(),
                self._load_version_info()
            ]
            
            await asyncio.gather(*stats_tasks)
            
            # If we got here, all API calls completed successfully
            if self._timeout_task:
                self._timeout_task.cancel()
                self._timeout_task = None
                
        except Exception as e:
            # Clear loading states if there's an error
            self.loading_sessions = False
            self.loading_chats = False
            self.loading_users = False
            self.loading_version = False
            self.has_error_sessions = True
            self.has_error_chats = True
            self.has_error_users = True
            self.has_error_version = True
    
    async def _load_active_sessions(self) -> None:
        """Load active sessions from the API."""
        self.loading_sessions = True
        self.has_error_sessions = False
        
        try:
            data = await asyncio.wait_for(utils.fetch_active_sessions(self.session), timeout=4.0)
            if data is None:
                self.active_sessions = 0
                self.has_error_sessions = True
            else:
                self.active_sessions = data
                # Even if data is 0, we don't consider it an error
                # so has_error_sessions remains False
        except asyncio.TimeoutError:
            self.active_sessions = 0
            self.has_error_sessions = True
        finally:
            self.loading_sessions = False
    
    async def _load_chat_rooms(self) -> None:
        """Load chat rooms from the API."""
        self.loading_chats = True
        self.has_error_chats = False
        
        try:
            data = await asyncio.wait_for(utils.fetch_chat_rooms(self.session), timeout=4.0)
            if data is None:
                self.chat_rooms = 0
                self.has_error_chats = True
            else:
                self.chat_rooms = len(data)
                # Even if data is empty (len(data) is 0), we don't consider it an error
                # so has_error_chats remains False
        except asyncio.TimeoutError:
            self.chat_rooms = 0
            self.has_error_chats = True
        finally:
            self.loading_chats = False
    
    async def _load_total_users(self) -> None:
        """Load total users from the API."""
        self.loading_users = True
        self.has_error_users = False
        
        try:
            data = await asyncio.wait_for(utils.fetch_total_users(self.session), timeout=4.0)
            if data is None:
                self.total_users = 0
                self.has_error_users = True
            else:
                self.total_users = data
                # Even if data is 0, we don't consider it an error
                # so has_error_users remains False
        except asyncio.TimeoutError:
            self.total_users = 0
            self.has_error_users = True
        finally:
            self.loading_users = False
    
    async def _load_version_info(self) -> None:
        """Load version information from the API."""
        self.loading_version = True
        self.has_error_version = False
        
        try:
            data = await asyncio.wait_for(utils.fetch_version_info(self.session), timeout=4.0)
            if data is None:
                self.version_info = "Unknown"
                self.has_error_version = True
            else:
                # Format the version info as a string
                self.version_info = data.get("version", "Unknown")
        except asyncio.TimeoutError:
            self.version_info = "Unknown"
            self.has_error_version = True
        finally:
            self.loading_version = False
    
    async def _process_api_result(self, api_call, error_message: str) -> t.Any:
        """Process an API call result with consistent error handling."""
        try:
            result = await api_call()
            
            if result is None:
                self.api_errors.append(error_message)
                return None
            
            return result
            
        except asyncio.TimeoutError:
            self.api_errors.append(error_message)
            return None
        
        except Exception as e:
            self.api_errors.append(f"{error_message}")
            return None
    
    def _validate_api_url(self) -> bool:
        """Validate the current API URL and fix it if needed."""
        settings = self.session[data_models.RasApiSettings]
        
        # Check if we have a valid API URL
        if not settings.api_url or settings.api_url == "http://localhost:500":
            settings.api_url = "http://localhost:5000"
            
            # Explicitly mark settings as modified to ensure they're saved
            if hasattr(settings, '_mark_as_modified'):
                settings._mark_as_modified()
            
            # Re-attach to ensure persistence
            self.session.attach(settings)
            
        # Update the local state
        self.current_api_url = settings.api_url
        
        return bool(settings.api_url)
    
    async def _handle_timeout(self, seconds: int) -> None:
        """Handle timeout for loading data."""
        try:
            # Wait for specified seconds
            await asyncio.sleep(seconds)
            
            # Make a fresh attempt to load data, setting a flag to avoid recursion
            if not self.is_loading_timeout:
                self.is_loading_timeout = True
                
                # Try to load active sessions as the most critical data
                try:
                    await self._load_active_sessions()
                except Exception as e:
                    pass
                    
                # Try to load chat rooms
                try:
                    await self._load_chat_rooms()
                except Exception as e:
                    pass
                    
                # Try to load user count
                try:
                    await self._load_total_users()
                except Exception as e:
                    pass
                    
                # Try to load version info
                try:
                    await self._load_version_info()
                except Exception as e:
                    pass
                    
                self.is_loading_timeout = False
        except asyncio.CancelledError:
            # Timeout was cancelled, which is fine
            pass
    
    @rio.event.on_mount
    async def on_mount(self) -> None:
        """Load stats when the component is mounted."""
        # Make sure loading indicators start in a clean state
        self.loading_sessions = True
        self.loading_chats = True
        self.loading_users = True
        self.loading_version = True
        self.has_error_sessions = False
        self.has_error_chats = False
        self.has_error_users = False
        self.has_error_version = False
        
        # Force a refresh to show loading state
        self.force_refresh()
        
        # Start loading stats
        await self.load_stats()
    
    def build(self) -> rio.Component:
        settings = self.session[data_models.RasApiSettings]
        
        # Only fix if the URL is missing or incorrect (don't override valid custom URLs)
        if not settings.api_url or settings.api_url == "http://localhost:500":
            settings.api_url = "http://localhost:5000"
            if hasattr(settings, '_mark_as_modified'):
                settings._mark_as_modified()
            # Re-attach settings to ensure they're saved
            self.session.attach(settings)
        
        # Main dashboard content
        return rio.Column(
            # Header section
            rio.Text(
                "Dashboard",
                style="heading1",
                margin_bottom=2,
            ),
            
            # Stats row
            rio.Row(
                StatCard(
                    title="Active Sessions",
                    value=self.active_sessions,
                    icon="material/person_raised_hand",
                    color="primary",
                    is_loading=self.loading_sessions,
                    has_error=self.has_error_sessions,
                ),
                StatCard(
                    title="Chat Rooms",
                    value=self.chat_rooms,
                    icon="material/chat",
                    color="secondary",
                    is_loading=self.loading_chats,
                    has_error=self.has_error_chats,
                ),
                StatCard(
                    title="Total Users",
                    value=self.total_users,
                    icon="material/person",
                    color="success",
                    is_loading=self.loading_users,
                    has_error=self.has_error_users,
                ),
                StatCard(
                    title="RAS Version",
                    value=self.version_info,
                    icon="material/terminal",
                    color="primary",
                    is_loading=self.loading_version,
                    has_error=self.has_error_version,
                ),
                spacing=1.0,
                margin_bottom=1,
            ),
            
            # API Settings Card
            rio.Card(
                content=rio.Column(
                    rio.Text(
                        "RAS Connection Settings",
                        style=rio.TextStyle(
                            font_size=1.2,
                            font_weight="bold",
                        ),
                    ),
                    rio.Text(
                        "Configure the connection to your Retro AIM Server API:",
                        style=rio.TextStyle(
                            font_size=1.0,
                            fill=theme.TEXT_FILL_DARKER,
                        ),
                    ),
                    rio.Text(
                        f"Current API URL: {settings.api_url}",
                        style=rio.TextStyle(
                            font_size=1.0,
                            fill=theme.TEXT_FILL_DARKER,
                        ),
                    ),
                    rio.Row(
                        rio.Text(
                            "API URL:",
                            style=rio.TextStyle(
                                font_size=1.0,
                            ),
                            margin_right=0.5,
                        ),
                        rio.TextInput(
                            text=settings.api_url,
                            label="",
                            on_change=self.on_api_url_change,
                            on_confirm=self.on_api_url_confirm,
                            grow_x=True,
                            margin_right=1.0,  # Add margin to create space between input and button
                        ),
                        rio.Button(
                            content="Save",
                            on_press=self.on_save_api_settings,
                            style="major",
                        ),
                        align_y=0.5,
                    ),
                    spacing=1,
                    margin=1,
                ),
            ),
            
            # Admin Screen Name Settings Card
            rio.Card(
                content=rio.Column(
                    rio.Text(
                        "Administrator Screen Name",
                        style=rio.TextStyle(
                            font_size=1.2,
                            font_weight="bold",
                        ),
                    ),
                    rio.Text(
                        "Set the screen name to use when sending administrator messages:",
                        style=rio.TextStyle(
                            font_size=1.0,
                            fill=theme.TEXT_FILL_DARKER,
                        ),
                    ),
                    rio.Text(
                        f"Current Screen Name: {settings.admin_screen_name}",
                        style=rio.TextStyle(
                            font_size=1.0,
                            fill=theme.TEXT_FILL_DARKER,
                        ),
                    ),
                    rio.Row(
                        rio.Text(
                            "Screen Name:",
                            style=rio.TextStyle(
                                font_size=1.0,
                            ),
                            margin_right=0.5,
                        ),
                        rio.TextInput(
                            text=settings.admin_screen_name,
                            label="",
                            on_change=self.on_admin_name_change,
                            on_confirm=self.on_admin_name_confirm,
                            grow_x=True,
                            margin_right=1.0,
                        ),
                        rio.Button(
                            content="Save",
                            on_press=self.on_save_admin_name,
                            style="major",
                        ),
                        align_y=0.5,
                    ),
                    spacing=1,
                    margin=1,
                ),
                margin_top=1,
            ),
            min_width=50,
            spacing=1,
            align_x=0,
        ) 

    async def _set_loading_timeout(self, seconds: int) -> None:
        """
        Set a timeout to clear loading states after specified seconds.
        If data hasn't loaded by then, make a fresh attempt to fetch stats.
        
        Args:
            seconds: Number of seconds to wait before clearing loading states
        """
        try:
            # Wait for the specified time
            await asyncio.sleep(seconds)
            
            # Force all loading states to False, regardless of API call status
            self.loading_sessions = False
            self.loading_chats = False
            self.loading_users = False
            self.loading_version = False
            
            # Mark cards that were still loading as having errors
            if not self.is_loading_timeout:
                self.is_loading_timeout = True
                
                # Only set error flags for items that didn't complete successfully
                if self.loading_sessions:
                    self.has_error_sessions = True
                    self.active_sessions = 0
                    
                if self.loading_chats:
                    self.has_error_chats = True
                    self.chat_rooms = 0
                    
                if self.loading_users:
                    self.has_error_users = True
                    self.total_users = 0
                    
                if self.loading_version:
                    self.has_error_version = True
                    self.version_info = "Unknown"
                
                # Try to make a fresh attempt for all stats
                try:
                    # Fresh attempt for active sessions
                    data = await asyncio.wait_for(utils.fetch_active_sessions(self.session), timeout=3.0)
                    if data is not None:
                        self.active_sessions = data
                        self.has_error_sessions = False
                    else:
                        self.active_sessions = 0
                        self.has_error_sessions = True
                except Exception as e:
                    self.active_sessions = 0
                    self.has_error_sessions = True
                
                try:
                    # Fresh attempt for chat rooms
                    data = await asyncio.wait_for(utils.fetch_chat_rooms(self.session), timeout=3.0)
                    if data is not None:
                        self.chat_rooms = len(data)
                        self.has_error_chats = False
                    else:
                        self.chat_rooms = 0
                        self.has_error_chats = True
                except Exception as e:
                    self.chat_rooms = 0
                    self.has_error_chats = True
                
                try:
                    # Fresh attempt for total users
                    data = await asyncio.wait_for(utils.fetch_total_users(self.session), timeout=3.0)
                    if data is not None:
                        self.total_users = data
                        self.has_error_users = False
                    else:
                        self.total_users = 0
                        self.has_error_users = True
                except Exception as e:
                    self.total_users = 0
                    self.has_error_users = True
                    
                try:
                    # Fresh attempt for version info
                    data = await asyncio.wait_for(utils.fetch_version_info(self.session), timeout=3.0)
                    if data is not None:
                        self.version_info = data.get("version", "Unknown")
                        self.has_error_version = False
                    else:
                        self.version_info = "Unknown"
                        self.has_error_version = True
                except Exception as e:
                    self.version_info = "Unknown"
                    self.has_error_version = True
                
                self.is_loading_timeout = False
                
                # Force refresh the UI with the new states
                self.force_refresh()
        except asyncio.CancelledError:
            # Handle task cancellation gracefully
            pass 