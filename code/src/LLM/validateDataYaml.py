import regex as re  # Use 'regex' instead of 're'
import yaml
import pandas as pd
import argparse

def load_yaml(yaml_path):
    """Loads validation rules from a YAML file."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("validation_rules", [])

def validate_data(csv_path, validation_rules):
    """Validates data in a CSV file based on regex rules and mandatory constraints."""
    df = pd.read_csv(csv_path)  
    validation_results = []

    for index, row in df.iterrows():
        row_errors = []
        for rule in validation_rules:
            column_name = rule.get("Technical Field Name", "").replace(" ", "_")  
            regex_pattern = rule.get("Regex", "")
            is_mandatory = rule.get("Is Mandatory", "Optional").lower()
            anomaly_message = rule.get("Anomaly Message", f"Invalid data in {column_name}")

            if column_name in df.columns:
                value = str(row[column_name]).strip() if pd.notna(row[column_name]) else ""

                # Check for missing mandatory fields
                if is_mandatory == "mandatory" and value == "":
                    row_errors.append({"Row": index + 1, "Column": column_name, "Anomaly Message": f"{column_name} is required"})
                
                # Validate regex if value exists
                elif value and not re.fullmatch(regex_pattern, value):
                    row_errors.append({"Row": index + 1, "Column": column_name, "Anomaly Message": anomaly_message})
        
        # Calculate anomaly score (number of failed validations per row)
        anomaly_score = len(row_errors)
        for error in row_errors:
            error["Anomaly Score"] = anomaly_score  

        validation_results.extend(row_errors)

    return pd.DataFrame(validation_results)

def save_validation_report(errors_df, output_file):
    """Saves validation errors to a CSV file."""
    errors_df.to_csv(output_file, index=False)
    print(f"Validation report saved to {output_file}")

# ----------- Main Execution -----------
if __name__ == "__main__":
    #yaml_file = "C://Narasimha//Personal//Hackathon//validation_rules.yaml"  
    #csv_file = "C://Narasimha//Personal//Hackathon//data.csv"  
    #output_file = "C://Narasimha//Personal//Hackathon//validation_report.csv"
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", required=True, help="Path to the input CSV file")
    parser.add_argument("--output_csv", required=True, help="Path to the report CSV file")
    args = parser.parse_args()
    yaml_file = "validation_rules.yaml"  
    csv_file = args.input_csv
    output_file = args.output_csv
    validation_rules = load_yaml(yaml_file)
    errors_df = validate_data(csv_file, validation_rules)

    if not errors_df.empty:
        save_validation_report(errors_df, output_file)
    else:
        print("No validation errors found.")
