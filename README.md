# Labeling Tool

## Introduction
The Labeling Tool is a Python script that allows users to extract various information from VirusTotal JSON report files, such as malware family, CPU type, first seen date, file size, and MD5 hash. It provides a flexible and customizable way to generate labeled datasets for malware analysis and research.

## Prerequisites
* Python >= 3.10
* Required packages:
  ```cmd
  pip3 install tqdm
  pip3 install avclass-malicialab
  ```

## Usage
```python
python3 label.py --input_folder <input_folder> [--family] [--cpu_type] [--first_seen] [--size] [--md5]
```
### Parameters
* `--input_folder` or `-i`: The folder path that stores the VirusTotal JSON report files. This parameter is required.
* `--family` or `-f`: Include malware family information in the output (requires [AVClass](https://github.com/malicialab/avclass.git)).
* `--cpu_type` or `-c`: Include CPU type information in the output.
* `--first_seen` or `-s`: Include first seen date information in the output.
* `--size` or `-z`: Include file size information in the output.
* `--md5` or `-m`: Include MD5 hash information in the output.

### Output
* `<input_folder>_info.csv`: This file will be generated in the same directory as the input folder. It contains the extracted information for each file in the input folder, based on the specified parameters.
* `<input_folder>_error.log`: This file will be generated in the same directory as the input folder. It contains any error messages encountered during the processing of the JSON report files.

### Example
```python
python3 label.py --input_folder ./reports/ --family --cpu_type --size
```
In this example, the script will process all the JSON report files in the `./reports/` folder, extract the malware family, CPU type, and file size information, and generate a `reports_info.csv` file in the same directory as the `./reports/` folder.

The `reports_info.csv` file will have the following format:
```
fileName,family,cpuType,size
file1,malwareFamily1,x86,100000
file2,malwareFamily2,ARM,50000
...
```
Note: If AVClass is used for malware family classification (`--family` option), the script will automatically convert the JSON report files to a single line format before processing them with AVClass. The original JSON files will not be modified.

## Error Logging
If any errors occur during the processing of the JSON report files, they will be logged in the `<input_folder>_error.log` file. Each error message includes a timestamp, the name of the logger ("Labeler"), the error level (ERROR), and a description of the error, along with the corresponding file name.

## License
This project is licensed under the MIT License.

## Acknowledgments
* AVClass - A malware labeling tool based on VirusTotal reports.
* The Labeling Tool extends the functionality of AVClass by providing additional options to extract various information from VirusTotal JSON report files, making it a versatile tool for generating labeled datasets for malware analysis and research.