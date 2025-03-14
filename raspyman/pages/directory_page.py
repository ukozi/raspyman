from __future__ import annotations

import typing as t
import rio

from .. import theme, utils, data_models
from ..components.crud_list import CRUDList

@rio.page(
    name="Directory",
    url_segment="directory",
)
class DirectoryPage(rio.Component):
    """
    Page for managing the AIM Directory in Retro AIM Server.
    
    This page provides a view of directory categories and keywords, allowing administrators to:
    - View a list of all categories
    - Click on categories to view and manage their keywords
    - Create new categories and keywords
    - Delete categories and keywords
    - Manage uncategorized keywords
    """
    
    # Directory items list and state
    categories: t.List[data_models.Category] = []
    
    # Notification banner state
    banner_text: str = ""
    banner_style: t.Literal["success", "danger", "info", "warning"] = "success"
    
    # Loading and error states
    is_loading: bool = False
    has_error: bool = False
    
    # Dictionary to store keywords by category ID
    category_keywords: dict[int, t.List[data_models.Keyword]] = {}
    # Dictionary to store loading states by category ID
    category_loading: dict[int, bool] = {}
    
    # Track the currently selected category
    selected_category_id: int = 0
    
    def __post_init__(self) -> None:
        """Initialize component state."""
        # Default to showing uncategorized keywords
        self.selected_category_id = 0
    
    @rio.event.on_populate
    async def on_populate(self) -> None:
        """
        Load directory categories when the page is populated.
        """
        await self.load_directory_items()
        
        # Pre-load uncategorized keywords for faster access
        self.category_loading[0] = True
        self.session.create_task(self.load_uncategorized_keywords())
    
    async def load_directory_items(self) -> None:
        """
        Load directory categories from the RAS API.
        """
        self.is_loading = True
        self.has_error = False
        
        # Fetch categories from the API
        items = await utils.fetch_directory_categories(self.session)
        
        self.is_loading = False
        if items is None:
            self.has_error = True
            self.banner_text = "Failed to load directory categories. Check API connection."
            self.banner_style = "danger"
        else:
            self.categories = items
            # Add display description for categories
            for category in self.categories:
                setattr(category, "display_description", 
                        f"Category ID: {category.id}")
            
            # Clear any previous banner if successful
            if self.banner_text and self.banner_style == "danger":
                self.banner_text = ""
    
    async def load_keywords_for_category(self, category_id):
        """
        Load keywords for a specific category.
        
        Args:
            category_id: The ID of the category to load keywords for
        """
        try:
            keywords = await utils.fetch_directory_keywords(self.session, category_id) or []
            
            # Add display description for keywords
            for keyword in keywords:
                setattr(keyword, "display_description", 
                        f"Keyword ID: {keyword.id} • Category ID: {category_id}")
            
            # Store the keywords and update loading state
            self.category_keywords[category_id] = keywords
            self.category_loading[category_id] = False
            
            # Force a refresh to update the UI
            self.force_refresh()
            
            return keywords
        except Exception as e:
            # Mark the category as not loading, but don't clear any existing keywords
            self.category_loading[category_id] = False
            self.force_refresh()
            return []
    
    async def load_uncategorized_keywords(self):
        """
        Load keywords that don't have a category assigned (category_id=0).
        """
        try:
            keywords = await utils.fetch_directory_keywords(self.session, 0) or []
            
            # Add display description for keywords
            for keyword in keywords:
                setattr(keyword, "display_description", 
                        f"Keyword ID: {keyword.id} • Uncategorized")
            
            # Store the keywords 
            self.category_keywords[0] = keywords
            self.category_loading[0] = False
            
            # Force a refresh to update the UI
            self.force_refresh()
            
            return keywords
        except Exception as e:
            # Mark as not loading, but don't clear any existing keywords
            self.category_loading[0] = False
            self.force_refresh()
            return []
    
    async def on_delete_category(self, category: data_models.Category) -> None:
        """
        Delete a directory category.
        
        Args:
            category: The category to delete
        """
        # Show confirmation dialog
        result = await self.session.show_yes_no_dialog(
            title="Confirm Delete",
            text=f"Are you sure you want to delete category '{category.name}'? This will also delete all keywords in this category.",
            yes_text="Delete",
            no_text="Cancel",
            yes_color="danger",
        )
        
        if result:
            # User confirmed deletion
            success = await utils.delete_directory_category(self.session, category.id)
            
            if success:
                # Remove the category from the local list
                self.categories = [c for c in self.categories if c.id != category.id]
                self.banner_text = f"Category '{category.name}' deleted successfully"
                self.banner_style = "success"
                
                # If the deleted category was selected, switch to uncategorized
                if self.selected_category_id == category.id:
                    self.select_category_by_id(0)
            else:
                self.banner_text = f"Failed to delete category '{category.name}'"
                self.banner_style = "danger"
    
    async def on_delete_keyword(self, keyword: data_models.Keyword) -> None:
        """
        Delete a directory keyword.
        
        Args:
            keyword: The keyword to delete
        """
        # Show confirmation dialog
        result = await self.session.show_yes_no_dialog(
            title="Confirm Delete",
            text=f"Are you sure you want to delete keyword '{keyword.name}'?",
            yes_text="Delete",
            no_text="Cancel",
            yes_color="danger",
        )
        
        if result:
            # User confirmed deletion
            success = await utils.delete_directory_keyword(self.session, keyword.id)
            
            if success:
                # Get the category ID 
                category_id = keyword.category_id
                
                # Remove the keyword from our local cache if it exists
                if category_id in self.category_keywords:
                    self.category_keywords[category_id] = [
                        k for k in self.category_keywords[category_id] 
                        if k.id != keyword.id
                    ]
                
                self.banner_text = f"Keyword '{keyword.name}' deleted successfully"
                self.banner_style = "success"
                
                # Force refresh to update the UI
                self.force_refresh()
            else:
                self.banner_text = f"Failed to delete keyword '{keyword.name}'"
                self.banner_style = "danger"
    
    async def on_create_category(self) -> None:
        """
        Create a new directory category.
        """
        # For creating a new category
        new_category = {
            "name": "",
        }
        
        def build_dialog_content() -> rio.Component:
            return rio.Column(
                rio.Text(
                    text="Create New Category",
                    style="heading2",
                    margin_bottom=1,
                ),
                rio.TextInput(
                    new_category["name"],
                    label="Category Name",
                    on_change=on_change_name,
                ),
                rio.Row(
                    rio.Button(
                        "Create Category",
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
            new_category["name"] = ev.text
        
        # Show the dialog
        dialog = await self.session.show_custom_dialog(
            build=build_dialog_content,
            modal=True,
        )
        
        # Wait for the user's decision
        result = await dialog.wait_for_close()
        
        if result and new_category["name"]:
            # User confirmed category creation
            success = await utils.create_directory_category(self.session, new_category["name"])
            
            if success:
                self.banner_text = f"Category '{new_category['name']}' created successfully"
                self.banner_style = "success"
                
                # Reload the categories to include the new one
                await self.load_directory_items()
            else:
                self.banner_text = f"Failed to create category '{new_category['name']}'"
                self.banner_style = "danger"
    
    async def on_create_keyword(self, category_id: int = None) -> None:
        """
        Create a new directory keyword.
        
        Args:
            category_id: Optional ID of the category to pre-select
        """
        # For creating a new keyword
        new_keyword = {
            "name": "",
            "category_id": category_id or 0,
        }
        
        # Get all categories for parent selection
        categories = await utils.fetch_directory_categories(self.session)
        
        if not categories:
            # Show error if no categories are available
            self.banner_text = "Cannot create keyword: No categories available"
            self.banner_style = "danger"
            return
        
        def build_dialog_content() -> rio.Component:
            # Find the correct default selection based on category_id
            default_selection = None
            
            # Handle the uncategorized case (category_id=0)
            if category_id == 0:
                default_selection = "Uncategorized (ID: 0)"
            elif category_id:
                # Find the category with matching ID
                for cat in categories:
                    if cat.id == category_id:
                        default_selection = f"{cat.name} (ID: {cat.id})"
                        break
                
                if not default_selection:
                    pass
            
            # If no match found or no category_id provided, use first category as default
            if not default_selection and categories:
                default_selection = f"{categories[0].name} (ID: {categories[0].id})"
            
            # Create options list with Uncategorized as the first option
            dropdown_options = ["Uncategorized (ID: 0)"] + [f"{c.name} (ID: {c.id})" for c in categories]
            
            return rio.Column(
                rio.Text(
                    text="Create New Keyword",
                    style="heading2",
                    margin_bottom=1,
                ),
                rio.TextInput(
                    new_keyword["name"],
                    label="Keyword Name",
                    on_change=on_change_name,
                ),
                rio.Dropdown(
                    options=dropdown_options,
                    label="Parent Category",
                    selected_value=default_selection,
                    on_change=on_change_parent,
                ),
                rio.Row(
                    rio.Button(
                        "Create Keyword",
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
            new_keyword["name"] = ev.text
        
        def on_change_parent(ev: rio.DropdownChangeEvent) -> None:
            # Extract the ID from the selection string
            selected_value = ev.value
            # Parse the ID from the string format "Category Name (ID: 123)"
            if selected_value and "ID:" in selected_value:
                try:
                    # Extract just the ID part from the string
                    id_part = selected_value.split("ID:")[1].strip().rstrip(")")
                    category_id = int(id_part)
                    new_keyword["category_id"] = category_id
                except (ValueError, IndexError):
                    pass
        
        # Initialize parent ID with the default based on input param
        if category_id is not None:
            new_keyword["category_id"] = category_id
        elif categories:
            new_keyword["category_id"] = categories[0].id
        
        # Show the dialog
        dialog = await self.session.show_custom_dialog(
            build=build_dialog_content,
            modal=True,
        )
        
        # Wait for the user's decision
        result = await dialog.wait_for_close()
        
        if result and new_keyword["name"]:
            # User confirmed keyword creation
            success = await utils.create_directory_keyword(
                self.session, 
                new_keyword["name"],
                new_keyword["category_id"]
            )
            
            if success:
                self.banner_text = f"Keyword '{new_keyword['name']}' created successfully"
                self.banner_style = "success"
                
                # Mark this category as loading so it will show the loading state
                cat_id = new_keyword["category_id"]
                self.category_loading[cat_id] = True
                
                # Force a refresh to show the loading state
                self.force_refresh()
                
                # Reload just this category's keywords and update the UI
                await self.load_keywords_for_category(cat_id)
                
                # Force refresh one more time after data is loaded
                self.force_refresh()
            else:
                self.banner_text = f"Failed to create keyword '{new_keyword['name']}'"
                self.banner_style = "danger"
    
    def select_category(self, category: data_models.Category) -> None:
        """
        Select a category to view its keywords.
        
        Args:
            category: The category to select
        """
        self.select_category_by_id(category.id)
    
    def select_category_by_id(self, category_id: int) -> None:
        """
        Select a category by ID.
        
        Args:
            category_id: The ID of the category to select
        """
        # Store the selected category ID
        self.selected_category_id = category_id
        
        # Ensure keywords are loaded for this category
        if category_id not in self.category_keywords:
            self.category_loading[category_id] = True
            
            # Load keywords for this category
            if category_id == 0:
                self.session.create_task(self.load_uncategorized_keywords())
            else:
                self.session.create_task(self.load_keywords_for_category(category_id))
        
        # Force refresh to update the UI
        self.force_refresh()
    
    async def refresh_keywords_for_category(self, category_id: int) -> None:
        """
        Refresh the keywords for a specific category.
        
        Args:
            category_id: The ID of the category to refresh keywords for
        """
        # Set loading state for this category
        self.category_loading[category_id] = True
        self.force_refresh()
        
        # Load keywords for this category
        if category_id == 0:
            await self.load_uncategorized_keywords()
        else:
            await self.load_keywords_for_category(category_id)
        
        # Update any dialogs that may be showing
        self.force_refresh()
    
    async def delete_current_category(self) -> None:
        """
        Delete the currently selected category.
        This is triggered from the category options in the SwitcherBar.
        """
        # Can't delete the Uncategorized category
        if self.selected_category_id == 0:
            return
        
        # Find the category from our list
        category = None
        for cat in self.categories:
            if cat.id == self.selected_category_id:
                category = cat
                break
        
        if category:
            await self.on_delete_category(category)
    
    def build(self) -> rio.Component:
        """
        Build the directory page UI with a SwitcherBar for category selection.
        
        Returns:
            Single-card layout with SwitcherBar and CRUDList for the directory page
        """
        # Action buttons for keywords
        keyword_action_buttons = [
            {
                "icon": "material/delete",
                "color": "danger",
                "tooltip": "Delete Keyword",
                "callback": self.on_delete_keyword,
            },
        ]
        
        # DETAIL PANEL - Get the selected category's name
        selected_category_id = self.selected_category_id
        selected_category_name = "Uncategorized"
        
        # Find the display name for the selected category
        if selected_category_id > 0:
            for category in self.categories:
                if category.id == selected_category_id:
                    selected_category_name = category.name
                    break
        
        # Get keywords for the selected category
        keywords = self.category_keywords.get(selected_category_id, [])
        is_loading_keywords = self.category_loading.get(selected_category_id, True)
        
        # Create a title with quotes around the category name (except for Uncategorized)
        detail_title = "Uncategorized Keywords" if selected_category_id == 0 else f'Keywords in "{selected_category_name}"'
        
        # Prepare SwitcherBar values and names
        switcher_values = [0]  # Start with Uncategorized (ID 0)
        switcher_names = ["Uncategorized"]
        switcher_icons = ["material/tag"]  # Icon for Uncategorized
        
        # Add category values, names, and icons
        for category in self.categories:
            switcher_values.append(category.id)
            switcher_names.append(category.name)
            switcher_icons.append("material/category:fill")
        
        # Create "Add Category" button as an IconButton
        add_category_button = rio.Tooltip(
            rio.IconButton(
                icon="material/add",
                color="primary",
                style="colored-text",
                on_press=self.on_create_category,
                min_size=2.2,
            ),
        
            tip="Add New Category"
        )
        
        # Create "Delete Category" button as an IconButton
        delete_category_button = rio.Tooltip(
            rio.IconButton(
                icon="material/delete",
                color="danger",
                style="colored-text",
                on_press=lambda: self.session.create_task(self.delete_current_category()),
                is_sensitive=selected_category_id != 0,  # Only enable for real categories, not uncategorized
                min_size=1.8,
            ),
            tip="Delete the current category"
        )
        
        # Row for category management buttons
        category_management_row = rio.Row(
            rio.Spacer(),
            add_category_button,
            delete_category_button,
            spacing=0.5,
            grow_x=True,
        )
        
        # Function to handle SwitcherBar change events
        def on_switcher_change(event: rio.SwitcherBarChangeEvent) -> None:
            # Convert to int as the category ID is an integer
            category_id = 0 if event.value is None else int(event.value)
            self.select_category_by_id(category_id)
        
        # Create the SwitcherBar for category selection and wrap it in a ScrollContainer
        category_switcher = rio.ScrollContainer(
            rio.SwitcherBar(
                values=switcher_values,
                names=switcher_names,
                icons=switcher_icons,
                selected_value=selected_category_id,
                color="primary",
                orientation="horizontal",
                on_change=on_switcher_change,
                spacing=0.2,  # Much smaller spacing between items (default is 1.0)
                margin_left=2,
                margin_right=2,
                margin_top=.5
            ),
            scroll_x="auto",
            scroll_y="never",
        )
        
        # DETAIL PANEL - Keywords list
        keywords_list = CRUDList[data_models.Keyword](
            # Data and state
            items=keywords,
            is_loading=is_loading_keywords,
            has_error=False,
            
            # Banner state
            banner_text=self.banner_text,
            banner_style=self.banner_style,
            
            # List configuration
            title=detail_title,
            create_item_text=f"Add {'Uncategorized' if selected_category_id == 0 else ''} Keyword",
            create_item_description=f"Add a new keyword {'without a category' if selected_category_id == 0 else f'to the {selected_category_name} category'}",
            create_item_icon="material/tag",
            
            # Item display configuration
            item_key_attr="id",
            item_text_attr="name",
            item_description_attr="display_description",
            item_icon="material/tag",
            item_icon_default_color="warning" if selected_category_id == 0 else "secondary",
            
            # Callbacks
            on_create_item=lambda: self.on_create_keyword(selected_category_id),
            on_refresh=lambda: self.refresh_keywords_for_category(selected_category_id),
            
            # Action buttons
            action_buttons=keyword_action_buttons,
        )
        
        # Return the final layout
        return rio.Column(
            # Header section at the top of the page
            rio.Text(
                "Directory",
                style="heading1",
                margin_bottom=2,
            ),
            
            # FIRST CARD: Categories section
            rio.Card(
                rio.Column(
                    # Categories title and action buttons in the same row
                    rio.Row(
                        rio.Text(
                            "Categories",
                            style=rio.TextStyle(
                                font_size=1.5,
                                font_weight="bold",
                            ),
                        ),
                        rio.Spacer(),
                        add_category_button,
                        delete_category_button,
                        spacing=0.5,
                        align_y=0.5,
                        grow_x=True,
                    ),
                    category_switcher,
                    spacing=0.5,
                    margin=2,  # Match CRUDList inner margin
                ),
                grow_x=True,  # Match CRUDList card's grow behavior
                margin_bottom=1,   # Margin for the card
            ),
            
            # Keywords CRUDList section (directly placed, no Container needed)
            keywords_list,
            spacing=0.5,
            align_y=0,
            grow_x=True,
            grow_y=True,
        ) 