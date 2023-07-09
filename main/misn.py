from sqlite3 import Connection
import schedule
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import sqlite3

arr_actions = ['OZON', 'SBER', 'ROSN', 'TATN']
arr_count = [2, 20, 2, 2]
options = webdriver.ChromeOptions()
service = Service(executable_path='/Users/egorkarinkin/PycharmProjects/Birzja/main/')

# add proxy
# options.add_argument('--proxy-server=46.29.165.166:8123') - нужен нормальный прокси

"""disable webdriver mode"""
options.add_experimental_option('excludeSwitches', ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(service=service, options=options)

def get_data(arr) -> list:

    """Эта функция возвращает список из цен всех нужных нам акций"""

    res_arr = []

    try:
        for i in arr:
            driver.get(url=f'https://www.tinkoff.ru/invest/stocks/{i}/')
            driver.maximize_window()
            res_str = ''
            response = driver.find_element(By.CSS_SELECTOR,
                                           'body > div.application > div > div.PageWrapper__wrapper_pqqYo > div > div.PageContainer__wrapper__lPI0 > div > div.Row-module__row_lV3vw > div.Column-module__column_gkBDn.Column-module__column_size_4_y2_Ek > div > div > div.SecurityPriceDetails__wrapper_bDFIo.SecurityPriceDetails__wrapperBorder_so3Fu > div > div > div.SecurityInvitingScreen__price_FSP8P > span > span')

            for el in response.text.split(' '):
                if '\n' in el or '₽' in el:
                    res_str += el.split('\n')[0]
                    break
                res_str += el

            res_arr.append(int(res_str))

    except Exception as ex:
        print(ex)

    finally:
        driver.close()
        driver.quit()
    return res_arr


def one_time():

    """Эта функция создает базу данных и
     вносит туда Названия акций который находятся
      в arr_actions и вводит их актуальное значение"""

    with sqlite3.connect('statistic.db') as db:

        req = """
        CREATE TABLE IF NOT EXISTS statistics(
        security VARCHAR(4),
        value INTEGER,
        difference INTEGER
        )
        """

        db.executescript(req)
        new = []
        for g, i in enumerate(arr_actions):
            new.append((i, get_data(arr_actions)[g]))

        db.executemany("INSERT INTO statistics(security, value) VALUES(?, ?)", new)

def main():
    """
    Функция main подключается к базе данных,
    Забирает старые значения ценных бумаг,
    И обновляет их цену и разницу между
    Старой ценной и новой
    """

    db: Connection = sqlite3.connect('statistic.db')

    try:
        cursor = db.cursor()

        new_arr = get_data(arr_actions)
        cursor.execute("SELECT value FROM statistics")
        get_response = cursor.fetchall()

        for i, el in enumerate(get_response):
            multiplication = int(new_arr[i]) * arr_count[i]
            prom = int(el[0]) - multiplication
            cursor.execute("UPDATE statistics SET value = ?, difference = ? WHERE security = ?", (multiplication, prom, arr_actions[i]))

        db.commit()
        cursor.close()

    except sqlite3.Error as error:
        print("Ошибка при работе с SQLite", error)

    finally:
        db.close()
        print("Соединение с SQLite закрыто")


if __name__ == '__main__':
    main()
