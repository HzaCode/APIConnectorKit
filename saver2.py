import requests
import webbrowser
import pubchempy as pcp

def fetch_pubchem_data(url):
    """Fetch data from PubChem given a URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error: {e}")
        return None

def get_cid_by_name(name):
    """Get the CID for a given compound name."""
    compounds = pcp.get_compounds(name, 'name')
    return compounds[0].cid if compounds else None

def get_compound_info(cid):
    """Fetch compound information including CAS, UNII, and synonyms."""
    cas, unii, synonyms = "Not found", "Not found", []
    data = fetch_pubchem_data(f'https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON')
    if data:
        for section in data.get('Record', {}).get('Sections', []):
            for subsection in section.get('Subsections', []):
                for info in subsection.get('Information', []):
                    if 'CAS' in info.get('Name', ''):
                        cas = info.get('ValueString', '')
                    elif 'UNII' in info.get('Name', ''):
                        unii = info.get('ValueString', '')
    synonyms_data = fetch_pubchem_data(f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/synonyms/JSON')
    if synonyms_data:
        synonyms = synonyms_data.get('InformationList', {}).get('Information', [{}])[0].get('Synonym', [])
    return cas, unii, synonyms

def manual_input(field_name, cid):
    """Prompt user for manual input if necessary."""
    webbrowser.open(f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}")
    return input(f"{field_name} not found. Please enter the {field_name}: ")

def get_compound_details(name, apid):
    """Gather compound details and prepare the dataset for saving."""
    cid = get_cid_by_name(name)
    if cid:
        cas, unii, synonyms = get_compound_info(cid)
        cas = manual_input("CAS number", cid) if cas == "Not found" else cas
        unii = manual_input("UNII", cid) if unii == "Not found" else unii
        compound = pcp.Compound.from_cid(cid)
        details = {
            "APID": apid,
            "ingredient": name,
            "CID": cid,
            "CAS_No": cas,
            "UNII": unii,
            "IUPAC_name": compound.iupac_name,
            "molecular_formula": compound.molecular_formula,
            "molecular_weight": compound.molecular_weight,
            "smiles": compound.isomeric_smiles,
            "Synonyms": ", ".join(synonyms),
            "description": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"
        }
        return details
    else:
        print("No compound found with the given name.")
        return None

def save_API_info(data):
    """Save the gathered information to a specified server."""
    server_url = "https://example.com/api"
    try:
        response = requests.post(server_url, json=data)
        if response.status_code == 200:
            print("Data successfully saved to server.")
        else:
            print("Failed to save data to server.")
    except requests.RequestException as e:
        print(f"Error: {e}")

# Example usage
if __name__ == "__main__":
    compound_name = "Aspirin"
    apid = "A00001"

    compound_details = get_compound_details(compound_name, apid)
    if compound_details:
        print("Compound Details Found:")
        for key, value in compound_details.items():
            print(f"{key}: {value}")
        save_API_info(compound_details)
