"""
Модуль тестирования
"""

import os
import unittest
import log_analyzer

config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log"
}
test_log_path = os.path.join(config.get("LOG_DIR"), "test-log-20170101")


class TestLogAnalyzer(unittest.TestCase):
    """
    Класс TestLogAnalyzer
    """

    def test_find_last_date_log(self):
        """
        Тестирование  find_last_date_log
        """
        last_date = log_analyzer.find_last_date_log(config.get("LOG_DIR"))[0]
        self.assertTrue(last_date > '20170629')
        self.assertTrue(last_date < '20170631')

    def test_read_lines(self):
        """
        Тестирование  read_lines
        """

        result = [
            ('/api/1/photogenic_banners/list/?server_name=WIN7RB1', '0.127'),
            ('/api/v2/banner/7763463', '0.151')
        ]
        for url, time in log_analyzer.read_lines(test_log_path):
            self.assertTrue((url, time) in result)

    def test_process_line(self):
        """
        Тестирование process_line
        """

        log_line1 = '1.126.153.80 -  - [29/Jun/2017:04:46:00 +0300] ' \
                    '"GET /agency/outgoings_stats/?date1=28-06-2017&' \
                    'date2=28-06-2017&date_type=day&do=1&rt=banner&' \
                    'oi=25754435&as_json=1 HTTP/1.1" 200 217 "-" "-" "-" ' \
                    '"1498700760-48424485-4709-9957635" "1835ae0f17f" 0.068'
        log_line2 = '1.202.56.176 -  - [29/Jun/2017:03:59:15 +0300] "0" ' \
                    '400 166 "-" "-" "-" "-" "-" 0.000'
        log_line3 = '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] ' \
                    '"GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" ' \
                    '"Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" ' \
                    '"1498697422-2190034393-4708-9752759" "dc7161be3" 0.390'

        self.assertEqual(
            log_analyzer.process_line(log_line1),
            (
                '/agency/outgoings_stats/?date1=28-06-2017&date2=28-06-2017&'
                'date_type=day&do=1&rt=banner&oi=25754435&as_json=1',
                '0.068'
            )
        )
        self.assertEqual(
            log_analyzer.process_line(log_line2),
            ('0', '0.000')
        )

        self.assertEqual(
            log_analyzer.process_line(log_line3),
            ('/api/v2/banner/25019354', '0.390')
        )

    def test_create_report(self):
        """
        Тестирование create_report
        """

        request_dict = {
            '/api/v2/banner/25019354': [0.39, 0.35],
            '/api/v2/banner/16852664': [0.199],
            '/api/1/photogenic_banners/list/?server_name=WIN7RB4': [0.133],
        }
        report_gen = log_analyzer.create_report(3, 1.072, request_dict)
        for i, request in enumerate(report_gen, start=1):
            if i == 1:
                self.assertEqual(
                    request,
                    {'url': '/api/v2/banner/25019354',
                     'count': 2,
                     'count_perc': 66.66666666666667,
                     'time_avg': 0.37,
                     'time_max': 0.39,
                     'time_med': 0.37,
                     'time_perc': 69.02985074626865,
                     'time_sum': 0.74,
                     }
                )
            if i == 2:
                self.assertEqual(
                    request,
                    {'url': '/api/v2/banner/16852664',
                     'count': 1,
                     'count_perc': 33.333333333333336,
                     'time_avg': 0.199,
                     'time_max': 0.199,
                     'time_med': 0.199,
                     'time_perc': 18.563432835820898,
                     'time_sum': 0.199,
                     }
                )
            if i == 3:
                self.assertEqual(
                    request,
                    {'url': '/api/1/photogenic_banners/list/?server_name=WIN7RB4',
                     'count': 1,
                     'count_perc': 33.333333333333336,
                     'time_avg': 0.133,
                     'time_max': 0.133,
                     'time_med': 0.133,
                     'time_perc': 12.406716417910447,
                     'time_sum': 0.133,
                     }
                )


if __name__ == '__main__':
    unittest.main()
