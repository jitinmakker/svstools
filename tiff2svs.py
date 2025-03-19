import pyvips
import argparse
from PIL import Image

def convert_tiff_to_svs(tiff_file, svs_file):
    image = pyvips.Image.new_from_file(tiff_file, access="sequential")

    # Save as pyramidal TIFF (SVS-compatible)
    image.tiffsave(
        svs_file,
        compression="jpeg",
        tile=True,
        pyramid=True,
        tile_width=256,
        tile_height=256,
        bigtiff=True,
        Q=85  # JPEG quality
    )

    print(f"Converted {tiff_file} to {svs_file}")

def main():
    """Main function to process TIFF to SVS conversion."""
    parser = argparse.ArgumentParser(description="Convert TIFF to SVS in-memory")
    parser.add_argument("input_tiff", help="Path to the input .tiff file")
    parser.add_argument("output_svs", help="Path to the output .svs file")
    args = parser.parse_args()

    convert_tiff_to_svs(args.input_tiff, args.output_svs)

if __name__ == "__main__":
    main()
