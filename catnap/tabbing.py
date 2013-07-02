from __future__ import absolute_import, division, print_function, with_statement, unicode_literals

def detab(contents):
    """
    Removes formatting tabs from Python code so it can be executed without a
    syntax error
    """
    lines = contents.splitlines()

    # Removes empty beginning/ending lines
    while len(lines) > 0 and lines[0].strip() == "":
        lines = lines[1:]
    while len(lines) > 0 and lines[-1].strip() == "":
        lines = lines[:-1]
    
    # Get the amount of whitespace in the first line of code, and remove it
    # from the beginning of all lines
    if len(lines) > 0:
        stripped = lines[0].lstrip()
        
        if len(stripped) < len(lines[0]):
            diff = len(lines[0]) - len(stripped)
            whitespace = lines[0][:diff]
            lines = [line[len(whitespace):] for line in lines if line.startswith(whitespace)]

    return "\n".join(lines)

def tab(contents, num_spaces):
    """
    Inserts the specified amount of spaces in front of each line of the contents
    """
    return "\n".join(["%s%s" % (" " * num_spaces, line) for line in contents.splitlines()])
