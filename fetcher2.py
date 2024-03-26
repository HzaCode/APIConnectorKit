import concurrent.futures
import logging
import csv
from datetime import datetime
import requests

logging.basicConfig(filename='drug_details.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_drug_details(apid, field_names):
    api_endpoint = 
    results = []
    try:
        response = requests.get(api_endpoint, params={'APID': apid}, timeout=10)
        response.raise_for_status()
        drug_details = response.json().get('content', None)
        
     
        if drug_details and 'ingredient' in drug_details and drug_details['ingredient']:
            for field_name in field_names:
                value = drug_details.get(field_name, "Not Found")
                results.append((apid, field_name, value))
        else:
            logging.info(f"Skipping APID: {apid} due to missing or empty 'ingredient'")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching details for APID: {apid} - {e}")
       
        for field_name in field_names:
            results.append((apid, field_name, "Error"))
    
    return results

def save_to_csv(data, filename='drug_details.csv'):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['APID', 'Field', 'Detail'])
        writer.writerows(data)

def main(total_apids, field_names):
    start_time = datetime.now()
    print("Fetching drug details...")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        
        future_tasks = {executor.submit(fetch_drug_details, f"A{str(i).zfill(5)}", field_names)
                        for i in range(1, total_apids + 1)}
      
        for future in concurrent.futures.as_completed(future_tasks):
            try:
                result = future.result()
                results.extend(result)  
                for r in result:
                    print(f"Fetched: {r[0]}, {r[1]}")
            except Exception as exc:
                logging.error(f"Generated an exception: {exc}")
    save_to_csv(results)
    print(f"Completed in {datetime.now() - start_time}. Details saved to drug_details1001.csv.")

if __name__ == "__main__":
    total_apids = 999  
    field_names = ['ingredient', 'CID', 'CAS_No', 'UNII', 'IUPAC_name',
                   'molecular_formula', 'molecular_weight', 'smiles']
    main(total_apids, field_names)
