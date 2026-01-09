
import json
import os

notebook_path = r'd:/Subek/project/Draft/UKI/Best time post v2/notebooks/neuralprophet_daily_v2.ipynb'

try:
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    found_init = False
    for cell in nb['cells']:
        if cell['cell_type'] == 'code':
            source = "".join(cell['source'])
            if "model = NeuralProphet(" in source:
                # Add holidays after model initialization
                if "add_country_holidays" not in source:
                    # Find the end of NeuralProphet call
                    lines = cell['source']
                    
                    # We will append the holiday call at the end of the cell
                    # Check if log_level line exists or the end of constructor
                    
                    new_lines = []
                    for line in lines:
                        new_lines.append(line)
                        if "model = NeuralProphet(" in "".join(lines) and ")" in line and "n_lags" not in line and "n_forecasts" not in line and "ar_layers" not in line: 
                             # This logic is tricky if ')' is not on the last line. 
                             pass
                    
                    # Safer approach: Append to the end of the source list
                    cell['source'].append("\n")
                    cell['source'].append("# Add Indonesian holidays\n")
                    cell['source'].append("model.add_country_holidays(country_name='ID')\n")
                    
                    print("Added add_country_holidays to model initialization cell.")
                    found_init = True
                    break
    
    if found_init:
        with open(notebook_path, 'w', encoding='utf-8') as f:
            json.dump(nb, f, indent=1)
        print(f"Successfully updated {notebook_path}")
    else:
        print("Could not find model initialization cell.")

except Exception as e:
    print(f"Error: {e}")
