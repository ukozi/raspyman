from __future__ import annotations

import typing as t
import rio

class CreateUserModal(rio.Component):
    """
    Modal dialog for creating a new user in Retro AIM Server.
    """
    on_close: t.Callable[[], None]
    on_create: t.Callable[[str, str, bool], None]
    
    screen_name: str = ""
    password: str = ""
    is_icq: bool = False
    
    def build(self) -> rio.Component:
        # Form fields
        form = rio.Column(
            rio.Text(
                "Create New User",
                style=rio.TextStyle(
                    font_size=1.5,
                    font_weight="bold",
                ),
                margin_bottom=1,
            ),
            
            # Screen name input
            rio.Column(
                rio.Text("Screen Name"),
                rio.TextInput(
                    value=self.screen_name,
                    on_change=lambda v: setattr(self, "screen_name", v),
                    placeholder="Enter AIM screen name or ICQ UIN",
                    min_width="100%",
                ),
                spacing=0.5,
                align_x=0,
                min_width="100%",
            ),
            
            # Password input
            rio.Column(
                rio.Text("Password"),
                rio.TextInput(
                    value=self.password,
                    on_change=lambda v: setattr(self, "password", v),
                    placeholder="Enter password",
                    password=True,
                    min_width="100%",
                ),
                spacing=0.5,
                align_x=0,
                min_width="100%",
            ),
            
            # ICQ checkbox
            rio.Row(
                rio.Checkbox(
                    checked=self.is_icq,
                    on_change=lambda v: setattr(self, "is_icq", v),
                ),
                rio.Text("This is an ICQ user"),
                spacing=0.5,
                align_x=0,
            ),
            
            # Form actions
            rio.Row(
                rio.Button(
                    content=rio.Text("Cancel"),
                    on_press=self.on_close,
                    fill=self.session.theme.neutral_color_brighter,
                    padding_x=1,
                    padding_y=0.5,
                ),
                rio.Button(
                    content=rio.Text("Create User"),
                    on_press=lambda: self.on_create(self.screen_name, self.password, self.is_icq),
                    fill=self.session.theme.primary_color,
                    padding_x=1,
                    padding_y=0.5,
                    disabled=not self.screen_name or not self.password,
                ),
                spacing=1,
                align_x=1,
                margin_top=2,
            ),
            
            spacing=1.5,
            align_x=0,
            min_width="100%",
            padding=2,
        )
        
        # Modal container
        return rio.Overlay(
            content=rio.Rectangle(
                content=rio.Rectangle(
                    content=form,
                    fill=self.session.theme.background_color,
                    corner_radius=self.session.theme.corner_radius_medium,
                    min_width=40,
                    max_width=60,
                ),
                fill=self.session.theme.neutral_color_darker.with_opacity(0.5),
                min_width="100vw",
                min_height="100vh",
                on_press=self.on_close,
            ),
            z_index=1000,
        ) 