from __future__ import annotations

import typing as t
import rio

from .. import components as comps
from .. import data_models

class AdminRootComponent(rio.Component):
    """
    Root component for the RAS admin interface.
    Displays the sidebar and the currently active page.
    
    The sidebar is now implemented as an overlay component that stays
    fixed on the left side of the screen.
    """
    
    @rio.event.on_page_change
    def _on_page_change(self) -> None:
        # Force the component to rebuild when the page changes
        self.force_refresh()
    
    def build(self) -> rio.Component:
        # Get the current page URL to highlight the active nav item
        current_url = str(self.session.active_page_url)
        
        # Extract just the path segment
        if "://" in current_url:
            current_url = current_url.split("://", 1)[1]
            current_url = current_url.split("/", 1)[1] if "/" in current_url else ""
            
        active_page = current_url.strip("/") or "dashboard"
        
        # Get device type to determine sidebar width
        device = self.session[data_models.PageLayout].device
        sidebar_width = 14 if device == "desktop" else 12
        
        # Pages where we want to limit width
        width_limited_pages = ["dashboard", "users", "chatrooms", "directory", "user"]
        
        # Check if current page should have limited width
        apply_width_limit = any(segment in active_page for segment in width_limited_pages)
        
        # Create a layout with the sidebar overlay and content
        return rio.Column(
            # Add the sidebar as an overlay
            comps.AdminSidebar(active_page=active_page),
            
            # Main content area with margin to prevent overlap with sidebar
            rio.Column(
                # Container to limit width if needed
                rio.Container(
                    content=rio.PageView(),
                    # Apply width constraint only for specific pages
                    min_width=70 if apply_width_limit else None,
                    # Center the container if width is limited
                    align_x=0.5 if apply_width_limit else 0,
                ),
                align_x=0,
                align_y=0,
                margin=2,
                # Add margin to the left to prevent overlap with sidebar
                margin_left=sidebar_width + 2,
                grow_x=True,
                grow_y=True,
            ),
            spacing=0,
            align_x=0,
            align_y=0,
            grow_x=True,
            grow_y=True,
        ) 