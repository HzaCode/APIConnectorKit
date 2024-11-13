import logging
import requests
import pandas as pd
from tqdm import tqdm


logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def get_code(ingredient):
    api_url = 
    payload = {
        "model_name": "XandaNER",
        "text": ingredient
    }
    try:
        response = requests.post(api_url, json=payload)
        response.raise_for_status()
        data = response.json()
        if data.get('api_status') == 'success' and len(data.get('content', [])) > 0:
            info = data['content'][0]['label']
            return {
                'code': info.get('code'),
                'type': info.get('type'),
                'XUI': info.get('XUI')
            }
    except requests.RequestException as e:
        logger.error(f"Error getting code for ingredient {ingredient}: {e}")
    return None


file_path = 
output_path = 


df = pd.read_excel(file_path)


results_df = pd.DataFrame(columns=['APID', 'Detail', 'XUI_Code', 'XUI_Type', 'XUI'])


for _, row in tqdm(df.iterrows(), desc="Extracting XUIs", total=df.shape[0]):
    apid = row['APID']
    detail = row['Detail']
    if pd.notna(detail):
        xui_info = get_code(detail)
        if xui_info:  
            results_df = results_df.append({
                'APID': apid,
                'Detail': detail,
                'XUI_Code': xui_info.get('code'),
                'XUI_Type': xui_info.get('type'),
                'XUI': xui_info.get('XUI')
            }, ignore_index=True)


results_df.to_excel(output_path, index=False)

print(f'Extracted XUIs are written to {output_path}')



# test
test_ingredient = "Amfepramone"
result = get_code(test_ingredient)

print(f"Result for '{test_ingredient}': {result}")
