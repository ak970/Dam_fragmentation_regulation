# process_data/read.py
import geopandas as gp
import pandas as pd
import process_data.extract as ex

def read_lines(main_directory, basin, year):
    # 1. Load Dam Data
    dam_actual_path = main_directory + "dam_data/dam.shp"
    dams = gp.read_file(dam_actual_path)
    
    # 🌟 THE FIX: Handling the -99 NoData values for the timeline
    if year != 'no_dams':
        if year == '2020': 
            # Modern Day: Include all valid dams <= 2020 PLUS the unknown (-99) dams
            dams = dams[(dams['Year_dam'] <= int(year)) | (dams['Year_dam'] == -99)]
        else:
            # Historical Years: Only include dams with a KNOWN year <= target year. 
            # The (dams['Year_dam'] > 0) strictly removes the -99 values!
            dams = dams[(dams['Year_dam'] <= int(year)) & (dams['Year_dam'] > 0)]
    else:
        dams = dams.iloc[0:0] # Creates an empty dataframe if 'no_dams'
        
    # Rename HYRIV_ID to REACH_ID so it matches the river dataset
    if 'HYRIV_ID' in dams.columns:
        dams = dams.rename(columns={'HYRIV_ID': 'REACH_ID'})

    # 2. Load River Flowlines
    flowlines = gp.read_file(main_directory + 'flowline_data/FFR_peninsular_updated2.shp')
    
    # Filter to current basin using the extract.py dictionary
    basin_codes = ex.major_basins[basin]
    flowlines = flowlines[flowlines['BASIN'].isin(basin_codes)]
    
    return dams, flowlines