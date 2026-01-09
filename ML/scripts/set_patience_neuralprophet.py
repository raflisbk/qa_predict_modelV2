
import json
import os
import re

notebook_path = r'd:/Subek/project/Draft/UKI/Best time post v2/notebooks/neuralprophet_daily_v2.ipynb'

try:
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    found_fit = False
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = "".join(cell['source'])
            if "model.fit" in source:
                # We found the training cell.
                # We need to replace early_stopping=True with early_stopping=20
                print("Found model.fit cell.")
                
                new_source = []
                for line in cell['source']:
                    if "early_stopping=True" in line:
                        new_line = line.replace("early_stopping=True", "early_stopping=20")
                        new_source.append(new_line)
                        print(f"Replaced: {line.strip()} -> {new_line.strip()}")
                        found_fit = True
                    else:
                        new_source.append(line)
                
                cell['source'] = new_source
                break 
    
    if found_fit:
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print(f"Successfully updated {notebook_path} with patience=20")
    else:
        print("Could not find 'early_stopping=True' in model.fit cell. Maybe it's already changed or different format.")

except Exception as e:
    print(f"Error: {e}")
