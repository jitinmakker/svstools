import zipfile
import os
import re
import io
from PIL import Image
import pyvips
import argparse

def extract_szi_to_memory(szi_file):
    """Extracts the SZI (ZIP) file into memory."""
    extracted_files = {}

    with zipfile.ZipFile(szi_file, 'r') as zip_ref:
        for file in zip_ref.namelist():
            extracted_files[file] = zip_ref.read(file)  # Store files in memory
    
    print(f"Extracted {szi_file} into memory.")
    return extracted_files

def get_extracted_paths_in_memory(extracted_files):
    """Finds the correct in-memory paths inside the 'scan' folder."""
    scan_files = {k: v for k, v in extracted_files.items() if k.startswith("scan/")}

    # Find DZI file
    dzi_file = None
    for file_name in scan_files.keys():
        if file_name.endswith(".dzi"):
            dzi_file = file_name
            break

    if not dzi_file:
        raise FileNotFoundError("Error: Could not find the .dzi file inside 'scan'.")

    # Find the _files folder dynamically
    tiles_dir = None
    for folder in scan_files.keys():
        if "_files/" in folder:
            tiles_dir = folder.split("_files/")[0] + "_files/"
            break

    if not tiles_dir:
        raise FileNotFoundError("Error: Could not find the '_files' directory inside 'scan'.")

    print(f"Using tiles directory: {tiles_dir}")
    print(f"Using DZI file: {dzi_file}")

    return tiles_dir, dzi_file, scan_files


def reconstruct_image_from_memory(tiles_dir, dzi_file, scan_files):
    """Reconstructs the full-resolution image from Deep Zoom tiles stored in memory."""
    # Read DZI file to get image dimensions
    dzi_content = scan_files[dzi_file].decode('utf-8')
    match = re.search(r'Width="(\d+)"\s+Height="(\d+)"', dzi_content)

    if not match:
        raise ValueError("Could not find image dimensions in DZI file.")
    
    width, height = int(match.group(1)), int(match.group(2))
    print(f"Image dimensions: {width}x{height}")

    # Get deepest zoom level (full resolution)
    levels = sorted(set(re.findall(fr'{tiles_dir}(\d+)/', "\n".join(scan_files.keys()))), key=int, reverse=True)
    if not levels:
        raise FileNotFoundError("Error: No zoom level directories found in '_files'.")

    full_res_level = levels[0]
    full_res_path = f"{tiles_dir}{full_res_level}/"

    # Get all tile images
    tile_files = {k: v for k, v in scan_files.items() if k.startswith(full_res_path)}

    if not tile_files:
        raise FileNotFoundError(f"Error: No image tiles found in {full_res_path}.")

    # Sort tile filenames by row and column
    tile_positions = {}
    for tile_name in tile_files.keys():
        match = re.search(r'(\d+)_(\d+)\.', os.path.basename(tile_name))
        if match:
            col, row = int(match.group(1)), int(match.group(2))
            tile_positions[(col, row)] = tile_name

    # Get tile size
    sample_tile = Image.open(io.BytesIO(tile_files[next(iter(tile_files.keys()))]))
    tile_width, tile_height = sample_tile.size
    print(f"Tile size: {tile_width}x{tile_height}")

    # Compute number of tiles
    cols = (width + tile_width - 1) // tile_width
    rows = (height + tile_height - 1) // tile_height

    # Create blank image
    reconstructed_image = Image.new("RGB", (width, height))

    # Stitch tiles
    for (col, row), tile_path in tile_positions.items():
        tile_img = Image.open(io.BytesIO(tile_files[tile_path]))
        reconstructed_image.paste(tile_img, (col * tile_width, row * tile_height))

    return reconstructed_image

def convert_tiff_to_svs_in_memory(image_pil, svs_file):
    """Converts an in-memory PIL image to SVS-compatible pyramidal TIFF."""
    # Convert PIL image to raw bytes for pyvips
    image_bytes = io.BytesIO()
    image_pil.save(image_bytes, format="TIFF")
    image_bytes.seek(0)

    # Load into pyvips from memory
    image_vips = pyvips.Image.new_from_buffer(image_bytes.getvalue(), "", access="sequential")

    # Save as pyramidal TIFF (SVS-compatible)
    image_vips.tiffsave(
        svs_file,
        compression="jpeg",
        tile=True,
        pyramid=True,
        tile_width=256,
        tile_height=256,
        bigtiff=True,
        Q=85  # JPEG quality
    )

    print(f"Converted image to {svs_file} without saving intermediate files.")

def main():
    """Main function to process SZI to SVS conversion in memory."""
    parser = argparse.ArgumentParser(description="Convert SZI (PathoZoom) to SVS in-memory")
    parser.add_argument("input_szi", help="Path to the input .szi file")
    parser.add_argument("output_svs", help="Path to the output .svs file")
    args = parser.parse_args()

    szi_file = args.input_szi
    svs_file = args.output_svs

    print("\n=== Step 1: Extracting SZI File Into Memory ===")
    extracted_files = extract_szi_to_memory(szi_file)

    print("\n=== Step 2: Locating Required Files in Memory ===")
    tiles_dir, dzi_file, scan_files = get_extracted_paths_in_memory(extracted_files)

    print("\n=== Step 3: Reconstructing Full-Resolution Image in Memory ===")
    full_image = reconstruct_image_from_memory(tiles_dir, dzi_file, scan_files)

    print("\n=== Step 4: Converting Image to SVS in Memory ===")
    convert_tiff_to_svs_in_memory(full_image, svs_file)

    print(f"\n✅ Conversion completed: {svs_file}")

if __name__ == "__main__":
    main()
