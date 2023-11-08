import sys
import csv
import xml.etree.ElementTree as ET

# Parse XML from standard input
tree = ET.parse(sys.stdin)
root = tree.getroot()

# Define the telecom operators to check
operators = ['中華電信', '遠傳電信', '台灣大哥大', '亞太電信', '台灣之星']

# Prepare the CSV writer
csv_writer = csv.writer(sys.stdout)
# Write the header row
csv_writer.writerow(['id', 'lat', 'lon', 'network'] + operators)

# Process each node element in the .osm file
for node in root.findall('node'):
    # Extract relevant attributes
    node_id = node.get('id')
    lat = node.get('lat')
    lon = node.get('lon')

    # Initialize variables for tags
    network = ''
    internet_access = ''

    # Extract information from tags
    for tag in node.findall('tag'):
        k = tag.get('k')
        v = tag.get('v')

        if k == 'network':
            network = v
        elif k == 'internet_access:operator':
            internet_access = v

    # Check which operators are mentioned in the 'internet_access:operator' tag
    operator_flags = [1 if op in internet_access else 0 for op in operators]

    # Write the extracted and processed information as a row in the CSV
    csv_writer.writerow([node_id, lat, lon, network] + operator_flags)
