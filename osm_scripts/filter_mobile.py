import sys
import csv
from xml.etree import ElementTree as ET

def main():
    # Read the CSV from standard input
    csv_reader = csv.DictReader(sys.stdin)

    # Filter nodes
    filtered_nodes = []
    for row in csv_reader:
        if (row['中華電信'] == '1' or row['台灣大哥大'] == '1') and row['遠傳電信'] == '0':
            filtered_nodes.append(row)

    # Create the root 'gpx' element with the necessary namespaces and attributes
    gpx = ET.Element('gpx', {
        'version': "1.1",
        'creator': "Garmin Desktop App",
        'xmlns': "http://www.topografix.com/GPX/1/1",
        'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
        'xsi:schemaLocation': " ".join([
            "http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd",
            # Add other schema locations here...
        ]),
        # Additional namespaces (complete them as needed)...
        'xmlns:wptx1': "http://www.garmin.com/xmlschemas/WaypointExtension/v1",
        'xmlns:gpxtrx': "http://www.garmin.com/xmlschemas/GpxExtensions/v3",
        # ...
    })

    # Add 'metadata' element
    metadata = ET.SubElement(gpx, 'metadata')
    link = ET.SubElement(metadata, 'link', href="http://www.garmin.com")
    ET.SubElement(link, 'text').text = 'Garmin International'
    ET.SubElement(metadata, 'time').text = '2023-10-28T00:53:59Z'
    ET.SubElement(metadata, 'bounds', maxlat="25.135719962418079", maxlon="121.520398920401931", minlat="23.43907356262207", minlon="120.936727523803711")

    # Add waypoints to the GPX file
    for node in filtered_nodes:
        wpt = ET.SubElement(gpx, 'wpt', lat=node['lat'], lon=node['lon'])
        ET.SubElement(wpt, 'name').text = f"{node['network']} {node['id']}"

    # Create the tree and write the GPX file to standard output
    tree = ET.ElementTree(gpx)
    tree.write(sys.stdout, encoding='unicode', xml_declaration=True)

if __name__ == "__main__":
    main()
