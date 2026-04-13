# process_data/read.py
import geopandas as gp
import pandas as pd
import numpy as np
import extract as ex

def read_lines(main_directory, basin, year):
    # 1. Load Dam Data
    dam_actual_path = main_directory + "dam_data/dam.shp"
    dams = gp.read_file(dam_actual_path)
    
    if year == 'no_dams':
        dams = dams.iloc[0:0] # Creates an empty dataframe
    else:
        # 🌟 RULE 1: STRICT YEAR FILTERING 🌟
        # If Year value is null (NaN) or NoData (-99/0), do not include the dam.
        dams = dams[dams['YEAR_DAM'].notna()]
        dams = dams[dams['YEAR_DAM'] > 0] 
        # Must be built on or before the current decade loop
        dams = dams[dams['YEAR_DAM'] <= int(year)]
        
        # 🌟 RULE 2: STORAGE FALLBACK LOGIC 🌟
        # First check 'CAP_MCM'. If it is null or 0, use the value of 'Gross_Stor'
        if 'Gross_Stor' in dams.columns:
            dams['CAP_MCM'] = np.where(
                dams['CAP_MCM'].isna() | (dams['CAP_MCM'] == 0), 
                dams['Gross_Stor'], 
                dams['CAP_MCM']
            )
            
        # Fill any lingering NaNs with 0 to safely do the math below
        dams['CAP_MCM'] = dams['CAP_MCM'].fillna(0)
        
        # 🌟 RULE 3: SKIP IF BOTH NULL 🌟
        # If both storage columns were null/0, the value is now 0. 
        # By keeping only dams with CAP_MCM > 0, we automatically skip the empty ones!
        dams = dams[dams['CAP_MCM'] > 0]
        
    # Rename HYRIV_ID to REACH_ID so it matches the river dataset
    if 'HYRIV_ID' in dams.columns:
        dams = dams.rename(columns={'HYRIV_ID': 'REACH_ID'})

    # 2. Load River Flowlines
    flowlines = gp.read_file(main_directory + 'flowline_data/river_peninsular.shp')
    
    # Filter to current basin using the dictionary
    basin_codes = ex.major_basins[basin]
    flowlines = flowlines[flowlines['BASIN'].isin(basin_codes)]
    
    return dams, flowlines