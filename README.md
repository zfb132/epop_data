# ePOP Data Downloader

## Overview
This Python script is designed to automate the process of downloading data from the ePOP (Enhanced Polar Outflow Probe) database hosted by the University of Calgary. It allows users to specify a date range and data type, and then downloads the corresponding data files in parallel, handling errors and missing files gracefully.

## Features
- Download ePOP data for a specified date range and product type.
- Utilize multiple processes for faster downloading.
- Use random `User-Agent` headers to avoid being blocked by the server.
- Automatically handle and log errors and missing files.
- Customizable through command line arguments.

## Requirements
- Python 3
- `requests` library
- `tqdm` library

## Usage
Run the script from the command line, specifying the required parameters. Here's the basic usage syntax:  
`python epop_downloader.py -s <start_date> -e <end_date> -d <data_name> -f <save_folder> -p <parallel_processes>`  

### Command Line Arguments
* `-s <start_date>`: The start date of the date range to download data for. Format: `YYYY-MM-DD`.
* `-e <end_date>`: The end date of the date range to download data for. Format: `YYYY-MM-DD`.
* `-d <data_name>`: The name of the data product to download. See the [ePOP Data Products](https://epop-data.phys.ucalgary.ca/) section for a list of available products.
* `-f <save_folder>`: The folder to save the downloaded data files to. If the folder does not exist, it will be created.
* `-p <parallel_processes>`: The number of parallel processes to use for downloading. Default: number of CPU cores.

## Example
To download RRI data from January 1, 2020, to December 31, 2020, into the data folder using 8 parallel processes:  
`python epop_downloader.py -s 2020-01-01 -e 2020-12-31 -d RRI -f data -p 8`  
The output will look something like this:  
```txt
Overall Progress:   0%|                                                                          | 0/366 [00:00<?, ?file/s
Downloading 2020-01-01-RRI.tar:  19%|█████████                                          | 248/0.00k [00:43<02:11, 7.79MB/s]
Downloading 2020-01-02-RRI.tar:  21%|███████████                                          | 183/869 [00:43<01:54, 6.00MB/s]
Downloading 2020-01-03-RRI.tar:  25%|█████████████                                        | 224/903 [00:42<01:27, 7.78MB/s]
Downloading 2020-01-04-RRI.tar:  19%|█████████                                            | 185/997 [00:42<02:21, 5.75MB/s]
```

## Note
An interactive web page is available at [edex.phys.ucalgary.ca](https://edex.phys.ucalgary.ca/)

## Disclaimer
This script is provided as-is, with no warranty or guarantee of any kind. Use at your own risk. The author is not responsible for any damages or losses caused by this script.
It is the user's responsibility to ensure that they have the right to download the data they are requesting.
