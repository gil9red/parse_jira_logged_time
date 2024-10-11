# parse_jira_logged_time

Графическое приложения для просмотра залогированных задач.
Использует RSS Jira для получения информации.

Разработано на python и использует Qt 5.

Перед работой нужно будет:
  * Иметь PEM файл, содержащий сертификат. Получить можно, например:
    ```
    openssl pkcs12 -nodes -out cert.pem -in ipetrash.p12
    ```
  * Настроить [config.json](etc/examples/config.json) (пример см. в etc/examples/config.json).
    * Если, при импорте/запуске config.py, config.json не будет в корне папки, то он будет скопирован из etc/examples/config.json
    * Поля:
  
    | Поле            | Описание                                                                                                          |
    |-----------------|-------------------------------------------------------------------------------------------------------------------|
    | **username**    | Ник, по которому, идет запрос информации.<br/>Если не задано, то будет получено из текущего пользователя в джире. |
    | **max_results** | Количество записей по активности                                                                                  |
    | **jira_host**   | Хост                                                                                                              |
    | **name_cert**   | Имя файла или путь к файлу с сертификатом                                                                         |
    | **gui**         | Содержит настройки приложения                                                                                     |

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
	pip install --proxy <адрес> -r requirements.txt
	```
  * Запуск:
    ```
    python gui.py
