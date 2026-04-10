# process_data/run_workflow.py
import geopandas as gp
import pandas as pd
import numpy as np
import os
import process_data.read as rd
import process_data.bifurcate as bfc
import datetime

main_directory = 'D:/Peninsular India/Dam_fragmentation/'

# Loop through the decadal timescale
years =['no_dams', '1980', '1990', '2000', '2010', '2020']
basin_ls =['godavari', 'krishna', 'cauvery', 'subernarekha', 'brahmani_baitarni', 
            'mahanadi', 'pennar', 'mahi', 'sabarmati', 'narmada', 'tapi', 
            'wfr_tapi_tadri', 'wfr_tadri_kanyakumari', 'efr_mahanadi_pennar', 'efr_pennar_kanyakumari']

for year in years:
    results_folder = main_directory + 'Output/analyzed_data/' + str(year) + '/'
    os.makedirs(results_folder, exist_ok=True)

    for basin in basin_ls:
        print(f"----- Starting {basin} ({year}) -----")
        
        # Read filtered data
        nabd_dams, flowlines = rd.read_lines(main_directory, basin, year)
        
        # Ensure units are metric MCM/year
        # DIS_AV_CMS is converted from seconds to years, divided by 10^6 to reach MCM
        flowlines['DIS_AV_CMS'] = (flowlines['DIS_AV_CMS'] * 365 * 24 * 3600) / (10**6)
        
        # Aggregate dams in case multiple dams sit on the exact same REACH_ID
        nabd_dams['Cap_mcm'] = nabd_dams['Cap_mcm'].fillna(0)
        dams_agg = nabd_dams.groupby('REACH_ID').agg({'Cap_mcm': 'sum', 'GDW_ID': 'count'}).reset_index()
        dams_agg.rename(columns={'GDW_ID': 'DamCount'}, inplace=True)
        dams_agg['DamID'] = range(1, len(dams_agg)+1) # Internal Fragment Breaker ID
        
        # Merge dams onto rivers
        segments = flowlines.merge(dams_agg, on='REACH_ID', how='left')
        segments['DamCount'] = segments['DamCount'].fillna(0)
        segments['Cap_mcm'] = segments['Cap_mcm'].fillna(0)
        segments['DamID'] = segments['DamID'].fillna(0)

        # 1. Aggregate Upstream attributes (Cap_mcm and DamCount) using NOID mapping
        segments_up = bfc.upstream_ag(data=segments, downIDs='NDOID', upIDs='NUOID', basin=basin, attr=['Cap_mcm', 'DamCount'])
        segments = segments.merge(segments_up, left_on='NOID', right_index=True, how='left')

        # 2. Calculate DOR (Degree of Regulation) safely
        segments['DOR'] = 0.0
        segments.loc[(segments['DIS_AV_CMS'] == 0) & (segments['Cap_mcm_up'] > 0), 'DOR'] = -1
        segments.loc[segments['DIS_AV_CMS'] > 0, 'DOR'] = segments['Cap_mcm_up'] / segments['DIS_AV_CMS']

        # 3. Create Fragments
        segments['FragEnd'] = 0
        segments.loc[segments['DamID'] > 0, 'FragEnd'] = 2 # Dam is a fragment outlet
        segments.loc[segments['NDOID'] == 0, 'FragEnd'] = 1 # Ocean/Terminal is an outlet
        
        fragments = bfc.make_fragments(segments, downIDs='NDOID', upIDs='NUOID', basin=basin)
        segments = segments.merge(fragments, left_on='NOID', right_index=True, how='left')

        # 4. Summarize and group by HYBAS_ID
        HUC_vallist = ['HYBAS_ID']
        for HUC_val in HUC_vallist:
            HUC_summary = segments.pivot_table(values=['Cap_mcm', 'DamCount', 'LENGTHKM'], index=HUC_val, aggfunc="sum")
            HUC_summaryf = fragments.pivot_table(values=['LENGTHKM'], index=HUC_val, aggfunc="mean")
            
            HUC_summary = HUC_summary.join(HUC_summaryf, rsuffix='_mean')
            HUC_summary.to_csv(results_folder + basin + '_' + HUC_val + '_indices.csv')

        # 5. Save basin-specific segments and fragments
        segmentsGeo = gp.GeoDataFrame(segments, geometry='geometry')
        segmentsGeo.crs = "EPSG:4326" # Standard for HydroATLAS
        segmentsGeo.to_file(results_folder + basin + '_segGeo_' + year + '.shp')
        
        fragments_df = pd.DataFrame(fragments.drop(columns=['geometry'], errors='ignore'))
        fragments_df.to_csv(results_folder + basin + '_fragments_' + year + '.csv')

print("All runs complete!")