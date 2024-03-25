import concurrent.futures
import logging
import csv
from datetime import datetime
import requests

logging.basicConfig(filename='missing_drug_details.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_drug_detail(apid, field_name):
    api_endpoint = "url"
    try:
        response = requests.get(api_endpoint, params={'APID': apid}, timeout=10)
        response.raise_for_status()
        drug_details = response.json().get('content', None)
        if drug_details and field_name in drug_details:
            return apid, field_name, drug_details[field_name] if drug_details[field_name] not in [None, "", []] else "No Data"
        return apid, field_name, "Not Found"
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {field_name} for APID: {apid} - {e}")
        return apid, field_name, "Error"

def save_to_csv(data, filename='missing_data_drug_details.csv'):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['APID', 'Field', 'Detail'])
        writer.writerows(data)

def main(total_apids, field_names):
    start_time = datetime.now()
    total_tasks = total_apids * len(field_names)
    task_counter = 0
    missing_data_results = []

    print("Fetching drug details...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_apid_field = {executor.submit(fetch_drug_detail, f"A{str(i).zfill(5)}", field): (f"A{str(i).zfill(5)}", field)
                                for i in range(1, total_apids + 1) for field in field_names}
        
        for future in concurrent.futures.as_completed(future_to_apid_field):
            task_counter += 1
            apid, field = future_to_apid_field[future]
            try:
                apid, field, detail = future.result()
                print(f"Progress: {task_counter}/{total_tasks} tasks completed.", end='\r')
                if detail in ["No Data", "Not Found", "Error"]:
                    missing_data_results.append((apid, field, detail))
            except Exception as exc:
                logging.error(f"{apid}, {field} generated an exception: {exc}")
                missing_data_results.append((apid, field, "Error"))

    save_to_csv(missing_data_results)
    print(f"\nCompleted in {datetime.now() - start_time}. Missing data details saved to {filename}.")

if __name__ == "__main__":
    total_apids = 999
    field_names = ['ingredient', 'CID', 'CAS_No', 'UNII', 'IUPAC_name',
                   'molecular_formula', 'molecular_weight', 'smiles', 'synonyms', 'description']
    main(total_apids, field_names)
