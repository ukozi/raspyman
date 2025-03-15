from __future__ import annotations

import typing as t
import rio

from .. import data_models
from .. import theme
from .sidebar_sessions import SidebarSessions

class AdminSidebar(rio.Component):
    """
    Sidebar navigation for the RAS admin interface.
    
    Now implemented as an overlay component that stays fixed 
    on the left side of the screen.
    """
    active_page: str = ""
    
    def build(self) -> rio.Component:
        device = self.session[data_models.PageLayout].device
        
        # Extract just the path segment from the full URL
        current_path = str(self.session.active_page_url)
        # Remove protocol and domain if present
        if "://" in current_path:
            current_path = current_path.split("://", 1)[1]
            current_path = current_path.split("/", 1)[1] if "/" in current_path else ""
        current_path = current_path.strip("/")
        
        # If empty, it's the dashboard
        if not current_path:
            current_path = "dashboard"
            
        # Map some potential variations in URL paths to our menu IDs
        path_mapping = {
            "chat-rooms": "chatrooms",
            "chatrooms": "chatrooms",
            "chat_rooms": "chatrooms",
        }
        
        active_segment = path_mapping.get(current_path, current_path)
        
        # Navigation items with exact matching IDs
        nav_items = [
            ("dashboard", "Dashboard", "material/space_dashboard:fill"),
            ("users", "Users", "material/person:fill"),
            ("chatrooms", "Chat Rooms", "material/chat:fill"),
            ("directory", "Directory", "material/menu_book:fill"),
        ]
        
        # Navigation column
        nav_links = rio.Column(
            spacing=0,
            align_x=0,
            align_y=0,
        )
        
        # Define colors - using standard Rio approach
        primary_color = self.session.theme.primary_color
        text_color = rio.Color.WHITE
        inactive_text = rio.Color.from_hex("#cccccc")
        
        for item_id, label, icon in nav_items:
            is_active = (item_id == self.active_page)
            
            nav_links.add(
                rio.Link(
                    target_url=f"/{item_id}",
                    content=rio.Row(
                        # Left indicator bar for active item
                        rio.Rectangle(
                            min_width=0.2,
                            min_height=2.0,
                            fill=primary_color if is_active else rio.Color.TRANSPARENT,
                            corner_radius=0,
                        ),
                        
                        rio.Row(
                            rio.Icon(
                                icon,
                                min_width=1.2,
                                min_height=1.2,
                                fill=text_color if is_active else inactive_text,
                            ),
                            rio.Text(
                                label,
                                style=rio.TextStyle(
                                    font_size=1.1,
                                    font_weight="bold" if is_active else "normal",
                                    fill=text_color if is_active else inactive_text,
                                ),
                            ),
                            spacing=0.6,
                            align_x=0,
                            align_y=0.5,
                            margin_left=0.5,
                            margin_y=0.5,
                        ),
                        spacing=0,
                        align_x=0,
                        align_y=0.5,
                    )
                )
            )
        
        # Create the sidebar content with all styling intact
        sidebar_content = rio.Rectangle(
            content=rio.Column(
                # Title at top
                rio.Row(
                    rio.Text(
                        "RASPyMAN",
                        style=rio.TextStyle(
                            font_size=1.6,
                            font_weight="bold",
                            fill=text_color,
                        ),
                    ),
                    align_x=0.5, 
                    margin_y=2.0,
                ),
                
                # Navigation links
                nav_links,
                
               
                # Add separator before online users section
                rio.Separator(
                    color=rio.Color.from_hex("#444444"),
                    margin_y=0.5,
                    margin_top=2,
                ),
                
                # Sessions component that shows active users
                SidebarSessions(),
                
                # Spacer that pushes everything up
                rio.Spacer(),
                
                align_y=0,
                min_width=14 if device == "desktop" else 12,
                min_height=100,
                margin=0.5,
            ),
            fill=theme.NEUTRAL_COLOR_DARKER,
            stroke_width=0,
            corner_radius=0,
            min_height=100,
            # Position it at the left side of the screen
            align_x=0,
            align_y=0,
        )
        
        # Wrap the sidebar content in an overlay so it stays fixed
        return rio.Overlay(
            content=rio.Container(
                content=sidebar_content,
                align_x=0,  # Left align
                align_y=0,  # Top align
            )
        ) 