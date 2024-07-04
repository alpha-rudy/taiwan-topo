import overpy

def count_peaks_in_taiwan(date):
    api = overpy.Overpass()

    # Overpass QL query
    # The date should be formatted as YYYY-MM-DDTHH:MM:SSZ
    query = f"""
    [date:"{date}"];
    area(3600449220)->.searchArea;
    (
      node["natural"="peak"](area.searchArea);
    );
    out;
    """
    
    result = api.query(query)
    # Count the number of nodes in the result
    peak_count = len(result.nodes)
    return peak_count

# Example usage
date = "2024-07-04T00:00:00Z"  # Specify your date here
try:
    peak_count = count_peaks_in_taiwan(date)
    print(f"Number of natural=peak nodes in Taiwan on {date}: {peak_count}")
except Exception as e:
    print(f"Error querying OSM data: {e}")
