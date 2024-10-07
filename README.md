# parse_jira_logged_time

Графическое приложения для просмотра залогированных задач.
Использует RSS Jira для получения информации.

Разработано на python и использует Qt 5.

Перед работой нужно будет:
  * Иметь PEM файл, содержащий сертификат. Получить можно, например:
    ```
    openssl pkcs12 -nodes -out cert.pem -in ipetrash.p12
    ```
  * Настроить [config.py](config.py). Поля:
    * **username** - ник, по которому, идет запрос информации
    * **max_results** - количество записей по активности
    * **jira_host** - хост
    * **name_cert** - имя файла или путь к файлу с сертификатом 

Для запуска:
  * Нужен python (проверялось на 3.10-3.12 версиях)
  * Установить в него зависимости [requirements.txt](requirements.txt) вручную (например, `pip install requests==2.32.2`) или все зависимости через команду:
    ```
    pip install -r requirements.txt
    ```
    Для установки в конкретную версию:
    ```
    <путь до приложения python> -m pip install -r requirements.txt
    ```
	Если при установке возникает сетевая ошибка, то можно к команде `pip` добавить прокси:
	```
	pip install --proxy http://proxy.compassplus.ru:3128 -r requirements.txt
	```
  * Запуск:
    ```
    python gui.py

[Исходники на Github](https://github.com/gil9red/parse_jira_logged_time)


### Ответственные лица ###
Илья Петраш (i.petrash@compassplus.com)
