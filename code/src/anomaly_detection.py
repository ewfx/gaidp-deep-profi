import pandas as pd
import yaml
import re


class AnomalyDetector:
    def __init__(self, filtered_data_path, ruleset_path, output_path):
        self.filtered_data_path = filtered_data_path
        self.ruleset_path = ruleset_path
        self.output_path = output_path
        self.filtered_data = None
        self.rules_dict = None
        self.anomaly_records = []
        self.total_rows = 0

    def load_data(self):
        """Load filtered data and ruleset from files."""
        # Load the filtered data
        self.filtered_data = pd.read_csv(self.filtered_data_path)
        self.total_rows = len(self.filtered_data)

        # Load the processed ruleset YAML file
        with open(self.ruleset_path, 'r') as file:
            ruleset = yaml.safe_load(file)

        # Convert the ruleset to a dictionary for easy lookup
        self.rules_dict = {rule['Technical Field Name']: rule for rule in ruleset['rules']}

    def is_value_valid(self, value, rule):
        """Validate values based on the Allowable Values rule."""
        allowable_values = rule.get('Allowable Values', '').strip().lower()

        # Apply rule conditions based on the description
        if 'must not contain a carriage return, line feed, comma or any unprintable character' in allowable_values:
            if isinstance(value, str) and (',' in value or '\r' in value or '\n' in value):
                return False

        if 'use the 2 letter country code' in allowable_values:
            if isinstance(value, str) and not re.match(r'^[A-Z]{2}$', value):
                return False

        if 'free text' in allowable_values:
            return True  # Accept any text value

        if 'report 4 to 6 digit number' in allowable_values:
            if isinstance(value, str) and not re.match(r'^\d{4,6}$', value):
                return False

        if 'must be valid 6 digit CUSIP number' in allowable_values:
            if isinstance(value, str) and not re.match(r'^[A-Za-z0-9]{6}$', value):
                return False

        if 'must be unique within a submission and over time' in allowable_values:
            return True  # Assuming uniqueness check is handled separately

        if 'must not contain' in allowable_values:
            # General rule to avoid unprintable characters
            if isinstance(value, str) and re.search(r'[\x00-\x1F\x7F]', value):
                return False

        if 'naics' in allowable_values.lower() or 'sic' in allowable_values.lower() or 'gics' in allowable_values.lower():
            if isinstance(value, str) and not re.match(r'^\d{4,6}$', value):
                return False

        # If no specific rules matched, consider it valid
        return True

    def detect_anomalies(self):
        """Detect anomalies by validating filtered data against ruleset."""
        self.anomaly_records.clear()  # Clear previous anomaly records

        for index, row in self.filtered_data.iterrows():
            row_issues = []

            for column_name, value in row.items():
                if column_name in self.rules_dict:
                    rule = self.rules_dict[column_name]
                    if not self.is_value_valid(str(value), rule):
                        row_issues.append({
                            "Field": column_name,
                            "Value": value,
                            "Issue": "Validation failed",
                            "Description": rule['Description'],
                            "Allowable Values": rule['Allowable Values']
                        })

            if row_issues:
                self.anomaly_records.append({"Row Index": index + 1, "Issues": row_issues})

    def generate_report(self):
        """Generate validation report and save to a text file."""
        rows_with_anomalies = len(self.anomaly_records)
        total_anomalies = sum(len(row["Issues"]) for row in self.anomaly_records)
        checked_columns = list(self.rules_dict.keys())
        processed_columns = set(self.filtered_data.columns)
        missing_columns = [col for col in checked_columns if col not in processed_columns]

        with open(self.output_path, 'w') as report_file:
            # Write summary report
            report_file.write("Validation Report\n")
            report_file.write("=" * 40 + "\n")
            report_file.write(f"Total rows processed: {self.total_rows}\n")
            report_file.write(f"Rows with anomalies: {rows_with_anomalies}\n")
            report_file.write(f"Total anomalies found: {total_anomalies}\n\n")
            report_file.write("Columns checked: " + ", ".join(checked_columns) + "\n")
            report_file.write(
                "\nNote: Missing required columns that weren't checked: " + ", ".join(missing_columns) + "\n\n")
            report_file.write("Detailed Anomalies:\n\n")

            # Write detailed anomalies row-wise
            for anomaly in self.anomaly_records:
                report_file.write(f"Row {anomaly['Row Index']}:\n")
                for issue in anomaly['Issues']:
                    report_file.write(f"  Field: {issue['Field']}\n")
                    report_file.write(f"  Value: '{issue['Value']}'\n")
                    report_file.write(f"  Issue: {issue['Issue']}\n")
                    report_file.write(f"  Description: {issue['Description']}\n")
                    report_file.write(f"  Allowable Values: {issue['Allowable Values']}\n\n")

        print(f"Anomaly report successfully saved to: {self.output_path}")


def main():
    # Define file paths
    filtered_data_path = 'Filtered_Data.csv'
    ruleset_path = 'processed_ruleset.yaml'
    output_path = 'anomaly_detected.txt'

    # Create an AnomalyDetector instance
    detector = AnomalyDetector(filtered_data_path, ruleset_path, output_path)

    # Load data
    detector.load_data()

    # Detect anomalies
    detector.detect_anomalies()

    # Generate report and save it to file
    detector.generate_report()


if __name__ == "__main__":
    main()
