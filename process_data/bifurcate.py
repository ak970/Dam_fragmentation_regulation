# process_data/bifurcate.py
import numpy as np
import pandas as pd

def upstream_ag(data, downIDs, upIDs, basin, attr):
    data = data.set_index(downIDs, drop=False)
    up_agg = data[[upIDs] + attr].copy()
    
    # Initialize counts
    up_agg['upstream_count'] = np.ones(len(up_agg))
    for a in attr:
        up_agg[a+'_up'] = up_agg[a]
        
    queuef = pd.DataFrame()
    queue = pd.DataFrame([data.loc[data[downIDs][~data[downIDs].isin(data[upIDs])]]])
    queue = pd.concat([pd.DataFrame(), data.loc[~data[downIDs].isin(data[upIDs])]])

    while len(queue) > 0:
        DnTemp = queue.iloc[0][downIDs]
        UpTemp = queue.iloc[0][upIDs]
        
        if UpTemp in up_agg.index:
            up_agg.loc[UpTemp, 'upstream_count'] += up_agg.loc[DnTemp, 'upstream_count']
            for a in attr:
                up_agg.loc[UpTemp, a+'_up'] += up_agg.loc[DnTemp, a+'_up']
                
            queue = pd.concat([queue, data.loc[[UpTemp]]]).drop_duplicates(subset=[downIDs])
            
        queuef = pd.concat([queuef, up_agg.loc[[DnTemp]]])
        queue = queue.iloc[1:]

    return queuef[[a+'_up' for a in attr] + ['upstream_count']]


def make_fragments(segments, downIDs, upIDs, basin):
    FragEnds = segments.loc[segments['FragEnd'] > 0].copy()
    FragEnds['NOID'] = FragEnds.index
    fragments = pd.DataFrame()

    queue = pd.DataFrame(segments.loc[segments['FragEnd'] == 1])
    queue['Frag_Index'] = range(1, len(queue) + 1)
    fragments = queue.copy()

    while len(queue) > 0:
        UpTemp = queue.iloc[0][upIDs]
        Frag_Index = queue.iloc[0]['Frag_Index']
        
        if UpTemp in segments.index:
            temp_row = segments.loc[[UpTemp]].copy()
            if temp_row.iloc[0]['FragEnd'] > 0:
                temp_row['Frag_Index'] = FragEnds.index.get_loc(UpTemp) + len(queue) + 1
            else:
                temp_row['Frag_Index'] = Frag_Index
                
            fragments = pd.concat([fragments, temp_row])
            queue = pd.concat([queue, temp_row])
            
        queue = queue.iloc[1:]
        
    # Aggregate fragment attributes
    fragments0 = fragments.groupby('Frag_Index').agg({'LENGTHKM': 'sum', 'DamCount': 'sum', 'Cap_mcm': 'sum'})
    return fragments0