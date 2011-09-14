import itertools
from screenplain.types import Slug, Action, Dialog, DualDialog, Transition

slug_prefixes = (
    'INT. ',
    'EXT. ',
    'INT./EXT. ',
    'INT/EXT. ',
    'INT ',
    'EXT ',
    'INT/EXT ',
    'I/E ',
)

TWOSPACE = ' ' * 2

def is_blank(string):
    return string == '' or string.isspace() and string != '  '

def is_slug(blanks_before, string):
    if blanks_before >= 2:
        return True
    upper = string.upper()
    return any(upper.startswith(s) for s in slug_prefixes)

def _create_dialog(line_list):
    try:
        dual_index = line_list.index('||')
    except ValueError:
        return Dialog(line_list)
    else:
        return DualDialog(line_list[:dual_index], line_list[dual_index + 1:])

def create_paragraph(blanks_before, line_list):
    if is_slug(blanks_before, line_list[0]):
        return Slug(line_list)
    if (
        len(line_list) > 1 and
        line_list[0].isupper() and
        not line_list[0].endswith(TWOSPACE)
    ):
        return _create_dialog(line_list)
    elif len(line_list) == 1 and line_list[0].endswith(':') and line_list[0].isupper():
        # Assume this is a transition. It may be changed to Action
        # later if we find that it's not followed by a slug.
        return Transition(line_list)
    else:
        return Action(line_list)

def clean_line(line):
    """Strips leading whitespace and trailing end of line characters
    in a string.

    Leading whitespace is insignificant in SPMD, and trailing EOL
    appear when reading from a file or HTML form.
    """
    return line.lstrip().rstrip('\r\n')

def parse(source):
    """Reads raw text input and generates paragraph objects."""
    blank_count = 0
    source = (clean_line(line) for line in source)
    paragraphs = []
    for blank, lines in itertools.groupby(source, is_blank):
        if blank:
            blank_count = len(list(lines))
        else:
            paragraphs.append(create_paragraph(blank_count, list(lines)))

    # Make a second pass over the script and replace transitions not
    # followed by sluglines with action.
    for i in xrange(len(paragraphs) - 1):
        if (isinstance(paragraphs[i], Transition) and
            not isinstance(paragraphs[i + 1], Slug)):
            paragraphs[i] = Action(paragraphs[i].lines)
    return paragraphs