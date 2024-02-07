
import requests
import webbrowser
import pcp  

# Function to get the CID (Compound Identifier) by name
def get_cid_by_name(name):
    compounds = pcp.get_compounds(name, 'name')
    if compounds:
        return compounds[0].cid
    return None

# Function to get CAS number and UNII for a given CID
def get_cas_unii(cid):
    url = f'https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/JSON'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        cas = unii = None
        for section in data.get('Record', {}).get('Sections', []):
            for subsection in section.get('Subsections', []):
                for information in subsection.get('Information', []):
                    if 'CAS' in information.get('Name', ''):
                        cas = information.get('ValueString', 'Not found')
                    if 'UNII' in information.get('Name', ''):
                        unii = information.get('ValueString', 'Not found')
        return cas, unii
    else:
        return None, None

# Function to get synonyms for a given CID
def get_synonyms(cid):
    url = f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/synonyms/JSON'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        synonyms = data.get('InformationList', {}).get('Information', [{}])[0].get('Synonym', [])
        return synonyms
    else:
        return []

# Function to get compound details and save them to a server
def get_compound_details(name, apid):
    cid = get_cid_by_name(name)
    web_page_opened = False  # Flag to track if the web page has been opened

    if cid:
        synonyms = get_synonyms(cid)  # Get synonyms
        cas_number, unii = get_cas_unii(cid)
        if not cas_number or cas_number == "Not found":
            if not web_page_opened:
                webbrowser.open(f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}")
                web_page_opened = True  # Update the flag
            cas_number = input("CAS number not found. Please enter the CAS number: ")
        if not unii or unii == "Not found":
            if not web_page_opened:
                webbrowser.open(f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}")
                web_page_opened = True  # Ensure the page is opened
            unii = input("UNII not found. Please enter the UNII: ")

        compound = pcp.Compound.from_cid(cid)
        details = {
            "APID": apid,
            "ingredient": name,
            "CID": cid,
            "CAS_No": cas_number,
            "UNII": unii,
            "IUPAC_name": compound.iupac_name,
            "molecular_formula": compound.molecular_formula,
            "molecular_weight": compound.molecular_weight,
            "smiles": compound.isomeric_smiles,
            "Synonyms": ", ".join(synonyms),  # Save all synonyms
            "description": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}"  # Link for manual description review
        }
        return details
    else:
        return None

# Function to save compound details to a server
def save_API_info(data):
    # Placeholder URL for the server API
    server_url = "https://example.com/api/save"
    try:
        res = requests.post(server_url, json=data)
        print("Server response:", res.text)
        return res.status_code == 200
    except requests.RequestException as e:
        print("Error:", e)
        return False

# Example usage
compound_name = "Aspirin"
apid = "A00001"

compound_details = get_compound_details(compound_name, apid)
if compound_details:
    print("Compound Details Found:")
    for key, value in compound_details.items():
        print(f"{key}: {value}")
    user_description = input("Please enter the description you found: ")
    compound_details["description"] = user_description if user_description else "User did not provide a description."
    if save_API_info(compound_details):
        print("Data successfully saved to server.")
    else:
        print("Failed to save data to server.")
else:
    print("No compound found with the given name.")


