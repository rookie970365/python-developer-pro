"""
скрипт для анализа  логов nginx
"""
import argparse
import gzip
import json
import logging
import os
import re
import sys
from collections import defaultdict
from operator import itemgetter
from statistics import median
from string import Template

logging.basicConfig(
    format='[%(asctime)s] %(levelname)s %(message)s',
    datefmt="%Y.%m.%d %H:%M:%S",
    filename=None,
    encoding='utf-8',
    level=logging.DEBUG
)

logger = logging.getLogger()

CONFIG_DIR = './config'
default_config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}


def load_config(cfg_path, default_cfg):
    """
    Читает config, если он существует, и объединяет его с default
    """

    try:
        with open(cfg_path, "r", encoding="utf-8") as file:
            return {**default_cfg, **json.load(file)}
    except IOError as error:
        logging.error("Could not read config file %s. %s", config_path, error)
        return None


def find_last_date_log(log_dir):
    """
    Ищет последний по дате log
    """

    last_date = last_log = ''
    for file in os.listdir(log_dir):
        date = re.findall(r'\d+', str(file))
        if date and date[0] > last_date:
            last_date = date[0]
            last_log = file
        else:
            continue
    if last_log:
        logger.debug("found last log: %s", last_log)
    return last_date, last_log


def check_exist_report(date_last_log, report_dir):
    """
    Проверяет создан создан отчет или нет
    """

    for file in os.listdir(report_dir):
        date = re.findall(r'\d+', str(file))
        if date and date[0] == date_last_log:
            return True
    return False


def read_lines(path):
    """
    Открывает лог и построчно читает и передает в обработку
    :param path:
    :return:
    """

    open_flag = gzip.open if path.endswith(".gz") else open
    with open_flag(path, "rt", encoding="utf-8") as lines:
        total = processed = 0
        for line in lines:
            parsed_line = process_line(line)
            total += 1
            if parsed_line:
                processed += 1
                yield parsed_line
    logger.debug("%s of %s lines processed", processed, total)


def process_line(line):
    """
    Обрабатывает строки
    """

    log_template = '$remote_addr $remote_user  $http_x_real_ip [$time_local] "$request" ' \
                   '$status $body_bytes_sent "$http_referer" "$http_user_agent" ' \
                   '"$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" $request_time'

    mask = re.sub(r'([\[\]\"{}])', r'\\\1', log_template)
    pattern = re.sub(r'\$(\w+)', r'(?P<\1>.+)', mask)
    search_matches = re.search(pattern, line)
    request_time = search_matches['request_time']
    request = search_matches['request']

    url_pattern = re.compile(r'((GET|POST) (?P<url>.+) (http/\d\.\d))', re.I)
    url_search = re.search(url_pattern, request)
    url = url_search['url'] if url_search else request
    return url, request_time


def get_report_data(file_path):
    """
    Получает данные для отчета
    """
    report_data = defaultdict(list)
    total_time = 0.0
    total_count = 1
    for url, time in read_lines(file_path):
        total_time += float(time)
        total_count += 1
        if url in report_data:
            report_data[url].append(float(time))
        else:
            report_data[url] = [float(time)]
    return total_count, total_time, report_data


def create_report(total_count, total_time, report_data):
    """
    Создает отчет
    """

    for url, time_list in report_data.items():
        time_sum = sum(time_list)
        row = {
            'url': url,
            'count': len(time_list),
            'count_perc': 100 * len(time_list) / total_count,
            'time_avg': time_sum / len(time_list),
            'time_max': max(time_list),
            'time_med': median(time_list),
            'time_perc': 100 * time_sum / total_time,
            'time_sum': time_sum,
        }
        yield row


def render_report(cfg, date, report):
    """
    Создает html страницу с отчетом
    """

    with open("./reports/report.html", "r", encoding="utf-8") as report_template:
        template = Template(report_template.read())
        sorted_report = sorted(list(report), key=itemgetter('time_sum'), reverse=True)
        result = template.safe_substitute(table_json=sorted_report[0:cfg.get("REPORT_SIZE")])
        file_path = os.path.join(cfg.get("REPORT_DIR"), f"report-{date}.html")
        with open(file_path, "w", encoding="utf-8") as report_file:
            report_file.write(result)
        logger.debug("Complete render report. Path: %s", file_path)


def main(cfg):
    """
    Основная функция
    """

    date, filename = find_last_date_log(cfg.get("LOG_DIR"))
    report_path = os.path.join(cfg.get("REPORT_DIR"), f"report-{date}.html")
    if check_exist_report(date, cfg.get("REPORT_DIR")):
        logger.error("last date log report already exists. Path: %s", report_path)
        sys.exit()
    file_path = os.path.join(cfg.get('LOG_DIR'), filename)
    total_count, total_time, report_data = get_report_data(file_path)
    report = create_report(total_count, total_time, report_data)
    render_report(cfg, date, report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="log_analyzer")
    parser.add_argument("--config", dest="config_path")
    args = parser.parse_args()
    logger.debug(args)
    config_path = os.path.join('./config', args.config_path if args.config_path else 'config.json')
    config = load_config(config_path, default_config)
    main(config)
