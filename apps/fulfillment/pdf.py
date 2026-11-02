"""A small PDF writer for labels: text in Helvetica on one page per label,
no other dependency.  Thermal label printers (4x6 and smaller) print PDFs
at their own size from the browser's print dialog.

    doc = Document(4 * 72, 2 * 72)
    page = doc.page()
    page.text(10, 120, "Assam black tea", size=12, bold=True)
    pdf_bytes = doc.render()

Coordinates are PDF points (1/72 inch) from the bottom left.  Text is
encoded as Windows-1252 (the standard fonts' WinAnsiEncoding); anything
else prints as "?".
"""

# Helvetica's advance widths (per 1000 units of font size) for ASCII 32-126.
_WIDTHS = [
    278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,  # space - /
    556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,  # 0 - ?
    1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,  # @ - O
    667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,  # P - _
    333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,  # ` - o
    556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584,  # p - ~
]
# Helvetica-Bold is a little wider; measuring it as this much wider than
# the regular face errs on the side of wrapping early.
_BOLD_FACTOR = 1.1


def text_width(text, size, bold=False):
    total = 0
    for char in text:
        code = ord(char)
        total += _WIDTHS[code - 32] if 32 <= code <= 126 else 556
    return total * size / 1000 * (_BOLD_FACTOR if bold else 1)


def wrap(text, width, size, bold=False):
    """text split into lines no wider than width (points), at spaces; a
    word longer than a line is split."""
    lines = []
    for paragraph in str(text).split("\n"):
        line = ""
        for word in paragraph.split():
            candidate = f"{line} {word}" if line else word
            if text_width(candidate, size, bold) <= width:
                line = candidate
                continue
            if line:
                lines.append(line)
            while text_width(word, size, bold) > width and len(word) > 1:
                cut = len(word)
                while cut > 1 and text_width(word[:cut], size, bold) > width:
                    cut -= 1
                lines.append(word[:cut])
                word = word[cut:]
            line = word
        lines.append(line)
    return lines


def _escape(text):
    data = str(text).encode("cp1252", "replace")
    return data.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


class Page:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._ops = []

    def text(self, x, y, text, size=10, bold=False):
        font = b"/F2" if bold else b"/F1"
        self._ops.append(b"BT %s %.2f Tf %.2f %.2f Td (%s) Tj ET" % (font, size, x, y, _escape(text)))

    def line(self, x1, y1, x2, y2, width=1):
        self._ops.append(b"%.2f w %.2f %.2f m %.2f %.2f l S" % (width, x1, y1, x2, y2))

    def rect(self, x, y, width, height, line_width=1):
        self._ops.append(b"%.2f w %.2f %.2f %.2f %.2f re S" % (line_width, x, y, width, height))

    def content(self):
        return b"\n".join(self._ops)


class Document:
    def __init__(self, width, height, title=""):
        self.width = width
        self.height = height
        self.title = title
        self.pages = []

    def page(self):
        page = Page(self.width, self.height)
        self.pages.append(page)
        return page

    def render(self):
        if not self.pages:
            self.page()
        objects = []  # object bodies; object n is objects[n - 1]

        def add(body):
            objects.append(body)
            return len(objects)

        catalog = add(None)
        pages = add(None)
        regular = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        bold = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        kids = []
        for page in self.pages:
            content = page.content()
            stream = add(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content))
            kids.append(add(
                b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2f %.2f] /Contents %d 0 R "
                b"/Resources << /Font << /F1 %d 0 R /F2 %d 0 R >> >> >>"
                % (pages, page.width, page.height, stream, regular, bold)))
        objects[catalog - 1] = b"<< /Type /Catalog /Pages %d 0 R >>" % pages
        objects[pages - 1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (
            b" ".join(b"%d 0 R" % kid for kid in kids), len(kids))
        info = add(b"<< /Title (%s) /Producer (Teashop) >>" % _escape(self.title))

        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for number, body in enumerate(objects, start=1):
            offsets.append(len(out))
            out += b"%d 0 obj\n%s\nendobj\n" % (number, body)
        xref = len(out)
        out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
        for offset in offsets:
            out += b"%010d 00000 n \n" % offset
        out += b"trailer\n<< /Size %d /Root %d 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
            len(objects) + 1, catalog, info, xref)
        return bytes(out)
