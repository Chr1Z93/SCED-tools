from pypdf import PdfReader, PdfWriter

# Config
INPUT = r"C:\Users\pulsc\Downloads\Arkham Horror - Grimoire_v1.1.pdf"
OUTPUT = r"C:\Users\pulsc\Downloads\Arkham Horror - Grimoire_v1.1_output.pdf"


def fix_pdf():
    reader = PdfReader(INPUT)
    writer = PdfWriter()

    total_pages = len(reader.pages)

    for i, page in enumerate(reader.pages):

        # Don't split first or last page
        if i == 0 or i == total_pages - 1:
            writer.add_page(page)
            continue 

        # Split other pages
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        # Left half
        left = writer.add_page(page)
        left.cropbox.lower_left = (0, 0)
        left.cropbox.upper_right = (width / 2, height)

        # Right half
        right = writer.add_page(page)
        right.cropbox.lower_left = (width / 2, 0)
        right.cropbox.upper_right = (width, height)

    # Save
    with open(OUTPUT, "wb") as out_file:
        writer.write(out_file)

    print("PDF successfully split!")


if __name__ == "__main__":
    fix_pdf()
