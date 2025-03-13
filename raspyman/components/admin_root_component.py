from __future__ import annotations

import typing as t
import rio

from .. import components as comps

class AdminRootComponent(rio.Component):
    """
    Root component for the RAS admin interface.
    Displays the sidebar and the currently active page.
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
        
        # Create a simple row with sidebar and content
        return rio.Row(
            # Sidebar navigation
            comps.AdminSidebar(active_page=active_page),
            
            # Main content area - just the PageView
            rio.Column(
                rio.PageView(),
                align_x=0,
                align_y=0,
                margin=2,
            ),
            spacing=0,
            align_x=0,
            align_y=0,
        ) 