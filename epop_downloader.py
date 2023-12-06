#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author: 'zfb'
# time: 2023-12-05 18:48

import argparse
import os
import requests
from multiprocessing import Pool, cpu_count, freeze_support, Manager
from tqdm import tqdm
import random
import json
from datetime import datetime, timedelta

from log import initLog

logging = initLog('download.log', __name__)

# User-Agent pool
# https://www.useragents.me/#most-common-desktop-useragents-json-csv
user_agents = json.loads(open("user_agents.json").read())

def get_pgb_pos(shared_list):
    # Acquire lock and get a progress bar slot
    for i in range(PROC_NUM):
        if shared_list[i] == 0:
            shared_list[i] = 1
            return i

def release_pgb_pos(shared_list, slot):
    shared_list[slot] = 0

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
    url, params, save_path, err_name, not_found_name, shared_list = args
    if is_file_downloaded(save_path, url, params):
        return f"Skipped: {save_path}"
    pgb_pos = get_pgb_pos(shared_list)
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
                position=pgb_pos+1,
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
    finally:
        release_pgb_pos(shared_list, pgb_pos)


def generate_dates(start_date, end_date):
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    return [(start + timedelta(days=x)).strftime("%Y-%m-%d") for x in range((end - start).days + 1)]


def main(start_date, end_date, product_name, save_folder, process_count, err_name, not_found_name, shared_list, lock):
    dates = generate_dates(start_date, end_date)
    download_args = []

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
        download_args.append((url, params, save_path, err_name, not_found_name, shared_list))

    with Pool(process_count, initializer=tqdm.set_lock, initargs=(lock,)) as pool:
        for result in tqdm(pool.imap_unordered(download_file, download_args), total=len(download_args), desc="Overall Progress", unit="file", position=0, leave=True):
            logging.info(result)


def parse_args():
    parser = argparse.ArgumentParser(description='Download ePOP data')
    parser.add_argument('-s', '--start-date', type=str, default="2020-01-01", help='start date, format: YYYY-MM-DD')
    parser.add_argument('-e', '--end-date', type=str, default="2020-12-31", help='end date, format: YYYY-MM-DD')
    parser.add_argument('-d', '--data-name', type=str, default="RRI", help='data name, options: CER GAP IRM MGF RRI FAI SEI')
    parser.add_argument('-f', '--save-folder', type=str, default="data", help='save folder, default: data')
    parser.add_argument('-p', '--parallel', type=int, default=cpu_count(), help='number of parallel processes, default: cpu_count()')
    return parser.parse_args()


args = parse_args()
PROC_NUM = args.parallel

if __name__ == '__main__':
    freeze_support()
    err_name = f"{args.start_date}_{args.end_date}_errors.txt"
    if os.path.exists(err_name):
        os.remove(err_name)
    not_found_name = f"{args.start_date}_{args.end_date}_not_found.txt"
    if os.path.exists(not_found_name):
        os.remove(not_found_name)
    # This array is shared among all PROC_NUM and allows them to keep track of which tqdm "positions" are occupied / free
    with Manager() as manager:
        lock = manager.Lock()
        shared_list = manager.list([0] * PROC_NUM)
        main(
            args.start_date, args.end_date, args.data_name, args.save_folder, PROC_NUM, 
            err_name, not_found_name, shared_list, lock
        )
