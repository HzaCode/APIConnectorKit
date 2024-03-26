import requests
import pandas as pd
import webbrowser
import pubchempy as pcp

def fetch_cid(apid):
    api_endpoint = "url"
    try:
        response = requests.get(api_endpoint, params={'APID': apid})
        response.raise_for_status()
        drug_details = response.json().get('content', None)
        if drug_details and 'CID' in drug_details:
            return drug_details['CID']
        return None
    except requests.RequestException as e:
        print(f"Failed to fetch CID for APID: {apid} due to: {e}")
        return None

def fetch_iupac_name(cid):
    try:
        compound = pcp.Compound.from_cid(cid)
        return compound.iupac_name
    except Exception as e:
        print(f"Failed to fetch IUPAC name for CID: {cid} due to: {e}")
        return 'Not found'

def manual_entry(cid, details):
    webbrowser.open(f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}")
    if details['CAS'] == 'Manual Entry Required':
        details['CAS'] = input("Please manually enter the CAS number: ")
    if details['UNII'] == 'Manual Entry Required':
        details['UNII'] = input("Please manually enter the UNII: ")
    if details['IUPAC_name'] == 'Manual Entry Required':
        details['IUPAC_name'] = input("Please manually enter the IUPAC Name: ")
    return details

def save_api_info(apid, cas, unii, iupac_name):
    url = "url"
    data = {
        "APID": apid,
        "CAS_No": cas,
        "UNII": unii,
        "IUPAC_name": iupac_name
    }
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"APID: {apid} successfully saved to server.")
        else:
            print(f"APID: {apid} failed to save to server. Server response: {response.status_code}")
    except requests.RequestException as e:
        print(f"APID: {apid} error: {e}")

def main():
    apid_df = pd.read_excel('Missing value.xlsx', usecols=['APID'])
    results_list = []

    print("Fetching details for APIDs...")
    for i, row in apid_df.iterrows():
        apid = row['APID']
        cid = fetch_cid(apid)
        if cid:
            iupac_name = fetch_iupac_name(cid)
            details = {
                'CAS': 'Manual Entry Required', 
                'UNII': 'Manual Entry Required', 
                'IUPAC_name': iupac_name if iupac_name != 'Not found' else 'Manual Entry Required'
            }

            details = manual_entry(cid, details)
            
            details['APID'] = apid
            details['CID'] = cid
            results_list.append(details)
            save_api_info(apid, details['CAS'], details['UNII'], details['IUPAC_name'])

    if results_list:
        print("\nAll APIDs processed successfully.")
        print("Summary of results:")
        for item in results_list:
            print(item)
    else:
        print("\nNo data found for any APID.")

if __name__ == "__main__":
    main()
