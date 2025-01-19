import os

def delete_images(directory, extensions):
    """
    Delete files with specific extensions from a directory and its subdirectories.

    Args:
        directory (str): Path to the root directory.
        extensions (list): List of file extensions to delete (e.g., ['.gif', '.png']).
    """
    if not os.path.exists(directory):
        print(f"Error: Directory '{directory}' does not exist.")
        return

    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    print(f"Deleted: {file_path}")
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

# Define the folder and extensions
weathertiles_folder = "./weathertiles"

#Disabling this for dev work (I'm not failing gracefully when I don't have weather gifs)
#file_extensions_to_delete = [".gif", ".png"]

file_extensions_to_delete = [".png"]

# Run the deletion function
delete_images(weathertiles_folder, file_extensions_to_delete)
