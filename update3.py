import webbrowser
import logging
import requests
from datetime import datetime
import concurrent.futures


logging.basicConfig(filename='drug_details.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_drug_details(apid, field_names, total_apids):
    api_endpoint = "" 
    try:
        response = requests.get(api_endpoint, params={'APID': apid}, timeout=10)
        response.raise_for_status()
        drug_details = response.json().get('content', None)
        
      
        if drug_details and 'ingredient' in drug_details and drug_details['ingredient']:
            # Now, check the description field
            description = drug_details.get('description', "Not Found")
            if description in [None, "Not Found", "No description available"]:
                webbrowser.open(f"https://pubchem.ncbi.nlm.nih.gov/compound/{drug_details.get('CID', 'Not Found')}")
                webbrowser.open(f"http://link{apid}")
                input("Press Enter after you have finished reviewing the opened pages...")
        else:
            logging.info(f"Skipping APID: {apid} due to missing or empty 'ingredient'")
            return  
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching details for APID: {apid} - {e}")
    
   
    progress_update(apid, total_apids)

def progress_update(current_apid, total_apids):
    current_index = int(current_apid.replace("A", ""))  
    print(f"Progress: {current_index}/{total_apids} APIDs processed.")

def main(total_apids, field_names):
    start_time = datetime.now()
    print("Fetching drug details...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_tasks = [executor.submit(fetch_drug_details, f"A{str(i).zfill(5)}", field_names, total_apids)
                        for i in range(1, total_apids + 1)]
      
    print(f"Completed. Total APIDs processed: {total_apids}.")
    print(f"Total time taken: {datetime.now() - start_time}.")

if __name__ == "__main__":
    total_apids = 999  
    field_names = ['ingredient', 'CID', 'description']
    main(total_apids, field_names)
