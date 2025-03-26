#TO run 
# python run_Validation.py FedR.pdf corporateloans_sample.csv vali_report.csv >> data_profiling.log

import subprocess
import sys



# Check if two arguments are provided
if len(sys.argv) != 4:
    print("Usage: python script.py <arg1> <arg2> <arg3>")
    sys.exit(1)

# Extract arguments
rules_pdf = sys.argv[1]  # First argument
data_csv = sys.argv[2]  # Second argument
report_csv = sys.argv[3]  # Third argument

# Define file paths
#yaml_file = "validation_rules.yaml"
#yaml_raw = "rules.yaml"
#validation_results = "validation_results.csv"


# Run scripts in sequence
subprocess.run(["C:\\Narasimha\\Python\\PythonEnv\\Scripts\\python.exe", "PdfToCsv_New.py", "--rules_pdf", rules_pdf])
subprocess.run(["C:\\Narasimha\\Python\\PythonEnv\\Scripts\\python.exe", "regExpollama.py"])
subprocess.run(["C:\\Narasimha\\Python\\PythonEnv\\Scripts\\python.exe", "validateDataYaml.py", "--input_csv", data_csv,"--output_csv", report_csv])

print("Pipeline execution completed.")
