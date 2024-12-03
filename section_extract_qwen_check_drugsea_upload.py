import os
from pathlib import Path
import openai
import json
from typing import Optional, Dict, List, Any, Set
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.ns import qn
import re
import requests
from datetime import datetime

class PDEDocumentProcessor:
    def __init__(self, api_key: Optional[str] = None):
        # Init with API key from env or param
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("Missing API key")
        
        openai.api_key = self.api_key
        openai.api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        self.API_URL = ""

        # Map doc sections to standardized names
        self.SECTION_MAPPING = {
            "Pharmacodynamics data": "Pharmacodynamics",
            "Mechanism of Action": "Mechanism of Action",
            "ANNEXURE I: PHARMACOKINETICS": "Pharmacokinetics",
            "Indication": "Indication", 
            "HAZARDS IDENTIFIED": "Hazard Identified",
            "Acute toxicity studies": "Clinical Toxicity",
            "Repeated dose toxicity studies": "Non-Clinical Toxicity",
            "Carcinogenicity": "Non-Clinical Toxicity",
            "Reproductive and developmental studies": "Non-Clinical Toxicity",
            "Highly sensitizing potential": "Non-Clinical Toxicity",
            "IDENTIFICATION OF CRITICAL EFFECTS": "Therapeutic/Adverse Effects in Clinical Studies",
            "RATIONALE FOR NO/LOWEST OBSERVED ADVERSE EFFECT LEVEL": "Point of Departure (PoD) and Its Rationale",
            "APPLICATION OF ADJUSTMENT FACTORS": "Uncertainty Factors",
            "PDE CALCULATION": "PDE Calculation"
        }

    def convert_table_to_markdown(self, table: Table) -> str:
        # Convert docx table to md format
        rows = list(table.rows)
        if not rows:
            return ''
            
        md = []
        headers = [cell.text.strip() or " " for cell in rows[0].cells]
        md.append('| ' + ' | '.join(headers) + ' |')
        md.append('| ' + ' | '.join(['---'] * len(headers)) + ' |')
        
        for row in rows[1:]:
            cells = [cell.text.strip() for cell in row.cells]
            md.append('| ' + ' | '.join(cells) + ' |')
            
        return '\n'.join(md)

    def extract_references(self, text: str, references_set: Set[int]) -> None:
        # Get ref numbers from text (handles single, ranges)
        reference_pattern = re.compile(r'\(([\d,\s-]+)\)')
        refs_in_text = reference_pattern.findall(text)
        
        for ref_group in refs_in_text:
            ref_numbers = ref_group.split(',')
            for ref_number in ref_numbers:
                ref_number = ref_number.strip()
                if '-' in ref_number:
                    try:
                        start, end = map(int, ref_number.split('-'))
                        references_set.update(range(start, end + 1))
                    except ValueError:
                        continue
                else:
                    try:
                        references_set.add(int(ref_number))
                    except ValueError:
                        continue

    def iter_block_items(self, parent):
        # Yield paras and tables from doc
        for child in parent.element.body:
            if child.tag == qn('w:p'):
                yield Paragraph(child, parent)
            elif child.tag == qn('w:tbl'):
                yield Table(child, parent)

    def upload_file_to_qianwen(self, file_path: str) -> str:
        # Upload to Qianwen, get file ID
        try:
            with open(file_path, "rb") as file:
                file_object = openai.File.create(file=file, purpose="file-extract")
            return file_object.id
        except Exception as e:
            print(f"Upload err: {str(e)}")
            return None

    def validate_with_ai(self, sections_data: Dict[str, Dict], original_file_id: str, extracted_file_id: str) -> Dict[str, Dict]:
        # AI validate/correct sections using Qwen
        prompt = f'''







                 '''

        try:
            resp = openai.ChatCompletion.create(
                model="qwen-long",
                messages=[
                    {"role": "system", "content": ""},
                    {"role": "system", "content": f"fileid://{original_file_id}"},
                    {"role": "system", "content": f"fileid://{extracted_file_id}"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                stream=False
            )
            
            result_text = resp.choices[0].message.content.strip()
            
            # Extract JSON from resp
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                try:
                    return json.loads(result_text[json_start:json_end])
                except json.JSONDecodeError:
                    print("JSON parse err")
                    return sections_data
            
            return sections_data
            
        except Exception as e:
            print(f"AI validation err: {str(e)}")
            return sections_data

    def post_to_api(self, section_data: Dict[str, Any]) -> bool:
        # Post section to API endpoint
        try:
            resp = requests.post(self.API_URL, json=section_data)
            return resp.status_code == 200
        except Exception as e:
            print(f"API err for {section_data['section_name']}: {str(e)}")
            return False

    def process_document(self, file_path: str, output_dir: str) -> Dict[str, Dict[str, Any]]:
        # Extract & process doc sections
        filename = os.path.basename(file_path)
        filename_no_ext = os.path.splitext(filename)[0]
        
        # Get APID & drug name from filename
        match = re.match(r'(A\d+)\s+(.+?)-PDE', filename_no_ext, re.IGNORECASE)
        if not match:
            print(f"Skip {filename}: Wrong format")
            return {}

        apid = match.group(1)
        drug_name = match.group(2).strip()

        try:
            doc = Document(file_path)
            sections = {}
            current_section = None
            content_buffer = []
            references_set = set()
            
            # Extract content by sections
            for block in self.iter_block_items(doc):
                if isinstance(block, Paragraph):
                    para = block
                    heading_text = para.text.strip().lower()
                    
                    # Check if new section
                    for orig_heading, mapped_name in self.SECTION_MAPPING.items():
                        if orig_heading.lower() in heading_text:
                            # Save prev section
                            if current_section and content_buffer:
                                content = '\n'.join(content_buffer).strip()
                                if content:
                                    if current_section not in sections:
                                        sections[current_section] = {
                                            "APID": apid,
                                            "drug_name": drug_name,
                                            "section_name": current_section,
                                            "content": content,
                                            "references": sorted(list(references_set))
                                        }
                                    else:
                                        sections[current_section]["content"] += '\n' + content
                                        sections[current_section]["references"] = sorted(
                                            list(set(sections[current_section]["references"]) | references_set)
                                        )
                            
                            current_section = mapped_name
                            content_buffer = []
                            references_set = set()
                            break
                    
                    # Add to current section
                    if current_section and not any(orig_heading.lower() in heading_text 
                                                 for orig_heading in self.SECTION_MAPPING):
                        content_buffer.append(para.text)
                        self.extract_references(para.text, references_set)
                
                elif isinstance(block, Table) and current_section:
                    markdown_table = self.convert_table_to_markdown(block)
                    if markdown_table:
                        content_buffer.append(markdown_table)
                    table_text = '\n'.join([cell.text for row in block.rows for cell in row.cells])
                    self.extract_references(table_text, references_set)

            # Save last section
            if current_section and content_buffer:
                content = '\n'.join(content_buffer).strip()
                if content:
                    if current_section not in sections:
                        sections[current_section] = {
                            "APID": apid,
                            "drug_name": drug_name,
                            "section_name": current_section,
                            "content": content,
                            "references": sorted(list(references_set))
                        }
                    else:
                        sections[current_section]["content"] += '\n' + content
                        sections[current_section]["references"] = sorted(
                            list(set(sections[current_section]["references"]) | references_set)
                        )

            # Clear PDE calc refs
            if "PDE Calculation" in sections:
                sections["PDE Calculation"]["references"] = []

            # Save initial JSON
            initial_output = os.path.join(output_dir, f"{filename_no_ext}_initial.json")
            with open(initial_output, 'w', encoding='utf-8') as f:
                json.dump(sections, f, ensure_ascii=False, indent=2)

            # Upload docs for validation
            original_file_id = self.upload_file_to_qianwen(file_path)
            if not original_file_id:
                return sections

            extracted_file_id = self.upload_file_to_qianwen(initial_output)
            if not extracted_file_id:
                return sections
            
            # AI validation
            validated_sections = self.validate_with_ai(sections, original_file_id, extracted_file_id)
            
            # Save validated JSON
            final_output = os.path.join(output_dir, f"{filename_no_ext}_validated.json")
            with open(final_output, 'w', encoding='utf-8') as f:
                json.dump(validated_sections, f, ensure_ascii=False, indent=2)
            
            # Post to API
            for section_name, section_data in validated_sections.items():
                self.post_to_api(section_data)

            return validated_sections

        except Exception as e:
            print(f"Process err: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {}

    def process_folder(self, input_folder: str, output_folder: str):
        # Process all docs in folder
        os.makedirs(output_folder, exist_ok=True)
        
        for filename in os.listdir(input_folder):
            if filename.endswith('.docx'):
                file_path = os.path.join(input_folder, filename)
                self.process_document(file_path, output_folder)

def main():
    try:
        # Replace with your paths
        input_folder = "path/to/input"
        output_folder = "path/to/output"
        
        processor = PDEDocumentProcessor()
        processor.process_folder(input_folder, output_folder)
        
    except Exception as e:
        print(f"Main err: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
