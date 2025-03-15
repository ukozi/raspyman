import typing as t
import rio

from .. import theme

T = t.TypeVar("T")

class CRUDList(rio.Component, t.Generic[T]):
    """
    A reusable CRUD list component that can be used to display and manage a list of items.
    
    This component handles common CRUD operations and provides a consistent UI across
    different types of data.
    
    Attributes:
        items: List of items to display
        is_loading: Whether the list is currently loading
        has_error: Whether there was an error loading the list
        error_message: Error message to display
        banner_text: Text to display in the banner
        banner_style: Style of the banner
        title: Title to display at the top of the list
        create_item_text: Text for the create item button
        create_item_description: Description for the create item button
        create_item_icon: Icon for the create item button
        item_key_attr: Attribute name to use for item keys
        item_text_attr: Attribute name to use for item text
        item_description_attr: Attribute name to use for item descriptions
        item_icon: Icon to use for items
        item_icon_color_attr: Attribute name to get item icon color
        item_icon_default_color: Default color for item icons
        on_create_item: Function to call when creating a new item
        on_refresh: Function to call when refreshing the list
        on_item_press: Function to call when an item is clicked
        action_buttons: List of action buttons to display for each item
        header_buttons: List of additional buttons to display in the header
    """
    
    # Data and state
    items: t.List[T] = []
    is_loading: bool = False
    has_error: bool = False
    error_message: str = "Failed to load items. Check API connection."
    
    # Banner for notifications
    banner_text: str = ""
    banner_style: t.Literal["success", "danger", "info", "warning"] = "success"
    
    # List configuration
    title: str = "Items"
    create_item_text: str = "Create New Item"
    create_item_description: str = "Add a new item"
    create_item_icon: str = "material/add"
    
    # Item display configuration
    item_key_attr: str = "id"
    item_text_attr: str = "name"
    item_description_attr: str = "description"
    item_icon: str = "material/description"
    item_icon_color_attr: t.Optional[str] = None
    item_icon_default_color: str = "primary"
    
    # Callbacks
    on_create_item: t.Optional[t.Callable[[], t.Awaitable[None]]] = None
    on_refresh: t.Optional[t.Callable[[], t.Awaitable[None]]] = None
    on_item_press: t.Optional[t.Callable[[T], t.Awaitable[None]]] = None
    
    # Action buttons
    action_buttons: t.List[t.Dict[str, t.Any]] = []
    
    # Header buttons
    header_buttons: t.List[rio.Component] = []
    
    def _get_singular_form(self, plural: str) -> str:
        """
        Get the singular form of a plural word, handling irregular plurals.
        
        Args:
            plural: The plural form of the word
            
        Returns:
            The singular form of the word
        """
        # Special cases for irregular plurals
        irregular_plurals = {
            "categories": "category",
            "properties": "property",
            "activities": "activity",
            "histories": "history",
            "entries": "entry",
            "countries": "country",
            "policies": "policy",
            # Add more irregular plurals as needed
        }
        
        # Check if the lowercase version is in our irregular plurals dictionary
        lowercase_plural = plural.lower()
        if lowercase_plural in irregular_plurals:
            # Preserve the case of the first letter
            singular = irregular_plurals[lowercase_plural]
            if plural[0].isupper():
                return singular.capitalize()
            return singular
        
        # Handle regular plurals (ending with 's')
        if lowercase_plural.endswith('s'):
            return plural[:-1]
        
        # If not a plural or not recognized, return as is
        return plural
            
    def build(self) -> rio.Component:
        """Build the CRUD list UI."""
        # Create the list items for each item
        list_items = []
        
        # Add the "Create New" item at the top if a create callback is provided
        if self.on_create_item:
            list_items.append(
                rio.SimpleListItem(
                    text=self.create_item_text,
                    secondary_text=self.create_item_description,
                    key="create_new",
                    left_child=rio.Icon(self.create_item_icon),
                    on_press=lambda: self.session.create_task(self.on_create_item()),
                )
            )
        
        # Add items for each item in the list
        for item in self.items:
            # Get item properties
            item_key = getattr(item, self.item_key_attr, str(id(item)))
            item_text = getattr(item, self.item_text_attr, str(item))
            item_description = getattr(item, self.item_description_attr, "")
            
            # Get icon color if specified
            icon_color = self.item_icon_default_color
            if self.item_icon_color_attr and hasattr(item, self.item_icon_color_attr):
                icon_color = getattr(item, self.item_icon_color_attr)
            
            # Create action buttons for this item
            item_buttons = []
            for button_config in self.action_buttons:
                # Create a copy of the callback with this specific item
                callback = button_config.get("callback")
                icon = button_config.get("icon", "material/edit")
                color = button_config.get("color", "primary")
                tooltip = button_config.get("tooltip", "Action")
                is_sensitive = button_config.get("is_sensitive", True)
                
                if callback:
                    button = rio.Tooltip(
                        rio.Button(
                            rio.Icon(icon, margin=0.5),
                            color=color,
                            style="colored-text",
                            align_y=0.5,
                            is_sensitive=is_sensitive,
                            on_press=lambda item=item, cb=callback: self.session.create_task(cb(item)),
                        ),
                        tooltip,
                    )
                    item_buttons.append(button)
            
            # Create row for buttons if any
            right_child = None
            if item_buttons:
                right_child = rio.Row(
                    *item_buttons,
                    spacing=0.5,
                )
            
            # Create list item with on_press callback if provided
            list_item_on_press = None
            if self.on_item_press:
                list_item_on_press = lambda item=item: self.session.create_task(self.on_item_press(item))
            
            # Create list item
            list_items.append(
                rio.SimpleListItem(
                    text=item_text,
                    secondary_text=item_description,
                    key=item_key,
                    left_child=rio.Icon(
                        self.item_icon,
                        fill=icon_color,
                    ),
                    right_child=right_child,
                    on_press=list_item_on_press,
                )
            )
        
        # Main content - show loading, error, or item list
        if self.is_loading:
            content = rio.Column(
                rio.ProgressCircle(color="primary"),
                rio.Text(
                    "Loading items...",
                    style=rio.TextStyle(
                        font_size=1.0,
                        fill=theme.TEXT_FILL_DARKER,
                    ),
                    margin_top=1,
                ),
                align_x=0.5,
                align_y=0.5,
                margin=5,
                grow_x=True,
            )
        elif self.has_error:
            content = rio.Column(
                rio.Icon(
                    icon="material/error:fill",
                    fill="danger",
                ),
                rio.Text(
                    self.error_message,
                    style=rio.TextStyle(
                        font_size=1.0,
                        fill=theme.ERROR_COLOR,
                    ),
                    margin_top=1,
                ),
                rio.Button(
                    "Retry",
                    on_press=lambda: self.session.create_task(self.on_refresh()) if self.on_refresh else None,
                    margin_top=2,
                ),
                align_x=0.5,
                align_y=0.5,
                margin=5,
                grow_x=True,
            )
        elif not self.items:
            # Empty state when there are no items but no error
            # Prepare buttons for empty state - only include non-None values
            buttons = []
            
            # Add create button if creation is available
            if self.on_create_item:
                # Get item name (singular form from title)
                if ' ' in self.title:
                    # For multi-word titles like "Directory Categories", handle each word
                    words = self.title.split(' ')
                    last_word = words[-1]  # Get the last word (usually the plural)
                    singular_last_word = self._get_singular_form(last_word)
                    item_name = ' '.join(words[:-1] + [singular_last_word])
                else:
                    # For single word titles
                    item_name = self._get_singular_form(self.title)
                    
                buttons.append(
                    rio.Button(
                        f"Create New {item_name}",
                        icon=self.create_item_icon,
                        on_press=lambda: self.session.create_task(self.on_create_item()),
                        color="primary",
                    )
                )
                
            # Create the empty state content
            empty_state_components = [
                rio.Icon(
                    icon="material/info:fill",
                    fill="neutral",
                ),
                rio.Text(
                    f"No {self.title.lower() if self.title else 'items'} found",
                    style=rio.TextStyle(
                        font_size=1.0,
                        fill=theme.TEXT_FILL_DARKER,
                    ),
                    margin_top=1,
                )
            ]
            
            # Add buttons row only if there are buttons to show
            if buttons:
                empty_state_components.append(
                    rio.Row(
                        *buttons,
                        spacing=0,
                        margin_top=2,
                    )
                )
            
            content = rio.Column(
                *empty_state_components,
                align_x=0.5,
                align_y=0.5,
                margin=5,
                grow_x=True,
            )
        else:
            content = rio.ListView(
                *list_items,
                align_y=0,
                grow_x=True,
            )
        
        # Build the main layout
        # Create a list of children for the inner Column and filter out None values
        
        # Create a list of components for the header row and filter out None values
        header_row_items = [
            rio.Text(
                self.title,
                style=rio.TextStyle(
                    font_size=1.5,
                    font_weight="bold",
                ),
            ),
            rio.Spacer(),
        ]
        
        # Add the refresh button if on_refresh is provided
        if self.on_refresh:
            header_row_items.append(
                rio.Button(
                    "Refresh",
                    icon="material/refresh",
                    style="minor",
                    on_press=lambda: self.session.create_task(self.on_refresh()),
                )
            )
        
        # Add any additional header buttons
        if self.header_buttons:
            # Add a small spacer between the refresh button and additional buttons
            header_row_items.append(
                rio.Container(
                    content=rio.Text(""),
                    margin_left=1,
                )
            )
            
            for button in self.header_buttons:
                header_row_items.append(button)
        
        # Create the header row with the filtered items
        column_children = [
            rio.Row(
                *header_row_items,  # Spread the filtered list elements
                align_y=0.5,
                grow_x=True,
            )
        ]
        
        # Only add the banner if there's text to display
        if self.banner_text:
            column_children.append(
                rio.Banner(
                    self.banner_text,
                    style=self.banner_style,
                    margin_top=1,
                    margin_bottom=1,
                )
            )
        
        # Add the content
        column_children.append(content)
        
        return rio.Column(
            rio.Card(
                content=rio.Column(
                    *column_children,
                    margin=2,
                    spacing=1,
                    align_y=0,
                    grow_x=True,
                ),
                grow_x=True,
            ),
            margin=0,
            align_y=0,
            grow_x=True,
            grow_y=True,
        ) 