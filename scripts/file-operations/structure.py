# Creates a folder structure view of the contained directory

import os
from pathlib import Path


def append_tree(directory, output_file, lines, prefix=""):
    entries = []
    with os.scandir(directory) as children:
        for child in children:
            if child.name == ".git":
                continue
            path = Path(child.path)
            if path != output_file:
                entries.append((child.name, child.is_dir(follow_symlinks=False), path))

    entries.sort(key=lambda entry: (not entry[1], entry[0].casefold()))
    for index, (name, is_directory, path) in enumerate(entries):
        is_last = index == len(entries) - 1
        connector = "└── " if is_last else "├── "
        lines.append(prefix + connector + name + ("/" if is_directory else ""))

        if is_directory:
            child_prefix = prefix + ("    " if is_last else "│   ")
            append_tree(path, output_file, lines, child_prefix)


def main():
    root = Path(__file__).resolve().parent
    output_file = root / "structure.txt"
    lines = [root.name + "/"]
    append_tree(root, output_file, lines)
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Folder structure exported to {}".format(output_file))


if __name__ == "__main__":
    main()