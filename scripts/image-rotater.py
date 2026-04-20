import os
from PIL import Image

# List of file names (without extensions)
file_names = [
    "90001",
    "90005",
    "90006",
    "90008",
    "90012",
    "90013",
    "90014",
    "90017",
    "90021",
    "90022",
    "90024",
    "90033",
    "90034",
    "90035",
    "90037",
    "90042",
    "90043",
    "90044",
    "90046",
    "90049",
    "90055",
    "90056",
    "90059",
    "90062",
    "90066",
    "90067",
    "90068",
    "90069",
    "90078",
    "90081",
    "90084",
    "90087",
    "90095",
    "90096",
]

input_folder = r"C:\Users\pulsc\OneDrive\Dateien\Brettspiele\Arkham Horror\Karten\Arkham Cards - de\Parallel"


def rotate_images_auto_ext(names):
    # Get a list of all files in the folder once to save time
    folder_files = os.listdir(input_folder)

    for name in names:
        # Find the file that matches the name
        match = next(
            (f for f in folder_files if os.path.splitext(f)[0] == name),
            None,
        )

        if match:
            filepath = os.path.join(input_folder, match)
            try:
                with Image.open(filepath) as img:
                    rotated_img = img.rotate(180)
                    rotated_img.save(
                        filepath,
                        quality=100,
                        method=6,
                    )
                    print(f"Rotated and saved: {match}")
            except Exception as e:
                print(f"Could not process {match}: {e}")
        else:
            print(f"No file found starting with: {name}")


if __name__ == "__main__":
    rotate_images_auto_ext(file_names)
