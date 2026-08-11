from .document import StringDocument

HELP_TEXT = """Keybinds:

  UP               Up one line     |
  DOWN             Down one line   |
  LEFT             Left 10 cols    | Precede any of of these with a number N
  RIGHT            Right 10 cols   | to scroll by N instead of the default
  w, PGUP          Up one page     |
  z, PGDN, SPACE   Down one page   |


  g                Goto line 1      (Precede with N to goto line N)
  HOME             Goto first line
  END, G           Goto last line


  /                Start entering search pattern (regexp)
  CTRL-C           Cancel entering search pattern
  ENTER            Begin a search for current search pattern
  n                Continue search (down) for current pattern
  N, p, P          Continue search (up) for current pattern


  h, H, ?          Open this window
  l, L             Toggle displaying line numbers
  e, E             Toggle line-selection mode
  CTRL-L           Reorient window around selected line (cycles middle/top/bottom)
  q                Exit the app"""

class HelpDocument(StringDocument):
    def __init__(self):
        super().__init__(HELP_TEXT, 'Help (hit ENTER to close)')

    def handle_key(self, name):
        if name == '^J' and self.app.input_mode != 'search':
            self.app.pop_doc()
            return True
