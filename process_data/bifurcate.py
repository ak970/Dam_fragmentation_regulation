# process_data/bifurcate.py
import pandas as pd

def upstream_ag(data, downIDs, upIDs, basin, attr):
    # Ensure we are working with a clean copy
    df = data.copy()
    
    # Initialize the upstream storage tracking columns
    for a in attr:
        df[a+'_up'] = df[a].fillna(0)
    df['upstream_count'] = 1
    
    # Calculate "in-degrees" (How many rivers flow INTO a specific segment)
    in_degree = df.groupby(downIDs).size().to_dict()
    
    # Initialize Queue with "Headwaters" (Segments that have NO rivers flowing into them)
    queue =[nid for nid in df.index if nid not in in_degree]
    
    # Top-Down Graph Traversal (From headwaters to the ocean)
    while queue:
        curr = queue.pop(0)
        dn = df.at[curr, downIDs]
        
        # If the downstream segment exists in our map, push the water/dams downstream!
        if dn in df.index and dn != 0:
            for a in attr:
                df.at[dn, a+'_up'] += df.at[curr, a+'_up']
            df.at[dn, 'upstream_count'] += df.at[curr, 'upstream_count']
            
            # Decrement the dependency tracker
            in_degree[dn] -= 1
            if in_degree[dn] == 0:
                queue.append(dn)
                
    return df[[a+'_up' for a in attr] + ['upstream_count']]


def make_fragments(segments, downIDs, upIDs, basin):
    frag_dict = {}
    queue =[]
    
    # 1. Identify all Fragment Outlets (Dams and Ocean/Terminal nodes)
    frag_ends = segments[segments['FragEnd'] > 0]
    
    # Give every outlet its own unique Fragment Index
    for i, (noid, _) in enumerate(frag_ends.iterrows(), start=1):
        frag_dict[noid] = i
        queue.append(noid)
        
    # Pre-group the upstream segments for instant dictionary lookup
    upstream_map = segments.groupby(downIDs).groups
    
    # 2. Bottom-Up Traversal (Walk upstream from every dam and paint the river branches)
    while queue:
        curr = queue.pop(0)
        curr_frag = frag_dict[curr]
        
        if curr in upstream_map:
            for up in upstream_map[curr]:
                # If the upstream segment doesn't have an ID yet, inherit this one!
                if up not in frag_dict:
                    frag_dict[up] = curr_frag
                    queue.append(up)
                    
    # Format the clean dictionary back into a Pandas DataFrame
    out_df = pd.DataFrame.from_dict(frag_dict, orient='index', columns=['Frag_Index'])
    out_df.index.name = segments.index.name
    
    return out_df