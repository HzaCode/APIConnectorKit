import concurrent.futures
import logging
import csv
from datetime import datetime
import requests

logging.basicConfig(filename='drug_details.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_drug_detail(apid, field_name):
    api_endpoint = "url"
    try:
        response = requests.get(api_endpoint, params={'APID': apid}, timeout=10)
        response.raise_for_status()
        drug_details = response.json().get('content', None)
        if drug_details and field_name in drug_details:
            return apid, field_name, drug_details[field_name]
        return apid, field_name, "Not Found"
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {field_name} for APID: {apid} - {e}")
        return apid, field_name, "Error"

def save_to_csv(data, filename='drug_details.csv'):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['APID', 'Field', 'Detail'])
        writer.writerows(data)

def main(total_apids, field_names):
    start_time = datetime.now()
    print("Fetching drug details...")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        
        future_tasks = [executor.submit(fetch_drug_detail, f"A{str(i).zfill(5)}", field_name)
                        for i in range(1, total_apids + 1) for field_name in field_names]
      
        for future in concurrent.futures.as_completed(future_tasks):
            try:
                result = future.result()
                results.append(result)
                print(f"Fetched: {result[0]}, {result[1]}")
            except Exception as exc:
                logging.error(f"Generated an exception: {exc}")
    save_to_csv(results)
    print(f"Completed in {datetime.now() - start_time}. Details saved to drug_details.csv.")

if __name__ == "__main__":
    total_apids = 10  
    field_names = ['ingredient', 'CID', 'CAS_No', 'UNII', 'IUPAC_name',
                   'molecular_formula', 'molecular_weight', 'smiles', 'synonyms', 'description']
    main(total_apids, field_names)
