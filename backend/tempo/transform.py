import xarray as xr
import pandas as pd
import numpy as np
import os
from datetime import datetime
import glob

def create_transformed_directory():
    """Create the transformed directory if it doesn't exist"""
    if not os.path.exists("transformed"):
        os.makedirs("transformed")

def extract_timestamp_from_filename(filename):
    """Extract timestamp from TEMPO filename"""
    # Example: TEMPO_HCHO_L3_NRT_V02_20250920T140144Z_S005.nc
    # Extract: 20250920T140144Z
    try:
        parts = filename.split('_')
        for part in parts:
            if 'T' in part and 'Z' in part and len(part) > 10:
                # Convert to datetime
                timestamp_str = part.replace('Z', '')
                return datetime.strptime(timestamp_str, '%Y%m%dT%H%M%S')
    except:
        pass
    return None

def process_tempo_file(file_path, output_dir="transformed", sample_rate=100):
    """Process a single TEMPO .nc file and convert to CSV format
    
    Args:
        file_path: Path to the .nc file
        output_dir: Directory to save CSV files
        sample_rate: Sample every Nth point to reduce file size (default: 100)
    """
    
    print(f"Processing: {file_path}")
    
    try:
        # Open the NetCDF file
        ds = xr.open_dataset(file_path)
        
        # Extract timestamp from filename
        filename = os.path.basename(file_path)
        timestamp = extract_timestamp_from_filename(filename)
        
        if timestamp is None:
            print(f"Could not extract timestamp from {filename}")
            return
        
        # Get the data variables
        data_vars = list(ds.data_vars.keys())
        print(f"Data variables found: {data_vars}")
        
        # Process each data variable
        for var_name in data_vars:
            var_data = ds[var_name]
            
            # Get coordinates
            if 'latitude' in ds.coords and 'longitude' in ds.coords:
                lats = ds['latitude'].values
                lons = ds['longitude'].values
            else:
                print(f"No latitude/longitude coordinates found in {filename}")
                continue
            
            # Create a grid of lat/lon coordinates
            if len(var_data.dims) == 2:  # 2D data (lat, lon)
                lon_grid, lat_grid = np.meshgrid(lons, lats)
                values = var_data.values
                
                # Sample the data to reduce file size
                if sample_rate > 1:
                    # Sample every Nth point
                    lat_indices = np.arange(0, lat_grid.shape[0], sample_rate)
                    lon_indices = np.arange(0, lon_grid.shape[1], sample_rate)
                    lat_grid = lat_grid[np.ix_(lat_indices, lon_indices)]
                    lon_grid = lon_grid[np.ix_(lat_indices, lon_indices)]
                    values = values[np.ix_(lat_indices, lon_indices)]
                
                # Flatten the data
                flat_lats = lat_grid.flatten()
                flat_lons = lon_grid.flatten()
                flat_values = values.flatten()
                
                # Create DataFrame
                df = pd.DataFrame({
                    'location_id': f'tempo_{var_name}_{timestamp.strftime("%Y%m%d_%H%M")}',
                    'location_name': f'TEMPO_{var_name}_{timestamp.strftime("%Y%m%d_%H%M")}',
                    'parameter': var_name,
                    'value': flat_values,
                    'unit': var_data.attrs.get('units', 'unknown'),
                    'datetimeUtc': timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'datetimeLocal': timestamp.strftime('%Y-%m-%dT%H:%M:%SZ'),  # Same as UTC for now
                    'timezone': 'UTC',
                    'latitude': flat_lats,
                    'longitude': flat_lons,
                    'country_iso': '',  # Not available in TEMPO data
                    'isMobile': False,
                    'isMonitor': False,
                    'owner_name': 'NASA TEMPO',
                    'provider': 'NASA TEMPO'
                })
                
                # Remove rows with NaN values
                df = df.dropna(subset=['value'])
                
                # Sort by datetimeUtc descending (like OpenAQ format)
                df = df.sort_values(by='datetimeUtc', ascending=False)
                
                # Create output filename
                output_filename = f"tempo_{var_name}_{timestamp.strftime('%Y%m%d_%H%M')}.csv"
                output_path = os.path.join(output_dir, output_filename)
                
                # Save to CSV
                df.to_csv(output_path, index=False)
                print(f"Saved: {output_path} ({len(df)} records)")
                
            else:
                print(f"Unsupported data dimensions for {var_name}: {var_data.dims}")
        
        ds.close()
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    """Main function to process all TEMPO files"""
    print("Starting TEMPO data transformation...")
    print("Note: Current files only contain 'weight' data (area weights for Level 2 pixel overlap)")
    print("This script will process the weight data as a placeholder for HCHO data")
    
    # Create output directory
    create_transformed_directory()
    
    # Find all .nc files in the TEMPO directory
    tempo_dir = "TEMPO_HCHO_L3_NRT_V02-20251004_195203"
    if not os.path.exists(tempo_dir):
        print(f"TEMPO directory not found: {tempo_dir}")
        return
    
    nc_files = glob.glob(os.path.join(tempo_dir, "*.nc"))
    print(f"Found {len(nc_files)} .nc files")
    
    # Process all files
    print(f"Processing all {len(nc_files)} files...")
    
    # Process each file
    for i, file_path in enumerate(nc_files):
        print(f"\nProcessing file {i+1}/{len(nc_files)}")
        process_tempo_file(file_path, sample_rate=200)  # Sample every 200th point
    
    print("\nTransformation complete!")
    print(f"Processed {len(nc_files)} files total")

if __name__ == "__main__":
    main()
