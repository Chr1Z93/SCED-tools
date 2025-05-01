import os

# Config
search_folder = r"C:\git\SCED-downloads\decomposed"
filter_string = '"id": "01169"'
template_file = r"C:\git\SCED-downloads\decomposed\campaign\Return to The Circle Undone\ReturntoTheCircleUndone.757324\5ReturntoFortheGreaterGood.20790b\NotaMemberoftheLodge.abe15f\Encounterdeck.8bae65\Acolyte.ab3719.gmnotes"

# Load content from template file
try:
    with open(template_file, "r", encoding="utf-8") as f_template:
        new_content = f_template.read()
except FileNotFoundError:
    print(f"Error: Template file not found at {template_file}")
    exit()
except Exception as e:
    print(f"Error reading template file: {e}")
    exit()

# Loop through all *.gmnotes files
for root, _, files in os.walk(search_folder):
    for file in files:
        if file.endswith(".gmnotes"):
            file_path = os.path.join(root, file)

            try:
                with open(file_path, "r", encoding="utf-8") as f_target:
                    content = f_target.read()

                if filter_string in content:
                    # update content according to template file
                    if new_content != content:
                        with open(file_path, "w", encoding="utf-8") as f_target:
                            f_target.write(new_content)
                        print(f"Replaced in: {file_path}")

            except Exception as e:
                print(f"Error at {file_path}: {e}")
