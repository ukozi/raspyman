import rio

# Define color constants that'll be used across the app
TEXT_FILL_BRIGHTER = rio.Color.from_hex("#ffffff")
TEXT_FILL = rio.Color.from_hex("#333333")
TEXT_FILL_DARKER = rio.Color.from_hex("#666666")

PRIMARY_COLOR = rio.Color.from_hex("#ffae00")
ERROR_COLOR = rio.Color.from_hex("#e74c3c")
NEUTRAL_COLOR = rio.Color.from_hex("#e6e6e6")
NEUTRAL_COLOR_DARKER = rio.Color.from_hex("#1a1a1a")
NEUTRAL_COLOR_BRIGHTER = rio.Color.from_hex("#f5f5f5")
BACKGROUND_COLOR = rio.Color.from_hex("#ffffff")
disabled_color=rio.Color.from_hex('a1a1a1')

# Create a basic theme using pair_from_colors
# Based on actual Rio documentation
light_theme, dark_theme = rio.Theme.pair_from_colors(
    primary_color=PRIMARY_COLOR,
    background_color=BACKGROUND_COLOR,
    neutral_color=NEUTRAL_COLOR,
    danger_color=ERROR_COLOR,
    disabled_color=disabled_color,
    corner_radius_small=0.4,
    corner_radius_medium=0.8,
    corner_radius_large=1.2,
)

# Use the light theme as our admin theme
ADMIN_THEME = light_theme

# Common text styles
DARK_TEXT = rio.TextStyle(
    fill=TEXT_FILL_DARKER,
    font_size=1.0,
)

DARK_TEXT_BIGGER = rio.TextStyle(
    fill=TEXT_FILL_DARKER,
    font_size=1.1,
)

DARK_TEXT_SMALLER = rio.TextStyle(
    fill=TEXT_FILL_DARKER,
    font_size=0.9,
)

DARKER_TEXT = rio.TextStyle(
    fill=TEXT_FILL_DARKER,
    font_size=1.0,
)

# Text on the dashboard page is unusually large. These constants control the
# dashboard page styles for it (and other things).
ACTION_TITLE_HEIGHT = 4
SUB_TITLE_HEIGHT = 2.5
ACTION_TEXT_HEIGHT = 1.05


# This scaling factor is used to reduce the size of the text on mobile
MOBILE_TEXT_SCALING = 0.75

# Image placeholder height
MOBILE_IMAGE_HEIGHT = 13

# Seperator Color
SEPERATOR_COLOR = NEUTRAL_COLOR

# Text style for desktop
BOLD_BIGGER_SECTION_TITEL_DESKTOP = rio.TextStyle(
    fill=TEXT_FILL_BRIGHTER,
    font_size=SUB_TITLE_HEIGHT * 1.1,
    font_weight="bold",
)


BOLD_SECTION_TITEL_DESKTOP = rio.TextStyle(
    fill=TEXT_FILL_BRIGHTER,
    font_size=SUB_TITLE_HEIGHT,
    font_weight="bold",
)

BOLD_SMALLER_SECTION_TITEL_DESKTOP = rio.TextStyle(
    fill=TEXT_FILL_BRIGHTER,
    font_size=SUB_TITLE_HEIGHT * 0.8,
    font_weight="bold",
)


# Text style for mobile
BOLD_BIGGER_SECTION_TITEL_MOBILE = rio.TextStyle(
    fill=TEXT_FILL_BRIGHTER,
    font_size=SUB_TITLE_HEIGHT * 1.1 * MOBILE_TEXT_SCALING,
    font_weight="bold",
)

BOLD_SECTION_TITEL_MOBILE = rio.TextStyle(
    fill=TEXT_FILL_BRIGHTER,
    font_size=SUB_TITLE_HEIGHT * MOBILE_TEXT_SCALING,
    font_weight="bold",
)


BOLD_SMALLER_SECTION_TITLE_MOBILE = rio.TextStyle(
    fill=TEXT_FILL_BRIGHTER,
    font_size=ACTION_TITLE_HEIGHT * MOBILE_TEXT_SCALING,
    font_weight="bold",
)