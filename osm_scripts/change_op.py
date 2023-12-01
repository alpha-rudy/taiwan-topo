import xml.etree.ElementTree as ET
import sys

def process_node(node):
    # Check if the node already has action='modify'
    if node.get('action') != 'modify':
        for tag in node.findall('tag'):
            # Check for the 'internet_access:operator' tag
            if tag.get('k') == 'internet_access:operator':
                operators = tag.get('v').split(';')
                
                # Case 1
                if '台灣大哥大' in operators and '台灣之星' in operators:
                    operators.remove('台灣之星')
                    tag.set('v', ';'.join(operators))
                
                # Case 2
                elif '台灣之星' in operators and '台灣大哥大' not in operators:
                    tag.set('v', tag.get('v').replace('台灣之星', '台灣大哥大'))

        # Add action='modify' to the node
        node.set('action', 'modify')

def main():
    # Parse the XML from stdin
    tree = ET.parse(sys.stdin)
    root = tree.getroot()

    # Process each node
    for node in root.findall('node'):
        process_node(node)

    # Output the modified XML to stdout
    tree.write(sys.stdout, encoding='unicode')

if __name__ == '__main__':
    main()
