# Log Analyzer


Скрипт обрабатывает последний по дате лог вида "nginx-access-ui.log-YYYYMMDD" 
в формате plain или gzip и формирует HTML-отчет со следующими параметрами для проведения первичного анализа:

**count** - сколько раз встречается URL, абсолютное значение

**count_perc** - сколько раз встречается URL, в процентнах относительно общего числа запросов

**time_avg** - средний $request_time для данного URL'а

**time_max** - максимальный $request_time для данного URL'а

**time_med** - медиана $request_time для данного URL'а

**time_perc** - суммарный $request_time для данного URL'а, в процентах относительно общего $request_time всех запросов

**time_sum** - суммарный $request_time для данного URL'а, абсолютное значение




Cемпл лога:   

*nginx-access-ui.log-20170630.gz*

Запуск:

*python3 log_analyzer.py*

*python3 log_analyzer.py --config config.json*


