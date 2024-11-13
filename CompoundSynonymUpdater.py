import requests
from tqdm import tqdm
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the base URLs for API calls
# Example URL, replace with the real API URL when in use
API_DETAIL_URL = "http://example.com/api"
PUBCHEM_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/synonyms/JSON"

# Define the total number of drugs and the starting APID
TOTAL_DRUGS = 384
START_APID = 35

def fetch_cid(apid):
    try:
        response = requests.get(API_DETAIL_URL, params={'APID': apid}, timeout=10)
        response.raise_for_status()  # Raises an exception for 4xx/5xx errors
        data = response.json()
        # Check if 'content' exists and is not None
        if data.get('content') is not None:
            return data.get('content').get('CID')
        else:
            return None
    except requests.RequestException as e:
        logging.error(f"Failed to fetch CID for APID: {apid}, Error: {e}")
        return None

def get_synonyms(cid):
    try:
        url = PUBCHEM_URL.format(cid=cid)
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("InformationList", {}).get("Information", [{}])[0].get("Synonym", [])
    except requests.RequestException as e:
        logging.error(f"Failed to fetch synonyms for CID: {cid}, Error: {e}")
        return []

def save_API_info(data):
    try:
        res = requests.post(API_DETAIL_URL, json=data, timeout=10)
        res.raise_for_status()
        logging.info(f"Server response: {res.text}")
        return True
    except requests.RequestException as e:
        logging.error(f"Error saving API info, Error: {e}")
        return False

def main():
    for i in tqdm(range(START_APID, TOTAL_DRUGS + 1), desc="Processing APIs"):
        apid = f"A{i:05}"
        cid = fetch_cid(apid)
        if cid:
            synonyms = get_synonyms(cid)
            if synonyms:
                data = {
                    "APID": apid,
                    "Synonyms": ", ".join(synonyms)
                }
                if save_API_info(data):
                    logging.info(f"Synonyms for APID {apid} successfully saved to server.")
                else:
                    logging.error(f"Failed to save synonyms for APID {apid} to server.")
            else:
                logging.info(f"No synonyms found for APID {apid}.")
        else:
            logging.info(f"CID not found or APID {apid} does not exist, skipping.")
            continue  # Skip the current loop iteration if CID is not found
        time.sleep(1)  # Add a delay to respect API rate limits

# Furthermore, if you're interested in extracting other fields, simply follow the same path to access those fields.
# For example, if you want to get 'ingredient' or 'CAS_No', just replace data.get('content').get('CID')
# with data.get('content').get('ingredient') or data.get('content').get('CAS_No').

if __name__ == "__main__":
    main()

