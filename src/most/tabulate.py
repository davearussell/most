def tabulate(rows, indent=0, grid=False):
    """Given a list of lists, returns a string representing them as a table.
    Each inner list represents one row; each item in an inner list fills one
    column in that row. Values can be any type that supports stringification
    via str(). Every inner list must be of the same length.
     * Specify indent=N to insert N blank spaces at the start of each line.
     * Specify grid=True to insert grid lines between columns and also after the
       first row (assumed to hold column headings).

    For example:

    table = [["foo", "bar", "cheese"], [1, 'hello', None], ['', 'some longer text', '']]

    print(tabulate.tabulate(table))
    > foo  bar               cheese
    > 1    hello             None
    >      some longer text

    print(tabulate.tabulate(table, grid=True))
    > | foo | bar              | cheese |
    > +-----+------------------+--------+
    > | 1   | hello            | None   |
    > |     | some longer text |        |
    """
    n_cols = len(rows[0])
    col_widths = [max(map(len, [str(row[i]) for row in rows])) for i in range(n_cols)]
    s = ' ' * indent
    for i, row in enumerate(rows):
        for col, width in zip(row, col_widths):
            spacing = ' ' * (width - len(str(col)))
            if grid:
                s += '| %s%s ' % (col, spacing)
            else:
                s += '%s%s  ' % (col, spacing)
        if grid:
            s += '|'
        s += '\n' + (' ' * indent)
        if grid and i == 0:
            for width in col_widths:
                s += '+' + ('-' * (width + 2))
            s += '+\n' + (' ' * indent)
    return s.rstrip()

def tabulate_dict(columns, data, **kwargs):
    """Given a list of keys and a list of dicts, returns a table with the value
    each dict has for each key, with the dicts as rows and the keys as columns.
    Accepts the same kwargs as `tabulate`."""
    if not (columns or data):
        return ''
    return tabulate([columns] + [
        [entry.get(column, '') for column in columns]
        for entry in data
    ], **kwargs)
