# HomeWorldz
python scripts to identify likely HW locations on a NU starchart.

This python script will locate the most likely homeworld positions given the game setup parameters. 
USAGE:
1. Download the first turn file (Turn 001) and save as a json ascii txt file. [note: in the UtilityScripts repo you can use the 01-DownloadTurnFiles.py script to locate and download the appropriate file.]
2. Run PY script ensuring the input paths point to the turn file location.
3. Optional: the included R script can be called to generate a starchart with position locations mapped. See the 04 png file as an example of the output.

This script works great on the standard system generated charts. The addition of nebulae add a challenge. Generally the script will be able to work around 1 nebula. 2 or more and the algorithm is not going to work.

Also, after looking at a lot of maps to develop this script, the visual wet-algorithm in your brain can itself be pretty effective at locating possible HW positions. 

<HIJK
