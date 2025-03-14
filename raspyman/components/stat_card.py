from __future__ import annotations

import typing as t
import rio

from .. import theme

class StatCard(rio.Component):
    """
    A component that displays a statistic with a title, value, and icon.
    
    ## Attributes:
    
    `title`: The title of the statistic.
    `value`: The value of the statistic.
    `icon`: The icon to display.
    `color`: The color theme for the card.
    `is_loading`: Whether the data is currently loading.
    `has_error`: Whether there was an error loading the data.
    """
    
    title: str
    value: t.Union[str, int]
    icon: str = "material/assessment:outlined"
    color: str = "primary"
    is_loading: bool = False
    has_error: bool = False
    
    def build(self) -> rio.Component:
        # Content to display based on loading/error state
        if self.is_loading:
            content = rio.Column(
                rio.ProgressCircle(color=self.color),
                rio.Text(
                    "Loading...",
                    style=rio.TextStyle(
                        font_size=0.9,
                        fill=theme.TEXT_FILL_DARKER,
                    ),
                    margin_top=0.5,
                ),
                align_x=0.5,
            )
        elif self.has_error:
            content = rio.Column(
                rio.Icon(
                    icon="material/error:fill",
                    fill="danger",
                ),
                rio.Text(
                    "Connection error",
                    style=rio.TextStyle(
                        font_size=0.9,
                        fill=theme.ERROR_COLOR,
                    ),
                    margin_top=0.5,
                ),
                align_x=0.5,
            )
        else:
            content = rio.Text(
                str(self.value),
                style=rio.TextStyle(
                    font_size=2.2,
                    font_weight="bold",
                ),
            )
        
        return rio.Card(
            content=rio.Column(
                rio.Row(
                    rio.Icon(
                        icon=self.icon,
                        fill=self.color,
                        min_width=2.2,
                        min_height=2.2,
                    ),
                    rio.Spacer(),
                    align_y=0.5,
                ),
                rio.Text(
                    self.title,
                    style=rio.TextStyle(
                        font_size=1.0,
                        fill=theme.TEXT_FILL_DARKER,
                    ),
                    margin_top=0.5,
                ),
                rio.Container(
                    content=content,
                    min_height=3.0,
                    align_x=0.5,
                    align_y=0.5,
                ),
                margin=1.5,
            ),
            grow_x=True,
        ) 