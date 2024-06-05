import os
import sys
import json
import time
import logging
import argparse
import subprocess

from tqdm import tqdm
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

class Config:
    def __init__(self, input_dir, family, cpu, first_seen, size, md5):
        """
        Initialize the configuration object.

        :param input_dir: The input directory containing the JSON files.
        :param family: Flag to include family information.
        :param cpu: Flag to include CPU type information.
        :param first_seen: Flag to include first seen information.
        :param size: Flag to include file size information.
        :param md5: Flag to include MD5 hash information.
        """
        self.input_dir = input_dir
        self.output_path = os.path.join(os.path.dirname(input_dir), f"{os.path.basename(input_dir)}_report_info.csv")
        self.log_path = os.path.join(os.path.dirname(input_dir), f"{os.path.basename(input_dir)}_error.log")
        self.family = family
        self.cpu = cpu
        self.first_seen = first_seen
        self.size = size
        self.md5 = md5

class Labeler:
    def __init__(self, config: Config):
        """
        Initialize the Labeler object.

        :param config: The configuration object containing the input directory and output path.
        """
        self.config = config
        if not os.path.isdir(config.input_dir):
            print("Error: Input path must be a directory.")
            sys.exit(1)
        self.file_list = []
        self.logger = self.setup_logger()

    def setup_logger(self):
        """
        Set up the logger for error logging.

        :return: The configured logger.
        """
        logger = logging.getLogger("Labeler")
        logger.setLevel(logging.ERROR)

        handler = logging.FileHandler(self.config.log_path)
        handler.setLevel(logging.ERROR)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        return logger

    def run(self):
        """
        Run the labeling process.
        """
        self.get_all_files_in_directory()
        self.label_files()
        print(f"Output file path: {Path(self.config.output_path).resolve()}")
        print(f"Error log path: {Path(self.config.log_path).resolve()}")

    def get_all_files_in_directory(self):
        """
        Get all JSON files in the input directory and its subdirectories.
        """
        all_files = list(os.walk(self.config.input_dir))
        for root, dirs, files in all_files:
            for file in files:
                if not file.endswith(".json"):
                    continue
                file_path = os.path.join(root, file)
                self.file_list.append(file_path)

    def convert_to_one_line(self, json_file):
        """
        Convert the JSON file to a single line string.

        :param json_file: The path to the JSON file.
        :return: The single line string representation of the JSON file, or None if an error occurs.
        """
        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)
            return json.dumps(data, separators=(',', ':'))
        except json.JSONDecodeError as e:
            self.logger.error(f"Error decoding JSON file ({json_file}): {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error reading JSON file ({json_file}): {str(e)}")
            return None

    def process_json(self, json_file):
        """
        Process a single JSON file.

        :param json_file: The path to the JSON file.
        :return: A tuple containing the file name (without extension) and the extracted information.
        """
        file_name = os.path.basename(json_file)[:-5]
        family = None
        cpu = None
        first_seen = None
        size = None
        md5 = None

        try:
            with open(json_file, encoding="utf-8") as f:
                data = json.load(f)

            if self.config.family:
                one_line_data = self.convert_to_one_line(json_file)
                if one_line_data is None:
                    self.logger.error(f"Processing {json_file}")
                else:
                    with open(json_file + ".tmp", "w", encoding='utf-8') as tmp_file:
                        tmp_file.write(one_line_data)
                    command = f"avclass -f {json_file}.tmp"
                    try:
                        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
                        if result.returncode == 0:
                            family = result.stdout.split()[1]
                    except subprocess.CalledProcessError:
                        self.logger.error(f"AVClass command execution error ({json_file})")
                    except Exception:
                        self.logger.error(f"AVClass processing error ({json_file})")
                    finally:
                        os.remove(json_file + ".tmp")

            if self.config.cpu:
                try:
                    cpu = data["additional_info"]["gandelf"]["header"]["machine"]
                except KeyError:
                    pass

            if self.config.first_seen:
                try:
                    first_seen = data["first_seen"]
                except KeyError:
                    pass

            if self.config.size:
                try:
                    size = data["size"]
                except KeyError:
                    pass

            if self.config.md5:
                try:
                    md5 = data["md5"]
                except KeyError:
                    pass

        except json.JSONDecodeError:
            self.logger.error(f"Error decoding JSON file ({json_file})")
        except Exception as e:
            self.logger.error(f"Error processing JSON file ({json_file}): {str(e)}")

        return file_name, family, cpu, first_seen, size, md5

    def label_files(self):
        """
        Perform labeling on all JSON files using multi-threading.
        """
        start_time = time.time()
        
        # Create a list to store the file names and labels
        labels = []

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.process_json, json_file) for json_file in self.file_list]
            
            for future in tqdm(as_completed(futures), total=len(futures), desc="Labeling", unit="file"):
                file_name, family, cpu, first_seen, size, md5 = future.result()
                labels.append((file_name, family, cpu, first_seen, size, md5))

        # Sort the labels list based on the file name
        labels.sort(key=lambda x: x[0])

        # Write the header based on the requested fields
        header = ["file_name"]
        if self.config.family:
            header.append("family")
        if self.config.cpu:
            header.append("CPU")
        if self.config.first_seen:
            header.append("first_seen")
        if self.config.size:
            header.append("size")
        if self.config.md5:
            header.append("md5")

        with open(self.config.output_path, encoding="utf-8", mode='w') as f:
            f.write(",".join(header) + "\n")
            for label in labels:
                row = [label[0]]
                if self.config.family:
                    row.append(label[1] or '')
                if self.config.cpu:
                    row.append(label[2] or '')
                if self.config.first_seen:
                    row.append(label[3] or '')
                if self.config.size:
                    row.append(str(label[4]) if label[4] is not None else '')
                if self.config.md5:
                    row.append(label[5] or '')
                f.write(",".join(row) + "\n")

        end_time = time.time()
        execution_time = end_time - start_time
        print(f"Execution Time: {execution_time:.2f} seconds")

def parse_arguments():
    """
    Parse command-line arguments.

    :return: The parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Labeling Tool")
    parser.add_argument("--input_folder", "-i", required=True, help="Input dataset report folder")
    parser.add_argument("--family", "-f", action="store_true", help="Include family information")
    parser.add_argument("--cpu", "-c", action="store_true", help="Include CPU type information")
    parser.add_argument("--first_seen", "-s", action="store_true", help="Include first seen information")
    parser.add_argument("--size", "-z", action="store_true", help="Include file size information")
    parser.add_argument("--md5", "-m", action="store_true", help="Include MD5 hash information")
    return parser.parse_args()

def main():
    """
    The main function to run the labeling process.
    """
    args = parse_arguments()
    
    config = Config(args.input_folder, args.family, args.cpu, args.first_seen, args.size, args.md5)
    
    labeler = Labeler(config)
    labeler.run()

if __name__ == "__main__":
    main()