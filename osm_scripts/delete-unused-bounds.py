from __future__ import print_function
import argparse
import os
import re

def main():
    parser = argparse.ArgumentParser(description='''
    Example: python osm_scripts/delete-unused-bounds.py bounds
    ''')
    parser.add_argument('--bbox',
            default='21.55682,118.12141,26.44212,122.31377')
    parser.add_argument('--yes', action='store_true')
    parser.add_argument('folder')

    opts = parser.parse_args()
    lat_min, lon_min, lat_max, lon_max= map(float, opts.bbox.split(','))

    count_keep = 0
    count_delete = 0
    count_not_bound = 0
    for basename in os.listdir(opts.folder):
        path = os.path.join(opts.folder, basename)
        m = re.match(r'^bounds_(-?\d+)_(-?\d+).bnd', basename)
        if not m:
            count_not_bound += 1
            continue
        lat = float(m.group(1)) / 2**24 * 360
        lon = float(m.group(2)) / 2**24 * 360
        # bound dimention
        dim = 50000 / 2**24 * 360

        if (lat_min - dim * 1.5 <= lat <= lat_max + dim * 0.5 and
            lon_min - dim * 1.5 <= lon <= lon_max + dim * 0.5):
            count_keep += 1
            continue

        count_delete += 1
        if opts.yes:
            os.unlink(path)

    print('%d none bound files' % count_not_bound)
    print('%d bound files to keep' % count_keep)
    print('%d bound files to delete' % count_delete)
    if not opts.yes:
        print('pass --yes to actually delete files')


if __name__ == '__main__':
    main()
