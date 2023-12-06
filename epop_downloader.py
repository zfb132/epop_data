#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: 'zfb'
# time: 2023-12-05 18:48

import argparse
import os
import requests
from multiprocessing import Pool, cpu_count, freeze_support
from tqdm import tqdm
import random
import json
from datetime import datetime, timedelta

from log import initLog

logging = initLog('reserve.log','download')

# User-Agent pool
# https://www.useragents.me/#most-common-desktop-useragents-json-csv
user_agents = json.loads(open("user_agents.json").read())

def set_headers():
    return {
        "Connection": "keep-alive",
        "Origin": "https://epop-data.phys.ucalgary.ca",
        "Referer": "https://epop-data.phys.ucalgary.ca/",
        "User-Agent": random.choice(user_agents)['ua']
    }

def is_file_downloaded(save_path, url, params):
    if os.path.exists(save_path):
        local_file_size = os.path.getsize(save_path)
        response = requests.head(url, params=params, headers=set_headers())
        server_file_size = int(response.headers.get('content-length', 0))
        return local_file_size == server_file_size
    return False

def download_file(args):
    url, params, save_path, task_id, err_name, not_found_name = args
    if is_file_downloaded(save_path, url, params):
        return f"Skipped: {save_path}"

    try:
        with requests.post(url, params=params, headers=set_headers(), stream=True) as response:
            if response.status_code == 404:
                with open(not_found_name, "a") as not_found_file:
                    not_found_file.write(f"{url}\n")
                return f"Not found: {url}"

            response.raise_for_status()
            # 1MB
            chunk_size = 1024 * 1024
            with open(save_path, 'wb') as f, tqdm(
                desc=f"Downloading {os.path.basename(save_path)}", 
                total=int(response.headers.get('content-length', 0))/ (1024 * 1024), 
                unit='MB', 
                unit_scale=True, 
                unit_divisor=1024 * 1024,
                position=task_id,
                leave=False
            ) as bar:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    f.write(chunk)
                    bar.update(len(chunk) / (1024 * 1024))
        return f"Downloaded: {save_path}"
    except Exception as e:
        with open(err_name, "a") as error_file:
            error_file.write(f"{url} - {e}\n")
        return f"Error: {save_path}"


def generate_dates(start_date, end_date):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    return [(start + timedelta(days=x)).strftime("%Y-%m-%d") for x in range((end - start).days + 1)]


def main(start_date, end_date, product_name, save_folder, process_count, err_name, not_found_name):
    dates = generate_dates(start_date, end_date)
    download_args = []

    index = 0
    for date in dates:
        year, month, day = date.split('-')
        base_href = f"/{year}/{month}/{day}/{product_name}/"
        url = f"https://epop-data.phys.ucalgary.ca{base_href}?"
        params = {
            "action": "download",
            "as": f"{product_name}.tar",
            "type": "php-tar",
            "baseHref": base_href,
            "hrefs": ""
        }
        year_folder = os.path.join(save_folder, year)
        os.makedirs(year_folder, exist_ok=True)
        save_path = os.path.join(year_folder, f"{date}-{product_name}.tar")
        download_args.append((url, params, save_path, (index%process_count)+1, err_name, not_found_name))
        index += 1

    with Pool(process_count) as pool:
        for result in tqdm(pool.imap_unordered(download_file, download_args), total=len(download_args), desc="Overall Progress", unit="file", position=0, leave=False):
            logging.info(result)


def parse_args():
    parser = argparse.ArgumentParser(description='Download ePOP data')
    parser.add_argument('-s', '--start-date', type=str, default="2020-01-01", help='start date, format: YYYY-MM-DD')
    parser.add_argument('-e', '--end-date', type=str, default="2020-12-31", help='end date, format: YYYY-MM-DD')
    parser.add_argument('-d', '--data-name', type=str, default="RRI", help='data name, options: CER GAP IRM MGF RRI FAI SEI')
    parser.add_argument('-f', '--save-folder', type=str, default="data", help='save folder, default: data')
    parser.add_argument('-p', '--parallel', type=int, default=cpu_count(), help='number of parallel processes')
    return parser.parse_args()


if __name__ == '__main__':
    freeze_support()
    args = parse_args()
    err_name = f"{args.start_date}_{args.end_date}_errors.txt"
    if os.path.exists(err_name):
        os.remove(err_name)
    not_found_name = f"{args.start_date}_{args.end_date}_not_found.txt"
    if os.path.exists(not_found_name):
        os.remove(not_found_name)
    main(
        args.start_date, args.end_date, args.data_name, args.save_folder, args.parallel, 
        err_name, not_found_name
    )
