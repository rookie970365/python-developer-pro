# Scoring API

Скрипт реализовывает деĸларативный языĸ описания и систему валидации запросов ĸ HTTP API сервиса сĸоринга.
Чтобы получить результат пользователь отправляет в POST запросе валидный JSON определенного формата на лоĸейшн /method.

**Струĸтура запроса**

{"account": "<имя компании партнера>", "login": "<имя пользователя>", "method": "<имя метода>", "token": "
<аутентификационный токен>", "arguments": {<словарь с аргументами вызываемого метода>}}


**Струĸтура ответа**

OK:

*{"code": <числовой код>, "response": {<ответ вызываемого метода>}}*

Ошибĸа:

*{"code": <числовой код>, "error": {<сообщение об ошибке>}*

# Методы
**Online_score**

*Аргументы:*
phone, email, first_name, last_name, birthday, gender 

**Пример запроса**

$ curl -X POST -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "h&f", "method":"online_score", 
"token": "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95", 
"arguments": {"phone": "79175002040", "email": "stupnikov@otus.ru", "first_name": "Стансилав", "last_name": "Ступников", 
"birthday": "01.01.1990", "gender": 1}}' http://127.0.0.1:8080/method/

*{{"response": {"score": 5.0}, "code": 200}*

**Сlients_interests**

*Аргументы:* client_ids, date

**Пример запроса**

$ curl -X POST -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "admin", "method": "clients_interests", 
"token": "16f46f4c60476c7832a54e869029f6f11d1d637f5500634793d9f2ed3cddd79a3deaf821e8ae240b8953e42a7f74910b4d1c9331889442512136422a6bd51fac", 
"arguments": {"client_ids": [1,2,3,4], "date": "20.07.2017"}}' http://127.0.0.1:8080/method/

*{"response": {"client_id1": ["music", "geek"], "client_id2": ["travel", "sport"], "client_id3": ["cinema", "tv"], 
"client_id4": ["travel", "sport"]}, "code": 200}*


# Запуск
python api.py 

*Опции*

[-p|--port PORT]

PORT - номер порта для работы сервера (по умолчанию 8080)

[-l|--log LOGPATH]

LOGPATH - путь до логфайла (по умолчанию логирование производится в stdout) 