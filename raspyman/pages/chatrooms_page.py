from __future__ import annotations

import typing as t
import rio

from .. import theme, utils, data_models
from ..components.crud_list import CRUDList

@rio.page(
    name="Chat Rooms",
    url_segment="chatrooms",
)
class ChatroomsPage(rio.Component):
    """
    Page for managing chat rooms in Retro AIM Server.
    
    This page provides a view of active chat rooms, allowing administrators to:
    - View a list of all active chat rooms
    - Create new chat rooms
    - Delete chat rooms
    """
    
    # Chat rooms list and state
    chat_rooms: t.List[data_models.ChatRoom] = []
    
    # Notification banner state
    banner_text: str = ""
    banner_style: t.Literal["success", "danger", "info", "warning"] = "success"
    
    # Loading and error states
    is_loading: bool = False
    has_error: bool = False
    
    @rio.event.on_populate
    async def on_populate(self) -> None:
        """
        Load the list of chat rooms when the page is populated.
        """
        await self.load_chat_rooms()
    
    async def load_chat_rooms(self) -> None:
        """
        Load the list of active chat rooms from the RAS API.
        """
        self.is_loading = True
        self.has_error = False
        
        # Fetch chat rooms from the API
        chat_rooms = await utils.fetch_chat_rooms(self.session)
        
        self.is_loading = False
        if chat_rooms is None:
            self.has_error = True
            self.banner_text = "Failed to load chat rooms. Check API connection."
            self.banner_style = "danger"
        else:
            self.chat_rooms = chat_rooms
            
            # Add display info for each chat room
            for room in self.chat_rooms:
                # Get participant count
                participant_count = len(room.participants) if hasattr(room, 'participants') and room.participants else 0
                # Format creation time
                creation_time = room.create_time if hasattr(room, 'create_time') else "Unknown"
                # Set description
                setattr(room, "display_description", 
                        f"{participant_count} participants • Created: {creation_time}")
            
            # Clear any previous banner if successful
            if self.banner_text and self.banner_style == "danger":
                self.banner_text = ""
    
    async def on_delete_chat_room(self, room: data_models.ChatRoom) -> None:
        """
        Delete a chat room.
        
        Args:
            room: The chat room to delete
        """
        room_name = room.name
        
        # Show confirmation dialog
        result = await self.session.show_yes_no_dialog(
            title="Confirm Delete",
            text=f"Are you sure you want to delete chat room '{room_name}'? This will remove the room and disconnect all participants.",
            yes_text="Delete",
            no_text="Cancel",
            yes_color="danger",
        )
        
        if result:
            # User confirmed deletion
            success = await utils.delete_chat_room(self.session, room_name)
            
            if success:
                # Remove the chat room from the local list
                self.chat_rooms = [r for r in self.chat_rooms if r.name != room_name]
                self.banner_text = f"Chat room '{room_name}' deleted successfully"
                self.banner_style = "success"
            else:
                self.banner_text = f"Failed to delete chat room '{room_name}'"
                self.banner_style = "danger"
    
    async def on_create_chat_room(self) -> None:
        """
        Create a new chat room.
        """
        # For creating a new chat room
        new_room = {
            "name": "",
        }
        
        def build_dialog_content() -> rio.Component:
            return rio.Column(
                rio.Text(
                    text="Create New Chat Room",
                    style="heading2",
                    margin_bottom=1,
                ),
                rio.TextInput(
                    new_room["name"],
                    label="Room Name",
                    on_change=on_change_name,
                ),
                rio.Row(
                    rio.Button(
                        "Create Room",
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
        
        def on_change_name(ev: rio.TextInputChangeEvent) -> None:
            new_room["name"] = ev.text
        
        # Show the dialog
        dialog = await self.session.show_custom_dialog(
            build=build_dialog_content,
            modal=True,
        )
        
        # Wait for the user's decision
        result = await dialog.wait_for_close()
        
        if result and new_room["name"]:
            # User confirmed room creation
            success = await utils.create_chat_room(self.session, new_room["name"])
            
            if success:
                self.banner_text = f"Chat room '{new_room['name']}' created successfully"
                self.banner_style = "success"
                
                # Reload the chat room list to include the new room
                await self.load_chat_rooms()
            else:
                self.banner_text = f"Failed to create chat room '{new_room['name']}'"
                self.banner_style = "danger"
    
    def build(self) -> rio.Component:
        """
        Build the chat rooms page UI.
        """
        # Define the action buttons for each chat room
        action_buttons = [
            {
                "icon": "material/delete",
                "color": "danger",
                "tooltip": "Deleting Chat Rooms isn't available in this version of RAS",
                "callback": self.on_delete_chat_room,
                "is_sensitive": False,  # Disable the button
            },
        ]
        
        # Create a description text (without the title)
        description = rio.Text(
            "View and manage active chat rooms. Create new rooms or remove existing ones.",
            style=rio.TextStyle(
                font_size=1.1,
                fill=theme.TEXT_FILL_DARKER,
                italic=True,
            ),
            margin_bottom=1,
        )
        
        # Create the CRUD list with configurations for chat rooms
        chat_rooms_list = CRUDList[data_models.ChatRoom](
            # Data and state
            items=self.chat_rooms,
            is_loading=self.is_loading,
            has_error=self.has_error,
            error_message="Failed to load chat rooms. Check API connection.",
            
            # Banner state
            banner_text=self.banner_text,
            banner_style=self.banner_style,
            
            # List configuration
            title="Chat Rooms",  # Move title here
            create_item_text="Create New Chat Room",
            create_item_description="Create a new chat room",
            create_item_icon="material/chat",
            
            # Item display configuration
            item_key_attr="name",
            item_text_attr="name",
            item_description_attr="display_description",
            item_icon="material/chat",
            item_icon_default_color="secondary",
            
            # Callbacks
            on_create_item=self.on_create_chat_room,
            on_refresh=self.load_chat_rooms,
            
            # Action buttons
            action_buttons=action_buttons,
        )
        
        # Return the final layout
        return rio.Column(
            description,
            chat_rooms_list,
            spacing=0,
            align_y=0,
            grow_x=True,
            grow_y=True,
        ) 