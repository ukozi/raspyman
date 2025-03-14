from __future__ import annotations

import rio

# Import all pages so they are registered
from .dashboard_page import DashboardPage
from .users_page import UsersPage
from .chatrooms_page import ChatroomsPage
from .directory_page import DirectoryPage
from .user_details_page import UserDetailsPage
from .send_message_page import SendMessagePage

@rio.page(
    name="Root",
    url_segment="",  # Empty segment for root URL
)
class RootRedirectPage(rio.Component):
    """
    Handles the root URL and redirects to the dashboard page.
    This prevents "landing page not available" errors.
    """
    
    @rio.event.on_mount
    async def redirect_to_dashboard(self) -> None:
        """Redirect to dashboard page on mount."""
        await self.session.navigate_to("/dashboard")
    
    def build(self) -> rio.Component:
        """Simple empty component while redirect happens."""
        return rio.Text("Redirecting to dashboard...") 