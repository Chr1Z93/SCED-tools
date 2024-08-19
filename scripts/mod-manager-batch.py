import subprocess
import os

args = ["--reverse", "--moddir=C:\\git\\SCED"]
go_script = "main.go"
folder = "C:\\git\\loadable-objects\\campaigns"

for path, subdirs, files in os.walk(folder):
    for file in files:
        objin = ["--objin=" + folder + "\\" + file]
        objout = ["--objout=C:\\git\\SCED-downloads\\decomposed"]
        command = ["go", "run", go_script] + args + objin + objout

        try:
            result = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            print(f"Command: {' '.join(command)}")
            print(f"Output:\n{result.stdout}")
            if result.stderr:
                print(f"Errors:\n{result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while executing: {' '.join(command)}")
            print(f"Error code: {e.returncode}")
            print(f"Output:\n{e.output}")
            print(f"Errors:\n{e.stderr}")
