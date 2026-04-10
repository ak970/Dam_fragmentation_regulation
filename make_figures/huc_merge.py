# make_figures/huc_merge.py
import pandas as pd
import geopandas as gp

def HYBAS_indices_merge(results_folder, year, main_directory):
    # Load data
    summary_df = pd.read_csv(results_folder + 'HYBAS_summary_' + year + '.csv')
    catchment = gp.read_file(main_directory + "hucs/hybasin.shp")
    
    # Keep only available geometry columns
    catchment = catchment.loc[:, ~catchment.columns.duplicated()]
    catchment = catchment[['HYBAS_ID', 'SUB_AREA', 'BASIN', 'geometry']] 

    # Clean the IDs to text to ensure perfect, zero-safe matching
    summary_df['HYBAS_ID_str'] = summary_df['HYBAS_ID'].astype(str).str.replace('.0', '', regex=False)
    catchment['HYBAS_ID_str'] = catchment['HYBAS_ID'].astype(str)

    # Merge
    catchment = catchment.merge(summary_df, on='HYBAS_ID_str', how='left')
    
    # Drop redundant tracking columns
    catchment = catchment.drop(columns=['HYBAS_ID_str', 'HYBAS_ID_y'])
    catchment = catchment.rename(columns={'HYBAS_ID_x': 'HYBAS_ID'})

    # Save output
    catchment.to_file(results_folder + 'hybasin_indices_' + year + '.shp')
    print('Finished writing HYBAS indices to shp for ' + year)
    
    return catchment