JaVaWa MapConverter CLI

Usage:
jmc_cli source_folder

or

jmc_cli -src=source_folder [-dest=destination_folder] [-bmap=basemap.img] [-gmap=mapname.gmap] [-v]

or

jmc_cli -config=mapname.cfg [-v]

Parameters:
-src     (Relative) path to folder with map files you want to convert
-dest    (Relative) path to folder where the .gmap folder will be created
         (optional; when omitted the parent folder of source_folder will be used)
-bmap    Name of .img file with overview map (optional)
         (Needed only when jmc_cli cannot decide which file to use)
-gmap    Name of .gmap folder (optional; when omitted the map name will be used)
-v       Verbose output: display every step in the process (optional)
-config  Use parameters from config file; see sample

Use quotes around paths when they contain spaces, or (Mac/Linux only) escape
the spaces with backslashes (not in the config file!).

Status codes:

0: success
1: wrong parameters
2: missing files
3: error in processing files
4: unhandled exception