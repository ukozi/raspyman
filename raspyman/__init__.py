from __future__ import annotations

import typing as t
import logging
from pathlib import Path

import rio

from . import components as comps
from . import data_models
from . import theme
from .utils import ASSETS_DIR

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("raspyman")

# Set this to False to keep user's custom settings
RESET_SETTINGS = False

# Remove all the custom SVG icon registrations
# We'll use Material icons directly instead

def on_session_start(sess: rio.Session) -> None:
    # Determine which layout to use
    if sess.window_width < 60:
        layout = data_models.PageLayout(
            device="mobile",
        )
    else:
        layout = data_models.PageLayout(
            device="desktop",
        )

    # Attach the layout to the session
    sess.attach(layout)
    
    # Force reset settings if needed
    if RESET_SETTINGS:
        # Create fresh settings with correct values
        settings = data_models.RasApiSettings(api_url="http://localhost:5000")
        if hasattr(settings, '_mark_as_modified'):
            settings._mark_as_modified()
        sess.attach(settings)  # Replace existing one
    else:
        # Normal initialization code
        settings = sess[data_models.RasApiSettings]
        # Only fix invalid URL values
        if not settings.api_url or settings.api_url == "http://localhost:500":
            settings.api_url = "http://localhost:5000"
            # Explicitly mark settings as modified to ensure they're saved
            if hasattr(settings, '_mark_as_modified'):
                settings._mark_as_modified()
            sess.attach(settings)  # Re-attach to ensure persistence

# Create the Rio app
app = rio.App(
    name='ras-admin',
    # Initialize session for each new connection
    on_session_start=on_session_start,
    # Custom root component for consistent navigation 
    build=comps.AdminRootComponent,
    # Custom theme
    theme=theme.ADMIN_THEME,
    assets_dir=Path(__file__).parent / "assets",
    # Add the RasApiSettings as a default attachment
    default_attachments=[
        # Initialize with default values
        data_models.RasApiSettings(
            api_url="http://localhost:5000",
            last_connected=None
        ),
    ],
)

