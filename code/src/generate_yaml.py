import pandas as pd
import yaml

# Load the CSV file
file_path = 'processed_ruleset.csv'
df = pd.read_csv(file_path)

# Prepare a list of dictionaries for YAML generation following the required format
rules_list = []
for _, row in df.iterrows():
    rule = {
        'Field No.': str(row['Field_Number']),
        'Field Name': row['Technical_Name'],
        'Technical Field Name': row['Technical_Name'],
        'Description': row['Description'],
        'Allowable Values': row['Allowable Values']
    }
    rules_list.append(rule)

# Define the structure of the YAML document
yaml_data = {'rules': rules_list}

# Specify the path for the YAML output file
yaml_output_path = 'processed_ruleset.yaml'

# Write the YAML file
with open(yaml_output_path, 'w') as yaml_file:
    yaml.dump(yaml_data, yaml_file, default_flow_style=False)

print(f"YAML file has been generated and saved at {yaml_output_path}")
