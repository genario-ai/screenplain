# Copyright (c) 2014 Martin Vilcans
# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license.php
import os

from screenplain import types
from screenplain.types import Action, Dialog, DualDialog, Transition, Slug
import reportlab
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab import platypus
from reportlab.platypus import (
    BaseDocTemplate,
    Paragraph,
    Frame,
    PageTemplate,
    NextPageTemplate,
    Spacer,
)
from reportlab.lib import pagesizes
import sys

try:
    import reportlab
except ImportError:
    sys.stderr.write("ERROR: ReportLab is required for PDF output\n")
    raise
# del reportlab

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class MultiFontParagraph(Paragraph):
    # Created by B8Vrede for http://stackoverflow.com/questions/35172207/
    def __init__(self, text, style):
        if str(BASE_DIR) + "/export/fonts" not in reportlab.rl_config.TTFSearchPath:
            reportlab.rl_config.TTFSearchPath.append(str(BASE_DIR) + "/export/fonts")
        print("YOOOOLO : ", reportlab.rl_config.TTFSearchPath)

        font_list = []
        fonts_locations = [("Noto", "NotoSans-VariableFont_wdth,wght.ttf")]
        for font_name, font_location in fonts_locations:
            # Load the font
            font = TTFont(font_name, font_location)

            # Get the char width of all known symbols
            font_widths = font.face.charWidths

            # Register the font to able it use
            pdfmetrics.registerFont(font)

            # Store the font and info in a list for lookup
            font_list.append((font_name, font_widths))

        # Set up the string to hold the new text
        new_text = ""

        # Loop through the string
        for char in text:

            # Loop through the fonts
            for font_name, font_widths in font_list:

                # Check whether this font know the width of the character
                # If so it has a Glyph for it so use it
                if ord(char) in font_widths:

                    # Set the working font for the current character
                    new_text += '<font name="{}">{}</font>'.format(font_name, char)
                    break

        Paragraph.__init__(self, new_text, style)


def create_default_settings():
    return Settings()


class Settings:
    # General styles
    default_style: ParagraphStyle
    centered_style: ParagraphStyle

    # Screenplay styles
    character_style: ParagraphStyle
    dialog_style: ParagraphStyle
    parenthentical_style: ParagraphStyle
    action_style: ParagraphStyle
    centered_action_style: ParagraphStyle
    slug_style: ParagraphStyle
    transition_style: ParagraphStyle

    # Title page styles
    title_style: ParagraphStyle
    contact_style: ParagraphStyle

    font_size: int
    line_height: int
    character_width: float
    lines_per_page: int
    characters_per_line: int

    # True if sluglines should be bold
    strong_slugs: bool

    frame_height: float
    frame_width: float
    page_width: float
    page_height: float

    def __init__(
        self,
        font_size=12,
        line_height=None,
        lines_per_page=55,
        characters_per_line=61,
        page_size=pagesizes.letter,
        strong_slugs=False,
    ):
        line_height = line_height or font_size

        self.font_size = font_size
        self.line_height = line_height
        # Courier pitch is 10 chars/inch
        self.character_width = 1.0 / 10 * inch
        self.lines_per_page = lines_per_page
        self.characters_per_line = characters_per_line
        self.frame_height = self.line_height * self.lines_per_page
        self.frame_width = self.characters_per_line * self.character_width
        [self.page_width, self.page_height] = page_size
        self.left_margin = 1.5 * inch
        self.right_margin = self.page_width - (self.left_margin + self.frame_width)
        self.top_margin = 1 * inch
        self.bottom_margin = self.page_height - (self.top_margin + self.frame_height)
        self.title_frame_width = self.page_width - (self.left_margin + self.left_margin)
        self.strong_slugs = strong_slugs

        default_style = ParagraphStyle(
            "default",
            fontName="NotoSans",
            fontSize=font_size,
            leading=line_height,
            spaceBefore=0,
            spaceAfter=0,
            leftIndent=0,
            rightIndent=0,
        )
        self.default_style = default_style

        self.centered_style = ParagraphStyle(
            "default-centered",
            self.default_style,
            alignment=TA_CENTER,
        )

        self.character_style = ParagraphStyle(
            "character",
            default_style,
            spaceBefore=line_height,
            leftIndent=19 * self.character_width,
            keepWithNext=1,
        )
        self.dialog_style = ParagraphStyle(
            "dialog",
            default_style,
            leftIndent=9 * self.character_width,
            rightIndent=self.frame_width - (45 * self.character_width),
        )
        self.parenthentical_style = ParagraphStyle(
            "parenthentical",
            default_style,
            leftIndent=13 * self.character_width,
            keepWithNext=1,
        )
        self.action_style = ParagraphStyle(
            "action",
            default_style,
            spaceBefore=line_height,
        )
        self.centered_action_style = ParagraphStyle(
            "centered-action",
            self.action_style,
            alignment=TA_CENTER,
        )
        self.slug_style = ParagraphStyle(
            "slug",
            default_style,
            spaceBefore=line_height,
            spaceAfter=line_height,
            keepWithNext=1,
        )
        self.transition_style = ParagraphStyle(
            "transition",
            default_style,
            spaceBefore=line_height,
            spaceAfter=line_height,
            alignment=TA_RIGHT,
        )

        self.title_style = ParagraphStyle(
            "title",
            default_style,
            fontSize=font_size * 2,
            leading=font_size * 3,
            alignment=TA_CENTER,
        )
        self.contact_style = ParagraphStyle(
            "contact",
            default_style,
        )


