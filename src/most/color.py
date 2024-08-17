import curses

COLORS = {
    'grey':       (.5,  .5,  .5 ),
    'light_grey': (.94, .94, .94),
    'light_blue': (.9,  .9,   1),
    'light_green': (.9,  1,  .9),
}


INITED_COLORS = {} # (r, g, b) -> color_i
def get_color(color):
    """Given a color name from the COLORS dict, or an (r, g, b) tuple of
    intensities in the range 0-1, returns the curses color index for the
    color."""
    if color in COLORS:
        color = COLORS[color]
    elif isinstance(color, str):
        raise Exception("Unknown color %r" % (color,))
    key = tuple(int(x * 1000) for x in color)
    if key not in INITED_COLORS:
        color_i = len(INITED_COLORS) + 1
        curses.init_color(color_i, *key)
        INITED_COLORS[key] = color_i
    return INITED_COLORS[key]


INITED_PAIRS = {} # (fg_color_i, bg_color_i) -> pair_i
def get_pair(fg=None, bg=None):
    """Given a pair of foreground and background color names or tuples (or
    None to use the terminal's default color for that role), returns the curses
    color pair to use. The return value should be or'd directly into the attr
    passed to addstr."""
    fg_i = -1 if fg is None else get_color(fg)
    bg_i = -1 if bg is None else get_color(bg)
    key = (fg_i, bg_i)
    if key not in INITED_PAIRS:
        pair_i = len(INITED_PAIRS) + 1
        curses.init_pair(pair_i, *key)
        INITED_PAIRS[key] = pair_i
    return curses.color_pair(INITED_PAIRS[key])
