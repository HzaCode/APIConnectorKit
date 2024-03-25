import requests
import pandas as pd

def fetch_drug_details(apid):
   
    api_endpoint = "api_link"
    try:
        response = requests.get(api_endpoint, params={'APID': apid})
        response.raise_for_status()
        return response.json().get('content', None)
    except requests.RequestException as e:
        print(f"Failed to fetch data for APID: {apid} due to: {e}")
        return None

def main():
    excel_path = "C:/path/to/excel.xlsx"
    new_excel_path = "C:/path/to/new_excel.xlsx"
    
    df_excel = pd.read_excel(excel_path)
    matched_drugs_info = pd.DataFrame()

    total_apids = 999

    print("Fetching drug details and matching with Excel parameters...")
    for i in range(1, total_apids + 1):
        apid = f"A{str(i).zfill(5)}"
        drug_details = fetch_drug_details(apid)
        if drug_details and 'param' in drug_details:
            param = drug_details.get('param')
            matched_rows = df_excel[df_excel['parameter'].astype(str) == param].copy()
            if not matched_rows.empty:
                matched_rows['APID'] = apid
                matched_drugs_info = pd.concat([matched_drugs_info, matched_rows], ignore_index=True)
        
        print(f"Processed APID: {apid} ({i}/{total_apids})", end='\r')

    if not matched_drugs_info.empty:
        matched_drugs_info.to_excel(new_excel_path, index=False)
        print(f"\nMatched drug details saved to: {new_excel_path}")
    else:
        print("\nNo matched drugs found.")

if __name__ == "__main__":
    main()
