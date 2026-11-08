"""Regenerate the fake-data sample CVs: python tests/fixtures/make_fixtures.py"""

from pathlib import Path

from docx import Document
from pypdf import PdfWriter

HERE = Path(__file__).parent

BIO_LINES = [
    "Rahim Uddin (FAKE SAMPLE) - BSc Biochemistry, University of Dhaka, 2022-2026",
    "CGPA 3.62 / 4.00. IELTS 7.0. Interests: bioinformatics, genomics.",
    "Skills: Python (used for RNA-seq plots), R, PCR, Gel Electrophoresis, Basket Weaving.",
    "Project: Differential expression analysis of a public dataset using Python and pandas.",
    "Experience: Lab volunteer, Dept of Biochemistry - prepared PCR runs and gels.",
]


def _pdf(path: Path, lines: list[str]) -> None:
    """Hand-written one-page text PDF so no PDF-drawing dependency is needed."""
    body = "BT /F1 11 Tf 40 780 Td 16 TL " + " ".join(
        f"({line.replace('(', '[').replace(')', ']')}) Tj T*" for line in lines
    )
    stream = (body + " ET").encode()
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out, offsets = b"%PDF-1.4\n", []
    for i, obj in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + obj + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    path.write_bytes(out)


def main() -> None:
    _pdf(HERE / "bio_student.pdf", BIO_LINES)

    doc = Document()
    for line in [
        "Nusrat Jahan (FAKE SAMPLE) - BBA Marketing, North South University",
        "CGPA 3.31. Skills: Microsoft Excel, Public Speaking, Digital Marketing.",
        "Experience: Marketing intern at a fictional startup, ran 3 social campaigns.",
        "Languages: Bangla, English. Interests: brand management.",
    ]:
        doc.add_paragraph(line)
    doc.save(HERE / "business_student.docx")

    writer = PdfWriter()  # a page with no text layer, like a scan
    writer.add_blank_page(width=612, height=842)
    with (HERE / "scanned.pdf").open("wb") as handle:
        writer.write(handle)


if __name__ == "__main__":
    main()
