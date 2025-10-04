
import json
import pandas as pd
import os

# Create the output directory if it doesn't exist
if not os.path.exists("transformed"):
    os.makedirs("transformed")

with open("data/headers.json", "r") as f:
    headers_data = json.load(f)

for filename in headers_data["files"]:
    filepath = os.path.join("data", filename)
    df = pd.read_csv(filepath)
    
    # Get the location_id from the first row
    location_id = df["location_id"].iloc[0]
    
    # Get unique parameters
    parameters = df["parameter"].unique()
    
    for param in parameters:
        # Filter by parameter
        param_df = df[df["parameter"] == param]
        
        # Sort by datetimeUtc descending
        param_df = param_df.sort_values(by="datetimeUtc", ascending=False)
        
        # Create new filename
        new_filename = f"{location_id}_{param}.csv"
        
        # Write to new CSV
        param_df.to_csv(os.path.join("transformed", new_filename), index=False)
