# make_figures/create_csvs.py
import pandas as pd
import geopandas as gp
import glob, os

def combined_huc_csv(basin_ls, results_folder, year):
    summary_list =[results_folder + f for f in os.listdir(results_folder) if f.endswith('HYBAS_ID_indices.csv')]
    if summary_list:
        combined_csv = pd.concat([pd.read_csv(f) for f in summary_list])
        combined_csv.to_csv(results_folder + 'HYBAS_summary_' + year + '.csv', index=False)

def combined_segGeo_csv(basin_ls, results_folder, year):
    shp_list =[results_folder + f for f in os.listdir(results_folder) if f.endswith('_segGeo_'+year+'.shp')]
    if shp_list:
        combined_shp = pd.concat([gp.read_file(f) for f in shp_list])
        combined_shp.to_file(results_folder + 'All_basins_segGeo_' + year + '.shp')

def combined_frag_csv(basin_ls, results_folder, year):
    frag_list =[results_folder + f for f in os.listdir(results_folder) if f.endswith('_fragments_'+year+'.csv')]
    if frag_list:
        combined_csv = pd.concat([pd.read_csv(f) for f in frag_list])
        combined_csv.to_csv(results_folder + 'All_basins_fragments_' + year + '.csv', index=False)