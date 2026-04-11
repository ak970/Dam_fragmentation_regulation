import geopandas as gp
import pandas as pd
import numpy as np
import os
import read as rd
import bifurcate as bfc

main_directory = 'D:/Peninsular India/Dam_fragmentation/'

years =['no_dams', '1980', '1990', '2000', '2010', '2020']
basin_ls =['godavari', 'krishna', 'cauvery', 'subernarekha', 'brahmani_baitarni', 
            'mahanadi', 'pennar', 'mahi', 'sabarmati', 'narmada', 'tapi', 
            'wfr_tapi_tadri', 'wfr_tadri_kanyakumari', 'efr_mahanadi_pennar', 'efr_pennar_kanyakumari']

for year in years:
    results_folder = main_directory + 'Output/analyzed_data/' + str(year) + '/'
    os.makedirs(results_folder, exist_ok=True)

    for basin in basin_ls:
        print(f"----- Starting {basin} ({year}) -----")
        
        nabd_dams, flowlines = rd.read_lines(main_directory, basin, year)
        
        # Unit Conversions
        flowlines['DIS_AV_CMS'] = (flowlines['DIS_AV_CMS'] * 365 * 24 * 3600) / (10**6)
        
        # Aggregate dams
        nabd_dams['CAP_MCM'] = nabd_dams['CAP_MCM'].fillna(0)
        dams_agg = nabd_dams.groupby('REACH_ID').agg({'CAP_MCM': 'sum', 'GDW_ID': 'count'}).reset_index()
        dams_agg.rename(columns={'GDW_ID': 'DamCount'}, inplace=True)
        dams_agg['DamID'] = range(1, len(dams_agg)+1)
        
        # Merge dams onto rivers
        segments = flowlines.merge(dams_agg, on='REACH_ID', how='left')
        segments['DamCount'] = segments['DamCount'].fillna(0)
        segments['CAP_MCM'] = segments['CAP_MCM'].fillna(0)
        segments['DamID'] = segments['DamID'].fillna(0)

        # Ensure NOID is strictly set as the index to prevent duplication!
        segments = segments.set_index('NOID', drop=False)

        # 1. Aggregate Upstream attributes 
        segments_up = bfc.upstream_ag(data=segments, downIDs='NDOID', upIDs='NUOID', basin=basin, attr=['CAP_MCM', 'DamCount'])
        
        # Map values safely and directly using the index!
        segments['CAP_MCM_up'] = segments_up['CAP_MCM_up']
        segments['DamCount_up'] = segments_up['DamCount_up']

        # 2. Calculate DOR safely
        segments['DOR'] = 0.0
        segments.loc[(segments['DIS_AV_CMS'] == 0) & (segments['CAP_MCM_up'] > 0), 'DOR'] = -1
        segments.loc[segments['DIS_AV_CMS'] > 0, 'DOR'] = segments['CAP_MCM_up'] / segments['DIS_AV_CMS']

        # 3. Create Fragments Safely
        segments['FragEnd'] = 0
        segments.loc[segments['DamID'] > 0, 'FragEnd'] = 2 
        segments.loc[segments['NDOID'] == 0, 'FragEnd'] = 1 
        
        # Execute fragment mapping
        fragments_mapping = bfc.make_fragments(segments, downIDs='NDOID', upIDs='NUOID', basin=basin)
        segments['Frag_Index'] = fragments_mapping['Frag_Index']
        
        # Calculate fragment statistics cleanly
        fragments = segments.groupby('Frag_Index').agg({
            'LENGTH_KM': 'sum', 
            'DamCount': 'sum', 
            'CAP_MCM': 'sum',
            'HYBAS_ID': 'first'
        }).reset_index()

        # 4. Summarize and group by Catchment
        HUC_vallist = ['HYBAS_ID']
        for HUC_val in HUC_vallist:
            HUC_summary = segments.pivot_table(values=['CAP_MCM', 'DamCount', 'LENGTH_KM'], index=HUC_val, aggfunc="sum")
            HUC_summaryf = fragments.pivot_table(values=['LENGTH_KM'], index=HUC_val, aggfunc="mean")
            
            HUC_summary = HUC_summary.join(HUC_summaryf, rsuffix='_mean')
            HUC_summary.to_csv(results_folder + basin + '_' + HUC_val + '_indices.csv')

        # 5. Save basin outputs

        segments = segments.reset_index(drop=True)  # 🌟 THE FIX: Drops the index labels to prevent the duplicate column error
        
        segmentsGeo = gp.GeoDataFrame(segments, geometry='geometry')
        segmentsGeo.crs = "EPSG:4326"
        segmentsGeo.to_file(results_folder + basin + '_segGeo_' + year + '.shp')
        
        fragments_df = pd.DataFrame(fragments)
        fragments_df.to_csv(results_folder + basin + '_fragments_' + year + '.csv')

print("All runs complete!")