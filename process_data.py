import os
import subprocess
import sys

# --- Configuration ---
# Set the base directory to the current working directory.
# The script assumes it's being run from inside the "Trypanosoma" folder.
base_dir = os.getcwd()

# Define the names of your input/output folders and reference file.
results_folder = "results"
output_folder = "results_modified"
reference_file = "reference_names.txt"

# --- Script Logic ---
def process_files():
    """
    Finds .counts.txt files and replaces the first column based on a reference file.
    """
    # Construct full paths
    results_path = os.path.join(base_dir, results_folder)
    output_path = os.path.join(base_dir, output_folder)
    ref_file_path = os.path.join(base_dir, reference_file)

    # 1. Validate paths
    if not os.path.isdir(results_path):
        print(f"Error: The results folder '{results_folder}' was not found.")
        sys.exit(1)
    if not os.path.isfile(ref_file_path):
        print(f"Error: The reference file '{reference_file}' was not found.")
        sys.exit(1)

    # 2. Create the output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    print(f"Output will be saved in: '{output_path}'")

    # 3. Find all barcode*.counts.txt files to process
    try:
        files_to_process = [f for f in os.listdir(results_path) if f.endswith(".counts.txt")]
        if not files_to_process:
            print(f"Warning: No '.counts.txt' files found in '{results_path}'.")
            return
    except OSError as e:
        print(f"Error reading directory '{results_path}': {e}")
        sys.exit(1)

    # 4. Process each file
    for filename in files_to_process:
        input_file = os.path.join(results_path, filename)
        output_file = os.path.join(output_path, f"{os.path.splitext(filename)[0]}.modified.txt")
        
        print(f"Processing '{filename}' -> '{os.path.basename(output_file)}'")

        # 5. Construct and execute the FINAL awk command
        # This version keeps the full identifier (index + description).
        awk_command = (
            f"awk 'BEGIN{{OFS=\"\\t\"}} "
            f"NR==FNR {{ "
            f"  sub(/\\r$/, \"\"); " # Remove potential Windows line ending
            f"  lookup[$1]=$0; "     # Store the ENTIRE clean line as the value
            f"  next "
            f"}} "
            f"{{if ($1 in lookup) print lookup[$1], $2, $3, $4}}' "
            f"\"{ref_file_path}\" \"{input_file}\" > \"{output_file}\""
        )
        
        try:
            subprocess.run(awk_command, shell=True, check=True, executable='/bin/bash')
        except subprocess.CalledProcessError as e:
            print(f"  -> An error occurred while processing {filename}: {e}")

    print("\n✅ All files processed successfully.")

if __name__ == "__main__":
    process_files()