from typing import Tuple, Optional

import PySimpleGUI as sg


def popup_error(msg: str, parent_window_loc: Optional[Tuple[int,int]] = None, parent_window_size: Optional[Tuple[int,int]] = None):
    if parent_window_loc is None or parent_window_size is None:
        sg.popup_ok(msg, title='Uh oh', keep_on_top=True)
    else:
        max_line_width = 200
        current = sg.MESSAGE_BOX_LINE_WIDTH
        for line in msg.split('\n'):
            if len(line) > current:
                current = len(line)

        (win_x, win_y) = parent_window_loc
        (win_w, win_h) = parent_window_size
        dim_multiplier = 7
        popup_w = dim_multiplier * min(max_line_width, current)
        popup_h = 50 + dim_multiplier * len(msg.split('\n'))
        cx = int(win_w / 2 - popup_w / 2)
        cy = int(win_h / 2 - popup_h / 2)
        sg.popup_ok(msg, title='Uh oh', line_width=popup_w, location=(win_x + cx, win_y + cy), keep_on_top=True)
