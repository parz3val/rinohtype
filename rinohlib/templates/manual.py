

from rinoh.document import Document, DocumentPart, Page, PORTRAIT
from rinoh.dimension import PT, CM
from rinoh.layout import Container, FootnoteContainer, Chain, \
    UpExpandingContainer, DownExpandingContainer
from rinoh.paper import A4

from rinoh.structure import Section, Heading, TableOfContents, Header, Footer

from rinohlib.stylesheets.somestyle import stylesheet as STYLESHEET


# page definition
# ----------------------------------------------------------------------------

class SimplePage(Page):
    header_footer_distance = 14*PT

    def __init__(self, chain, paper, orientation, header_footer=True):
        super().__init__(chain.document, paper, orientation)
        h_margin = self.document.options['page_horizontal_margin']
        v_margin = self.document.options['page_vertical_margin']
        body_width = self.width - (2 * h_margin)
        body_height = self.height - (2 * v_margin)
        self.body = Container('body', self, h_margin, v_margin,
                              body_width, body_height)

        self.footnote_space = FootnoteContainer('footnotes', self.body, 0*PT,
                                                body_height)
        self.content = Container('content', self.body, 0*PT, 0*PT,
                                 bottom=self.footnote_space.top,
                                 chain=chain)

        self.content._footnote_space = self.footnote_space

        if header_footer:
            header_bottom = self.body.top - self.header_footer_distance
            self.header = UpExpandingContainer('header', self,
                                               left=h_margin,
                                               bottom=header_bottom,
                                               width=body_width)
            footer_vpos = self.body.bottom + self.header_footer_distance
            self.footer = DownExpandingContainer('footer', self,
                                                 left=h_margin,
                                                 top=footer_vpos,
                                                 width=body_width)
            header_text = self.document.options['header_text']
            footer_text = self.document.options['footer_text']
            self.header.append_flowable(Header(header_text))
            self.footer.append_flowable(Footer(footer_text))


# document parts
# ----------------------------------------------------------------------------

# class TitlePart(DocumentPart)



class ManualPart(DocumentPart):
    def __init__(self, document):
        super().__init__(document)
        self.chain = Chain(document)

    def init(self):
        self.new_page([self.chain])

    def new_page(self, chains):
        assert (len(chains) == 1)
        page = SimplePage(next(iter(chains)),
                          self.document.options['page_size'],
                          self.document.options['page_orientation'],
                          header_footer=self.header_footer)
        self.page_count += 1
        self.add_page(page, self.page_count)
        return page.content


class TableOfContentsPart(ManualPart):
    header_footer = False

    def __init__(self, document):
        super().__init__(document)
        self.chain << Section([Heading('Table of Contents', style='unnumbered'),
                               TableOfContents()],
                              style='table of contents')


class ContentsPart(ManualPart):
    header_footer = True

    def __init__(self, document, content_tree):
        super().__init__(document)
        for child in content_tree.getchildren():
            self.chain << child.flowable()


# main document
# ----------------------------------------------------------------------------
class Manual(Document):
    def __init__(self, rinoh_tree, options=None, backend=None, title=None):
        stylesheet = options['stylesheet']
        super().__init__(stylesheet, backend=backend, title=title)
        self.options = options or ManualOptions()
        self.add_part(TableOfContentsPart(self))
        self.add_part(ContentsPart(self, rinoh_tree))


class ManualOptions(dict):
    options = {'stylesheet': STYLESHEET,
               'page_size': A4,
               'page_orientation': PORTRAIT,
               'page_horizontal_margin': 2*CM,
               'page_vertical_margin': 3*CM,
               'header_text': None,
               'footer_text': None}

    def __init__(self, **options):
        for name, value in options.items():
            if name not in self.options:
                raise ValueError("Unknown option '{}'".format(name))
            self[name] = value

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            return self.options[key]