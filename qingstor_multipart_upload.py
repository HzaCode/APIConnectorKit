import os
import math
import logging
from urllib.parse import quote_plus
from qingstor.sdk.service.qingstor import QingStor
from qingstor.sdk.config import Config
from tqdm import tqdm


class Qingstor:

    def __init__(self, options={}):
        options_default = {
            'bucket_name': '',
            'zone_name': '',
        }
        options_default.update(options)
        self.bucket_name = options_default.get('bucket_name')
        self.zone_name = options_default.get('zone_name')

        access_key = '<access_key>'
        secret_key = '<secret_key>'

        config = Config(access_key, secret_key)
        config.protocol = 'https'
        config.port = 443
        config.connection_retries = 3

        service = QingStor(config)
        self.bucket = service.Bucket(self.bucket_name, self.zone_name)

    def initiate_multipart_upload(self, object_key):
        """
        Start multipart upload, return upload ID
        """
        response = self.bucket.initiate_multipart_upload(object_key)
        if response.status_code in (200, 201):
            return response['upload_id']
        else:
            logging.error(f"Failed to initiate multipart upload for {object_key}. Status: {response.status_code}")
            return None

    def upload_part(self, object_key, upload_id, part_number, chunk):
        """
        Upload a specific part of the file.
        """
        response = self.bucket.upload_multipart(
            object_key,
            upload_id=upload_id,
            part_number=str(part_number),
            body=chunk
        )
        if response.status_code == 201:
            logging.info(f"Uploaded part {part_number} of {object_key} {response.headers['etag']}")
            return response.headers['etag'].strip('"')
        else:
            logging.error(f"Failed to upload part {part_number} of {object_key}. Status: {response.status_code}")
            return None

    def complete_multipart_upload(self, object_key, upload_id, etags):
        """
        Complete multipart upload by providing ETags
        """
        parts = [{'part_number': i + 1, 'etag': etag} for i, etag in enumerate(etags)]
        response = self.bucket.complete_multipart_upload(object_key, upload_id, object_parts=parts)
        if response.status_code == 201:
            logging.info(f"Multipart upload for {object_key} completed successfully.")
            return True
        else:
            logging.error(f"Failed to complete multipart upload for {object_key}. Status: {response.status_code}")
            return False

    def multipart_upload(self, object_key, filepath):
        """
        Perform multipart upload of the file
        """
        # Start multipart upload
        upload_id = self.initiate_multipart_upload(object_key)

        logging.info("upload_id: {}".format(upload_id))
        if not upload_id:
            return None

        etags = []

        file_size = os.stat(filepath).st_size
        chunk_size = 5 * 1024 * 1024  # Each part is 5MB
        parts_count = math.ceil(file_size / chunk_size)

        with open(filepath, 'rb') as f, tqdm(total=file_size, unit='B', unit_scale=True, desc=object_key) as pbar:
            for part_number in range(1, parts_count + 1):
                part_size = min(chunk_size, file_size - (part_number - 1) * chunk_size)
                chunk = f.read(part_size)

                # Check if the chunk is empty
              
          
                # When splitting a file into multiple parts, it's possible that the file size is exactly a multiple
                # of the chunk size. In this scenario, after reading all the parts, we may reach a final iteration
                # where the code attempts to read another chunk but there is nothing left to read.
                # This results in an empty chunk (zero bytes). QingStor does not allow empty parts in a multipart
                # upload because an empty part does not contribute to the actual content of the object and will
                # cause the API to return an error.
                # 
                # To avoid this issue, we check if the chunk is empty and break out of the loop if it is.
                # This way, only meaningful data parts are uploaded, ensuring a successful multipart upload.
                if not chunk:  # Skip if chunk is empty
                    break

                etag = self.upload_part(object_key, upload_id, part_number, chunk)
                if not etag:
                    raise Exception(f"Failed to upload part {part_number}")
                etags.append(etag)
                pbar.update(part_size)

        # Complete the multipart upload
        return self.complete_multipart_upload(object_key, upload_id, etags)

# Test code
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    qingstor = Qingstor({
        'bucket_name': '',
        'zone_name': ''
    })

    # Test file upload
    object_key = "demo/demo.pdf"
    local_file_path = r"<your_local_file_path>"

    if os.path.exists(local_file_path):
        success = qingstor.multipart_upload(object_key, local_file_path)
        if success:
            print(f"File {local_file_path} uploaded successfully to {object_key}.")
        else:
            print(f"Failed to upload file {local_file_path}.")
    else:
        print(f"File {local_file_path} does not exist. Check the file path.")
