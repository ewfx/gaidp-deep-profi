import os
import re
import yaml
import ollama  # Use Ollama for local LLM execution

# Function to generate validation regex using Mistral-7B
def generate_validation_regex(description, allowable_values):
    """
    Uses Ollama's Mistral-7B model to generate a regex validation pattern 
    based on the field description and allowable values.
    """
    prompt = f"""
    You are an expert in data validation and regular expressions.
    Generate a strict and optimized regex pattern for data validation.

    ### Instructions:
    - Ensure the regex **strictly matches** valid values and rejects invalid ones.
    - Consider format, special characters, and length constraints.
    - If no allowable values are provided, infer the pattern based on the description.
    - Provide **only** the regex pattern without explanation.

    ### Input:
    - **Description**: {description}
    - **Allowable Values**: {allowable_values}

    ### Expected Output:
    - Just the regex pattern.
    """

    response = ollama.chat(model='mistral', messages=[{'role': 'user', 'content': prompt}])
    regex = str(response['message']['content']).strip()

    # Remove extra quotes if any
    regex = re.sub(r'^"|"$', '', regex)  

    return regex

# Function to check if a column is mandatory
def is_column_mandatory(description):
    """
    Determines if a column is mandatory based on its description.
    """
    if not description:
        return "Optional"
    
    mandatory_keywords = ["required", "must", "mandatory", "not null"]
    return "Mandatory" if any(word in description.lower() for word in mandatory_keywords) else "Optional"

# Function to generate an anomaly message
def generate_anomaly_message(technical_field_name, description, allowable_values):
    """
    Creates an anomaly message explaining why validation failed.
    """
    return f"Invalid data in '{technical_field_name}'. Expected: {description} with allowed values {allowable_values}."

# Function to load YAML file
def load_yaml(yaml_path):
    """
    Loads field definitions from a YAML file.
    """
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("rules", [])

# Function to save results to a YAML file
def save_results_to_yaml(results, output_yaml):
    """
    Saves validation rules to a YAML file.
    """
    data = {"validation_rules": results}
    with open(output_yaml, "w", encoding="utf-8") as outfile:
        yaml.dump(data, outfile, sort_keys=False, default_flow_style=False)
    print(f"Validation rules saved to {output_yaml}")

# ---------------- Main Execution ----------------
if __name__ == "__main__":
    #input_yaml = "C://Narasimha//Personal//Hackathon//rules.yaml"  # Update path
    #output_yaml = "C://Narasimha//Personal//Hackathon//validation_rules.yaml"  # Output file
    input_yaml = "rules.yaml"  # Update path
    output_yaml = "validation_rules.yaml"  # Output file

    rules = load_yaml(input_yaml)
    validation_results = []

    for rule in rules:
        technical_field_name = rule.get("Technical Field Name", "").replace(" ", "_")  # Remove spaces in field name
        description = rule.get("Description", "")
        allowable_values = rule.get("Allowable Values", "")

        regex = generate_validation_regex(description, allowable_values)
        is_mandatory = is_column_mandatory(description)
        anomaly_message = generate_anomaly_message(technical_field_name, description, allowable_values)

        validation_results.append({
            "Technical Field Name": technical_field_name,
            "Is Column Mandatory": is_mandatory,
            "Regex": regex,
            "Anomaly Message": anomaly_message
        })

        print(f"Generated Validation for: {technical_field_name}")
        print(f"  - Is Mandatory: {is_mandatory}")
        print(f"  - Regex: {regex}")
        print(f"  - Anomaly Message: {anomaly_message}\n")

    save_results_to_yaml(validation_results, output_yaml)
