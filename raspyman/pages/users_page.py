from __future__ import annotations

import typing as t
import rio

from .. import theme, utils, data_models
from ..components.crud_list import CRUDList

@rio.page(
    name="Users",
    url_segment="users",
)
class UsersPage(rio.Component):
    """
    Page for managing user accounts in Retro AIM Server.
    
    This page provides a CRUD interface for user accounts, allowing administrators to:
    - View a list of all users
    - Create new user accounts
    - Update user account details (suspended status)
    - Delete user accounts
    - Reset user passwords
    """
    
    # User list and selection state
    users: t.List[data_models.User] = []
    
    # Notification banner state
    banner_text: str = ""
    banner_style: t.Literal["success", "danger", "info", "warning"] = "success"
    
    # Loading and error states
    is_loading: bool = False
    has_error: bool = False
    
    @rio.event.on_populate
    async def on_populate(self) -> None:
        """
        Load the list of users when the page is populated.
        """
        await self.load_users()
    
    async def load_users(self) -> None:
        """
        Load the list of users from the RAS API.
        """
        self.is_loading = True
        self.has_error = False
        
        # Fetch users from the API
        users = await utils.fetch_users(self.session)
        
        self.is_loading = False
        if users is None:
            # API call failed
            self.has_error = True
            self.banner_text = "Failed to load users. Check API connection."
            self.banner_style = "danger"
        else:
            # API call successful, even if the list is empty
            self.users = users
            
            # Clear any previous banner if the API call was successful
            if self.banner_text and self.banner_style == "danger":
                self.banner_text = ""
    
    async def on_press_delete_user(self, user: data_models.User) -> None:
        """
        Handle the delete user button press.
        
        Args:
            user: The user to delete
        """
        screen_name = user.screen_name
        
        # Show confirmation dialog
        result = await self.session.show_yes_no_dialog(
            title="Confirm Delete",
            text=f"Are you sure you want to delete user '{screen_name}'? This action cannot be undone.",
            yes_text="Delete",
            no_text="Cancel",
            yes_color="danger",
        )
        
        if result:
            # User confirmed deletion
            success = await utils.delete_user(self.session, screen_name)
            
            if success:
                # Remove the user from the local list
                self.users = [user for user in self.users if user.screen_name != screen_name]
                self.banner_text = f"User '{screen_name}' deleted successfully"
                self.banner_style = "success"
            else:
                self.banner_text = f"Failed to delete user '{screen_name}'"
                self.banner_style = "danger"
    
    async def on_press_reset_password(self, user: data_models.User) -> None:
        """
        Handle the reset password button press.
        
        Args:
            user: The user to reset the password for
        """
        screen_name = user.screen_name
        
        # Create a dialog for password reset
        new_password = ""
        
        def build_dialog_content() -> rio.Component:
            return rio.Column(
                rio.Text(
                    text=f"Reset Password for {screen_name}",
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
            success = await utils.reset_user_password(self.session, screen_name, new_password)
            
            if success:
                self.banner_text = f"Password for '{screen_name}' reset successfully"
                self.banner_style = "success"
            else:
                self.banner_text = f"Failed to reset password for '{screen_name}'"
                self.banner_style = "danger"
    
    async def on_create_new_user(self) -> None:
        """
        Handle the create new user button press.
        """
        # For creating a new user
        new_user = {
            "screen_name": "",
            "password": "",
            "is_icq": False,
        }
        
        def build_dialog_content() -> rio.Component:
            return rio.Column(
                rio.Text(
                    text="Create New User",
                    style="heading2",
                    margin_bottom=1,
                ),
                rio.TextInput(
                    new_user["screen_name"],
                    label="Screen Name",
                    on_change=on_change_screen_name,
                ),
                rio.TextInput(
                    new_user["password"],
                    label="Password",
                    is_secret=True,
                    on_change=on_change_password,
                ),
                rio.Row(
                    rio.Checkbox(
                        new_user["is_icq"],
                        on_change=on_change_is_icq,
                    ),
                    rio.Text("ICQ User"),
                    spacing=0.5,
                ),
                rio.Row(
                    rio.Button(
                        "Create User",
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
        
        def on_change_screen_name(ev: rio.TextInputChangeEvent) -> None:
            new_user["screen_name"] = ev.text
        
        def on_change_password(ev: rio.TextInputChangeEvent) -> None:
            new_user["password"] = ev.text
        
        def on_change_is_icq(ev: rio.CheckboxChangeEvent) -> None:
            new_user["is_icq"] = ev.is_on
        
        # Show the dialog
        dialog = await self.session.show_custom_dialog(
            build=build_dialog_content,
            modal=True,
        )
        
        # Wait for the user's decision
        result = await dialog.wait_for_close()
        
        if result and new_user["screen_name"] and new_user["password"]:
            # User confirmed user creation
            success = await utils.create_user(
                self.session, 
                new_user["screen_name"], 
                new_user["password"]
            )
            
            if success:
                self.banner_text = f"User '{new_user['screen_name']}' created successfully"
                self.banner_style = "success"
                
                # Reload the user list to include the new user
                await self.load_users()
            else:
                self.banner_text = f"Failed to create user '{new_user['screen_name']}'"
                self.banner_style = "danger"
    
    async def on_update_user_status(self, user: data_models.User) -> None:
        """
        Handle the update user status button press.
        
        Args:
            user: The user to update the status for
        """
        # For updating user status
        suspended_status_options = [
            ("Active", None),
            ("Deleted", "deleted"),
            ("Expired", "expired"),
            ("Suspended", "suspended"),
            ("Suspended (Age)", "suspended_age")
        ]
        
        # Find the current status in the options
        current_status = user.suspended_status
        selected_status = next(
            (option for option in suspended_status_options if option[1] == current_status), 
            suspended_status_options[0]
        )
        
        # For capturing the updated status
        updated_status = {
            "value": selected_status[1]
        }
        
        def build_dialog_content() -> rio.Component:
            return rio.Column(
                rio.Text(
                    text=f"Update Status for {user.screen_name}",
                    style="heading2",
                    margin_bottom=1,
                ),
                rio.Dropdown(
                    options=[option[0] for option in suspended_status_options],
                    label="Account Status",
                    selected_value=selected_status[0],
                    on_change=on_change_status,
                ),
                rio.Row(
                    rio.Button(
                        "Update Status",
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
        
        def on_change_status(ev: rio.DropdownChangeEvent) -> None:
            # Find the suspended_status value based on the selected display text
            selected_index = next(
                (i for i, option in enumerate(suspended_status_options) if option[0] == ev.value), 
                0
            )
            updated_status["value"] = suspended_status_options[selected_index][1]
        
        # Show the dialog
        dialog = await self.session.show_custom_dialog(
            build=build_dialog_content,
            modal=True,
        )
        
        # Wait for the user's decision
        result = await dialog.wait_for_close()
        
        if result:
            # User confirmed status update
            success = await utils.update_user_status(
                self.session, 
                user.screen_name, 
                updated_status["value"]
            )
            
            if success:
                # Update the local user object with the new status
                user.suspended_status = updated_status["value"]
                
                # Update the user in the users list
                for i, u in enumerate(self.users):
                    if u.screen_name == user.screen_name:
                        self.users[i] = user
                        break
                
                status_display = next(
                    (option[0] for option in suspended_status_options if option[1] == updated_status["value"]), 
                    "Active"
                )
                self.banner_text = f"Status for '{user.screen_name}' updated to {status_display}"
                self.banner_style = "success"
            else:
                self.banner_text = f"Failed to update status for '{user.screen_name}'"
                self.banner_style = "danger"
    
    def build(self) -> rio.Component:
        """
        Build the users page UI.
        """
        # Define the action buttons for each user
        action_buttons = [
            {
                "icon": "material/edit",
                "color": "primary",
                "tooltip": "Editing User Account Status isn't available in this version of RAS",
                "callback": self.on_update_user_status,
                "is_sensitive": False,  # Disable the button
            },
            {
                "icon": "material/password",
                "color": "secondary",
                "tooltip": "Reset Password",
                "callback": self.on_press_reset_password,
            },
            {
                "icon": "material/delete",
                "color": "danger",
                "tooltip": "Delete User",
                "callback": self.on_press_delete_user,
            },
        ]
        
        # Create a description text (without the title)
        description = rio.Text(
            "Manage all user accounts. Create new users, reset passwords, update user status, or delete accounts.",
            style=rio.TextStyle(
                font_size=1.1,
                fill=theme.TEXT_FILL_DARKER,
                italic=True,
            ),
            margin_bottom=1,
        )
        
        # Create the CRUD list with configurations for users
        users_list = CRUDList[data_models.User](
            # Data and state
            items=self.users,
            is_loading=self.is_loading,
            has_error=self.has_error,
            error_message="Failed to load users. Check API connection.",
            
            # Banner state
            banner_text=self.banner_text,
            banner_style=self.banner_style,
            
            # List configuration
            title="User Accounts",  # Move title here
            create_item_text="Create New User",
            create_item_description="Add a new user account",
            create_item_icon="material/person_add",
            
            # Item display configuration
            item_key_attr="id",
            item_text_attr="screen_name",
            item_description_attr="display_description",  # Will be handled with a property
            item_icon="material/person",
            
            # Callbacks
            on_create_item=self.on_create_new_user,
            on_refresh=self.load_users,
            
            # Action buttons
            action_buttons=action_buttons,
        )
        
        # Return the final layout
        return rio.Column(
            description,
            users_list,
            spacing=0,
            align_y=0,
            grow_x=True,
            grow_y=True,
        ) 