# make_figures/summarize.py
import create_csvs as crc
import huc_merge as hm
import os

main_directory = 'D:/Peninsular India/Dam_fragmentation/'

years =['no_dams', '1980', '1990', '2000', '2010', '2020']
basin_ls =['godavari', 'krishna', 'cauvery', 'subernarekha', 'brahmani_baitarni', 
            'mahanadi', 'pennar', 'mahi', 'sabarmati', 'narmada', 'tapi', 
            'wfr_tapi_tadri', 'wfr_tadri_kanyakumari', 'efr_mahanadi_pennar', 'efr_pennar_kanyakumari']

for year in years:
    print(f"\n---------------{year}---------------")
    results_folder2 = main_directory + 'Output/analyzed_data/' + str(year) + '/'

    # 1. Combine Basin outputs
    crc.combined_huc_csv(basin_ls, results_folder2, year)
    crc.combined_segGeo_csv(basin_ls, results_folder2, year)
    crc.combined_frag_csv(basin_ls, results_folder2, year)

    # 2. Merge with Catchment Shapefile
    # (Assuming you put hybasin.shp inside a folder named 'hucs')
    hybas = hm.HYBAS_indices_merge(results_folder2, year, main_directory)

print("\n** Summarize by HYBAS_ID and all_basins complete **")