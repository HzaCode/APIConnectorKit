import logging
from fetcher import main as fetcher_main
from CompoundSaver import get_compound_details, save_API_info
from checker import main as checker_main
from upload2 import main as upload2_main
from update3 import main as update3_main
from saver2 import get_compound_details as saver2_get_details, save_API_info as saver2_save_info
from fetcher2 import main as fetcher2_main

logging.basicConfig(filename='main.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    # Fetch drug details for a specified range of APIDs
    # fetcher_main(total_apids=100, field_names=['ingredient', 'CID', 'CAS_No'])
    
    # Get and save details for a specific compound
    # compound_details = get_compound_details(compound_name="Aspirin", apid="A00001")
    # save_API_info(compound_details=compound_details)
    
    # Check for missing drug details within a specified range of APIDs
    # checker_main(total_apids=500, field_names=['ingredient', 'CID'])
    
    # Upload missing drug details
    # upload2_main(missing_file="missing_drug_details.csv")
    
    # Update drug details for a specified range of APIDs
    # update3_main(total_apids=200, field_names=['description'])
    
    # Get and save details for a specific compound (alternative method)
    # compound_details = saver2_get_details(compound_name="Ibuprofen", apid="A00002")
    # saver2_save_info(compound_details=compound_details)
    
    # Fetch drug details for a specified range of APIDs (alternative method)
    # fetcher2_main(total_apids=800, field_names=['ingredient', 'CID', 'molecular_weight'])
    
    pass

if __name__ == '__main__':
    main()
