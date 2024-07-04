import overpy
import csv

def count_peaks_in_taiwan(api, year):
    date = f"{year}-07-04T00:00:00Z"
    query = f"""
    [date:"{date}"];
    area(3600449220)->.searchArea;
    (
      node["natural"="peak"](area.searchArea);
    );
    out;
    """
    result = api.query(query)
    return len(result.nodes)

def generate_csv_file():
    api = overpy.Overpass()
    years = range(2000, 2025)
    
    with open('peaks_in_taiwan.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Year', 'Date', 'Count of Peaks'])  # Header row
        
        for year in years:
            try:
                peak_count = count_peaks_in_taiwan(api, year)
                writer.writerow([year, f"{year}-07-04", peak_count])
                print(f"Data for {year} added to peaks_in_taiwan.csv")
            except Exception as e:
                print(f"Error processing data for {year}: {e}")

# Run the function to generate the CSV file
generate_csv_file()
