Scripts to convert image file types to svs  
# Requirement
pyvips (https://pypi.org/project/pyvips/)
PIL - python imaging library (https://pypi.org/project/pillow/)

# szi2svs
Converts the PathoZoom szi format to aperio svs format

# Usage - use this in the folder where the input.szi file is

python szi2svs.py input.szi output.svs

# Also a separate script for tiff to svs
python tiff2svs.py input.tiff output.svs
