from __future__ import annotations

import typing as t
from dataclasses import KW_ONLY, field

import rio

from .. import components as comps


class RootComponent(rio.Component):
    """
    This page will be used as the root component for the app. This means, that
    it will always be visible, regardless of which page is currently active.

    This makes it the perfect place to put components that should be visible on
    all pages, such as a navbar or a footer.

    Additionally, the root page will contain a `rio.PageView`. Page views don't
    have any appearance on their own, but they are used to display the content
    of the currently active page. Thus, we'll always see the navbar and footer,
    with the content of the current page in between.
    """

    def build(self) -> rio.Component:
        return rio.Column(
            # The navbar contains a `rio.Overlay`, so it will always be on top
            # of all other components.
            comps.Navbar(),
            # Add some empty space so the navbar doesn't cover the content.
            rio.Spacer(min_height=10),
            # The page view will display the content of the current page.
            rio.PageView(
                # Make sure the page view takes up all available space.
                grow_y=True,
            ),
            # The footer is also common to all pages, so place it here.
            comps.Footer(),
        )

