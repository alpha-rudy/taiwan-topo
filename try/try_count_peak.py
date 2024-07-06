import overpy
import csv

from datetime import datetime

def generate_query(date):
    # Converts date to the required format and generates the Overpass query
    formatted_date = date.strftime("%Y-%m-%dT00:00:00Z")
    query = f"""
    [date:"{formatted_date}"];
    area(3600449220)->.searchArea;
    (
      node["natural"="peak"](area.searchArea);
    );
    out;
    """
    return query

def count_peaks(api, query):
    # Execute the query and return the count of results
    result = api.query(query)
    return len(result.nodes)

def generate_csv_file():
    api = overpy.Overpass()
    start_date = datetime(2021, 7, 4)
    end_date = datetime(2022, 7, 5)

    with open('monthly_peaks_in_taiwan.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Date', 'Count of Peaks'])  # Header row
        
        current_date = start_date
        while current_date <= end_date:
            query = generate_query(current_date)
            
            # Save each query to a separate file
            query_file_name = f"query_{current_date.strftime('%Y-%m-%d')}.txt"
            with open(query_file_name, 'w') as query_file:
                query_file.write(query)
                print(f"Query for {current_date.strftime('%Y-%m-%d')} saved to {query_file_name}")
            
            try:
                peak_count = count_peaks(api, query)
                writer.writerow([current_date.strftime("%Y-%m-%d"), peak_count])
                print(f"Data for {current_date.strftime('%Y-%m-%d')} added to monthly_peaks_in_taiwan.csv")
            except Exception as e:
                print(f"Error processing data for {current_date.strftime('%Y-%m-%d')}: {e}")
            
            # Increment to the 4th of the next month
            month = current_date.month + 1 if current_date.month < 12 else 1
            year = current_date.year if current_date.month < 12 else current_date.year + 1
            current_date = datetime(year, month, 4)

# Run the function to generate the CSV file and store queries
generate_csv_file()