class DocTemplate(BaseDocTemplate):
    def __init__(self, *args, **kwargs):
        self.settings = kwargs.pop("settings", None) or create_default_settings()
        self.has_title_page = kwargs.pop("has_title_page", False)
        frame = Frame(
            self.settings.left_margin,
            self.settings.bottom_margin,
            self.settings.frame_width,
            self.settings.frame_height,
            id="normal",
            leftPadding=0,
            topPadding=0,
            rightPadding=0,
            bottomPadding=0,
        )
        title_frame = Frame(
            self.settings.left_margin,
            self.settings.bottom_margin,
            self.settings.title_frame_width,
            self.settings.frame_height,
            id="title",
            leftPadding=0,
            topPadding=0,
            rightPadding=0,
            bottomPadding=0,
        )
        pageTemplates = [
            PageTemplate(id="title", frames=[title_frame]),
            PageTemplate(id="standard", frames=[frame]),
        ]
        BaseDocTemplate.__init__(self, pageTemplates=pageTemplates, *args, **kwargs)

    def handle_pageBegin(self):
        self.canv.setFont(
            "Courier", self.settings.font_size, leading=self.settings.line_height
        )
        if self.has_title_page:
            page = self.page  # self.page is 0 on first page
        else:
            page = self.page + 1
        if page >= 2:
            self.canv.drawRightString(
                self.settings.left_margin + self.settings.frame_width,
                self.settings.page_height - 42,
                "%s." % page,
            )
        self._handle_pageBegin()


def add_paragraph(story, para, style):
    story.append(
        Paragraph("<br/>".join(line.to_html() for line in para.lines), style)
    )


def add_slug(story, para, style, is_strong):
    for line in para.lines:
        if is_strong:
            html = "<b><u>" + line.to_html() + "</u></b>"
        else:
            html = line.to_html()
        story.append(Paragraph(html, style))


def add_dialog(story, dialog, settings: Settings):
    story.append(
        Paragraph(dialog.character.to_html(), settings.character_style)
    )
    for parenthetical, line in dialog.blocks:
        if parenthetical:
            story.append(
                Paragraph(line.to_html(), settings.parenthentical_style)
            )
        else:
            story.append(Paragraph(line.to_html(), settings.dialog_style))


def add_dual_dialog(story, dual, settings: Settings):
    # TODO: format dual dialog
    add_dialog(story, dual.left, settings)
    add_dialog(story, dual.right, settings)


def get_title_page_story(screenplay, settings):
    """Get Platypus flowables for the title page"""
    # From Fountain spec:
    # The recommendation is that Title, Credit, Author (or Authors, either
    # is a valid key syntax), and Source will be centered on the page in
    # formatted output. Contact and Draft date would be placed at the lower
    # left.

    def add_lines(story, attribute, style, space_before=0):
        lines = screenplay.get_rich_attribute(attribute)
        if not lines:
            return 0

        if space_before:
            story.append(Spacer(settings.frame_width, space_before))

        total_height = 0
        for line in lines:
            html = line.to_html()
            para = Paragraph(html, style)
            width, height = para.wrap(settings.frame_width, settings.frame_height)
            story.append(para)
            total_height += height
        return space_before + total_height

    title_story = []
    title_height = sum(
        (
            add_lines(title_story, "Title", settings.title_style),
            add_lines(
                title_story,
                "Credit",
                settings.centered_style,
                space_before=settings.line_height,
            ),
            add_lines(title_story, "Author", settings.centered_style),
            add_lines(title_story, "Authors", settings.centered_style),
            add_lines(title_story, "Source", settings.centered_style),
        )
    )

    lower_story = []
    lower_height = sum(
        (
            add_lines(lower_story, "Draft date", settings.default_style),
            add_lines(
                lower_story,
                "Contact",
                settings.contact_style,
                space_before=settings.line_height,
            ),
            add_lines(
                lower_story,
                "Copyright",
                settings.centered_style,
                space_before=settings.line_height,
            ),
        )
    )

    if not title_story and not lower_story:
        return []

    story = []
    top_space = min(
        settings.frame_height / 3.0, settings.frame_height - lower_height - title_height
    )
    if top_space > 0:
        story.append(Spacer(settings.frame_width, top_space))
    story += title_story
    # The minus half font size adds some room for rounding errors and whatnot
    middle_space = settings.frame_height - (
        top_space + title_height + lower_height + settings.font_size / 2
    )
    if middle_space > 0:
        story.append(Spacer(settings.frame_width, middle_space))
    story += lower_story

    story.append(NextPageTemplate("standard"))

    story.append(platypus.PageBreak())
    return story


def to_pdf(
    screenplay, output_filename, template_constructor=DocTemplate, settings=None
):
    settings = settings or create_default_settings()
    story = get_title_page_story(screenplay, settings)
    has_title_page = bool(story)

    for para in screenplay:
        if isinstance(para, Dialog):
            add_dialog(story, para, settings)
        elif isinstance(para, DualDialog):
            add_dual_dialog(story, para, settings)
        elif isinstance(para, Action):
            add_paragraph(
                story,
                para,
                (
                    settings.centered_action_style
                    if para.centered
                    else settings.action_style
                ),
            )
        elif isinstance(para, Slug):
            add_slug(story, para, settings.slug_style, settings.strong_slugs)
        elif isinstance(para, Transition):
            add_paragraph(story, para, settings.transition_style)
        elif isinstance(para, types.PageBreak):
            story.append(platypus.PageBreak())
        else:
            # Ignore unknown types
            pass

    doc = template_constructor(
        output_filename,
        pagesize=(settings.page_width, settings.page_height),
        settings=settings,
        has_title_page=has_title_page,
    )
    doc.build(story)
