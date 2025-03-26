import re
import pdfplumber
import pandas as pd
import yaml
import argparse

#EXPECTED_HEADERS = {"Field No.", "Field Name;(Technical Field Name)", "Description", "Allowable Values"}

import unicodedata

# Helper function to split "Field Name;(Technical Field Name)" into two parts.
def split_field_name(field_text):
    """
    Splits a combined field string into a human-readable field name and a technical field name.
    For example, if field_text is "Customer ID (CustomerID)", it returns:
      ("Customer ID", "CustomerID")
    If no parentheses are found, returns (field_text, "").
    """
    field_text = field_text.strip()
    # Pattern: everything before '(' is the human-friendly name; inside parentheses is technical name.
    m = re.match(r"^(.*?)\s*\((.*?)\)$", field_text)
    if m:
        return m.group(1).strip(), m.group(2).replace(" ", "").strip()
    else:
        return field_text, ""

def clean_text(text):
    """
    Cleans text by:
      - Replacing newline characters with a space,
      - Converting various special Unicode characters (like curly quotes, right single quote, etc.)
        to their ASCII equivalents,
      - Normalizing the text (NFKD) and encoding to ASCII (ignoring errors) to remove other special chars,
      - Stripping extra whitespace.
    If text is None, returns an empty string.
    """
    if text is None:
        return ""
    
    # Replace common curly quotes and similar characters.
    replacements = {
        "\u201C": "\"",  # Left double quotation mark
        "\u201D": "\"",  # Right double quotation mark
        "\u2018": "'",   # Left single quotation mark
        "\u2019": "'",   # Right single quotation mark
        "\u2013": "-",   # En dash
        "\u2014": "-",   # Em dash
        "\u2026": "...", # Ellipsis
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Normalize the text to decompose characters.
    normalized = unicodedata.normalize("NFKD", text)
    # Encode to ASCII bytes (ignoring characters that cannot be encoded), then decode back to a string.
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_text.split()).strip()


def clean_header(header):
    """
    Cleans header text by removing newlines, extra spaces, and
    ensuring there is no space between ';' and '('.
    """
    header = clean_text(header)
    header = re.sub(r';\s*\(', ';(', header)
    return header

def extract_table_from_pdf(pdf_path):
    """
    Extracts table data from a PDF file using pdfplumber.
    Cleans and normalizes headers and cell values.
    Returns a list of dictionaries representing each row.
    """
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Adjust table_settings if needed.
            table = page.extract_table(table_settings={
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines"
            })
            n=0
            if table:
                # Clean and normalize headers using the clean_header function.
                headers = [clean_header(h) for h in table[0]]
                if page.page_number == 1:
                    EXPECTED_HEADERS = headers
                print(f"\nNormalized headers on page {page.page_number}: {headers}")
                header_missing = not bool(set(EXPECTED_HEADERS) & set(headers))
                if header_missing:
                    #print(f"Page {page.page_number} is flagged as missing header.")
                    n=0
                else:
                    n=1
                for row in table[n:]:
                    # Extend row if it's shorter than headers.
                    if len(row) < len(EXPECTED_HEADERS):
                        row = row + [None] * (len(EXPECTED_HEADERS) - len(row))
                    # Clean each cell in the row.
                    clean_row = [clean_text(cell) for cell in row]
                    row_dict = dict(zip(EXPECTED_HEADERS, clean_row))
                    rows.append(row_dict)
    return rows

def merge_continuation_rows(rows):
    """
    Iterates over the list of rows (each a dictionary). If a row's "Field No." (after stripping)
    is empty, it is treated as a continuation row: its "Description" and "Allowable Values"
    are appended to the previous row. Otherwise, the row is treated as a new field.
    """
    merged_rows = []
    prev_row = None
    #print(len(rows))
    for i, row in enumerate(rows):
        #print(i)
        
        field_no = row.get("Field No.", "")
        if field_no.strip() == "":
            # Continuation row: append description and allowed values to the previous row.
            if prev_row is not None:
                desc = row.get("Description", "").strip()
                allow_vals = row.get("Allowable Values", "").strip()
                if desc:
                    # Append (with a space) to previous row's description.
                    prev_desc = prev_row.get("Description", "").strip()
                    prev_row["Description"] = (prev_desc + " " + desc).strip() if prev_desc else desc
                if allow_vals:
                    # Append (with a space) to previous row's allowed values.
                    prev_allow = prev_row.get("Allowable Values", "").strip()
                    prev_row["Allowable Values"] = (prev_allow + " " + allow_vals).strip() if prev_allow else allow_vals
                    if i == len(rows)-1:
                        merged_rows.append(prev_row)
            else:
                # If no previous row exists, simply add the row.
                #merged_rows.append(row)
                if i == len(rows)-1:
                    merged_rows.append(row)
                prev_row = row
        else:
            # New field row.
            #merged_rows.append(row)
            if prev_row is not None:
                merged_rows.append(prev_row)
            if i == len(rows)-1:
                merged_rows.append(row)                
            prev_row = row
            
    return merged_rows


def extract_rules_from_table_data(table_data):
    """
    Processes table data to extract rules.
    Returns a list of dictionaries with the rule data for the following fields:
      - Field No.
      - Field Name;(Technical Field Name)
      - Description
      - Allowable Values
    """
    rules = []
    for row in table_data:
        combined_field = row.get("Field Name;(Technical Field Name)", "")
        field_name, technical_field = split_field_name(combined_field)
        rule = {
            "Field No.": row.get("Field No.", ""),
            "Field Name": field_name,
            "Technical Field Name": technical_field,
            "Description": row.get("Description", ""),
            "Allowable Values": row.get("Allowable Values", "")
        }
        rules.append(rule)
    return rules

def save_rules_to_yaml(rules, output_yaml): 
    """
    Saves the list of rules to a YAML file under the key "rules".
    """
    data = {"rules": rules}
    with open(output_yaml, "w") as outfile:
        yaml.dump(data, outfile, sort_keys=False, default_flow_style=False)
    print(f"\nRules have been saved to {output_yaml}")

# ---------------- Main Workflow ----------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rules_pdf", required=True, help="Path to the validation results CSV file")
    args = parser.parse_args()
    pdf_path = args.rules_pdf
    #pdf_path = "C://Narasimha//Personal//Hackathon//DownloadAttachment.pdf"  # Update with your PDF file path.
    output_yaml = "rules.yaml"             # Output YAML file path.
    #output_yaml = "C://Narasimha//Personal//Hackathon//rules.yaml"             # Output YAML file path.
    
    # 1. Extract table data from the PDF.
    table_data = extract_table_from_pdf(pdf_path)
    if not table_data:
        print("No table data extracted from the PDF.")
    else:
        # 2. Process the table data to extract rules.
        table_data_merge = merge_continuation_rows(table_data)
        rules = extract_rules_from_table_data(table_data_merge)
        
        # Debug: Print each extracted rule dictionary.
        #print("\nExtracted Rules:")
        #for rule in rules:
            #print(rule)
        
        # 3. Save the rules to a YAML file.
        save_rules_to_yaml(rules, output_yaml)
        
        # save the rules to csv file
        df = pd.DataFrame(rules)
        df.to_csv("C://Narasimha//Personal//Hackathon//ScheduleH_Data_format_final.csv", index=False)