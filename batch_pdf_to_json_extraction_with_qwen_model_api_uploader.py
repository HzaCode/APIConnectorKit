import requests
from openai import OpenAI
from datetime import datetime
import os
import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

# Configuration
LOCAL_PDF_DIR = "./extracted_pde_docs"
OUTPUT_DIR = "./extracted_pde_results"
API_KEY = ""
API_URL = ""

# Init directories
os.makedirs(OUTPUT_DIR, exist_ok=True)
client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

class ProcessingError(Exception):
    """Custom exception for processing errors"""
    pass

def get_pdf_files() -> List[str]:
    # Get all PDF files in the directory
    if not os.path.exists(LOCAL_PDF_DIR):
        raise ProcessingError(f"Directory not found: {LOCAL_PDF_DIR}")
    
    pdf_files = [f for f in os.listdir(LOCAL_PDF_DIR) if f.endswith('.pdf')]
    if not pdf_files:
        raise ProcessingError(f"No PDF files found in {LOCAL_PDF_DIR}")
    
    return pdf_files

def process_pdf_files():
    # Start processing all PDFs
    print(f"\nStart processing PDFs - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        pdf_files = get_pdf_files()
        print(f"Found {len(pdf_files)} PDF files to process")
        
        results = []
        for pdf_file in pdf_files:
            try:
                # Process each PDF, track result
                result = process_single_file(pdf_file)
                results.append({
                    "file": pdf_file,
                    "status": "success" if result else "failed"
                })
            except Exception as e:
                # Record error if something goes wrong
                results.append({
                    "file": pdf_file,
                    "status": "failed",
                    "error": str(e)
                })
        
        # Print summary of results
        print("\nSummary of processing results:")
        success_count = sum(1 for r in results if r["status"] == "success")
        print(f"Total files: {len(results)}")
        print(f"Successfully processed: {success_count}")
        print(f"Failed to process: {len(results) - success_count}")
        
        if len(results) - success_count > 0:
            print("\nFailed files:")
            for r in results:
                if r["status"] == "failed":
                    print(f"File: {r['file']}")
                    if "error" in r:
                        print(f"Error: {r['error']}")
                    print("-" * 30)
    
    except Exception as e:
        # General error handling for bulk processing
        print(f"Error during batch processing: {str(e)}")
    
    print(f"\nFinished processing - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def process_single_file(pdf_file: str) -> bool:
    # Process a single PDF file
    local_file_path = os.path.join(LOCAL_PDF_DIR, pdf_file)
    print(f"\nProcessing file: {pdf_file}")

    try:
        # Extract drug name and ID from filename
        drug_name, apid = extract_info_from_filename(pdf_file)
        
      
        file_id = upload_to_openai(local_file_path)
        if not file_id:
            raise ProcessingError("Failed to upload PDF ")
        
       
        extracted_data = extract_sections(file_id, apid, drug_name)
        if not extracted_data:
            raise ProcessingError("Failed to extract sections")
        
        # Save result as JSON
        output_filename = os.path.join(OUTPUT_DIR, f"{apid}_extracted.json")
        save_extracted_content(extracted_data, output_filename)
        
        return True
    
    except Exception as e:
        # Handle errors for each PDF
        print(f"Error processing file {pdf_file}: {str(e)}")
        return False

def upload_all_json_files():
    # Upload all JSON files to the API
    print(f"\nStart uploading JSON files - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        json_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('_extracted.json')]
        print(f"Found {len(json_files)} JSON files to upload")
        
        upload_results = []
        for json_file in json_files:
            try:
                # Upload each JSON, track result
                file_path = os.path.join(OUTPUT_DIR, json_file)
                result = upload_extracted_data(file_path)
                upload_results.append({
                    "file": json_file,
                    "status": "success" if result else "failed"
                })
            except Exception as e:
                # Record error if something goes wrong
                upload_results.append({
                    "file": json_file,
                    "status": "failed",
                    "error": str(e)
                })
            
            # Avoid API rate limit
            time.sleep(1)
        
        # Print summary of upload results
        print("\nSummary of upload results:")
        success_count = sum(1 for r in upload_results if r["status"] == "success")
        print(f"Total files: {len(upload_results)}")
        print(f"Successfully uploaded: {success_count}")
        print(f"Failed to upload: {len(upload_results) - success_count}")
        
        if len(upload_results) - success_count > 0:
            print("\nFailed files:")
            for r in upload_results:
                if r["status"] == "failed":
                    print(f"File: {r['file']}")
                    if "error" in r:
                        print(f"Error: {r['error']}")
                    print("-" * 30)
    
    except Exception as e:
        # General error handling for batch upload
        print(f"Error during batch upload: {str(e)}")
    
    print(f"\nFinished uploading - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def extract_info_from_filename(filename: str) -> tuple[str, str]:
    # Extract drug name and ID from filename
    base_name = os.path.splitext(filename)[0]
    try:
        drug_name, apid = base_name.split("_")
        return drug_name, apid
    except ValueError:
        raise ProcessingError(f"Invalid filename format: {filename}")

def upload_to_openai(file_path: str) -> Optional[str]:
 
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.suffix.lower() == '.pdf':
            raise ValueError(f"File must be PDF: {file_path}")
        
        with open(file_path, "rb") as file:
            file_object = client.files.create(
                file=file,
                purpose="file-extract"
            )
        
        print(f"Uploaded file. File ID: {file_object.id}")
        return file_object.id
    
    except Exception as e:
        print(f"Error uploading: {str(e)}")
        return None

def extract_sections(file_id: str, apid: str, drug_name: str) -> Optional[dict]:
    # Extract specific sections from the PDF
    prompt =f'''Extract sections from PDE report.
Required sections to extract (exactly as they appear in the document):


For each section:

Section name mapping:
{{

}}

Output format (JSON):
{{
    "section_name": {{
        "APID": "{apid}",
        "drug_name": "{drug_name}",
        "section_name": "mapped_name",
        "content": "extracted_content",
        "references": [ref_numbers]  
    }}
}}
'''
    try:
        messages = [
            {'role': 'system', 'content': ''},
            {'role': 'system', 'content': f'fileid://{file_id}'},
            {'role': 'user', 'content': prompt}
        ]
        
        completion = client.chat.completions.create(
            model="qwen-long",
            messages=messages,
            stream=False
        )
        
        if hasattr(completion, 'choices') and len(completion.choices) > 0:
            content = completion.choices[0].message.content.strip()
            
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            try:
                return json.loads(content.strip())
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {str(e)}")
                print("Response content:", content)
                return None
        else:
            print("Invalid response format")
            return None
            
    except Exception as e:
        print(f"Extract error: {str(e)}")
        return None

def save_extracted_content(content: dict, output_filename: str) -> None:
    # Save extracted data to JSON
    try:
        os.makedirs(os.path.dirname(output_filename), exist_ok=True)
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        print(f"Saved extracted content to {output_filename}")
    except Exception as e:
        print(f"Error saving extracted content: {str(e)}")

def post_section(apid: str, drug_name: str, section_name: str, 
                content: str, references: List[str]) -> Dict[str, Any]:
    # Send extracted section to the API
    payload = {
        "APID": apid,
        "drug_name": drug_name,
        "section_name": section_name,
        "content": content,
        "references": references
    }
    
    result = {
        "section_name": section_name,
        "status": "failed",
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "details": ""
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        result["status_code"] = response.status_code
        
        if response.status_code == 200:
            result["status"] = "success"
            result["details"] = response.text
        else:
            result["details"] = f"Error: HTTP {response.status_code} - {response.text}"
            
    except Exception as e:
        result["details"] = f"Exception occurred: {str(e)}"
    
    return result

def upload_extracted_data(json_file_path: str) -> bool:
    # Upload JSON to the API
    print(f"\nUploading {json_file_path}")
    
    try:
        data = load_json_file(json_file_path)
        total_sections = len(data)
        success_count = 0
        
        print(f"File has {total_sections} sections")
        
        for section_key, section_data in data.items():
            print(f"Uploading section: {section_data['section_name']}")
            
            result = post_section(
                apid=section_data["APID"],
                drug_name=section_data["drug_name"],
                section_name=section_data["section_name"],
                content=section_data["content"],
                references=section_data["references"]
            )
            
            if result['status'] == 'success':
                success_count += 1
                print("Upload success")
            else:
                print(f"Upload failed: {result['details']}")
            
            time.sleep(0.5)  # Avoid rate limiting
        
        return success_count == total_sections
    
    except Exception as e:
        print(f"Error during upload: {str(e)}")
        return False

def load_json_file(file_path: str) -> Dict[str, Any]:
    # Load JSON file
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    # Main workflow
    print("=== Start Batch Processing ===")
    print("\n1. Process PDF files and generate JSON")
    process_pdf_files()
    
    print("\n2. Upload generated JSON files to API")
    upload_all_json_files()
    
    print("\n=== Batch Processing Finished ===")

if __name__ == "__main__":
    main()
