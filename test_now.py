from selenium import webdriver
from bs4 import BeautifulSoup
import time
import requests
import os
import os.path
import json
from colorama import Fore, Back, Style

HEADERS = {
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.86 YaBrowser/21.3.0.740 Yowser/2.5 Safari/537.36',
    'accept': '*/*'
}

options = webdriver.ChromeOptions()
options.headless = True
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument(
    'user-agent=Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36')



def pars():
    driver = webdriver.Chrome(
        executable_path='/Users/levreyn/Yandex.Disk.localized/python/selenium/driver/chromedriver',
        options=options)
    def parse_info(url):
        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'lxml')

        # собираем основную иформаицю мотоцикле
        info_dict = {}  # здесь все данные со страницы
        product_info = soup.find('div', class_='product-info').find('ul').find_all('li')
        for li in product_info:
            index_start = str(li).find('">') + 2
            index_end = str(li).find('<span>')
            name_info = str(li)[index_start:index_end]
            try:
                info = li.find('span').text.strip()
            except:
                info = li.find('span')
            info_dict[name_info] = info

        # собираем фотографии мотоцикла
        links_photos_lst = []  # список для ссылок на фотографии
        photos = soup.find('div', class_='thumbs').find_all('li')
        for i in range(len(photos)):
            # ссылка для первой фотографии находится по одному пути
            if i == 0:
                link_photo = 'https://spb.x-m.su' + photos[i].find('img')['src']
            #  а для остальных по-другому
            else:
                link_photo = 'https://spb.x-m.su' + photos[i].find('a')['href']
            links_photos_lst.append(link_photo)
        info_dict['photos urls'] = links_photos_lst

        # собираем подробную информацию и убираем разный мусор, типо теги и всё такое4
        # start_time = time.time()
        big_information = str(soup.find('div', class_='props-col')).split('<br/>')
        big_information = [i.replace('\t', '').replace('\n', '').replace('\r', '') for i in big_information]
        big_information = [i.replace('</td>', '').replace('<td>', '').replace('<p>', '') for i in big_information]
        big_information = [i.replace('</p>', '').replace('<div class="props-col">', '') for i in big_information]
        big_information = [i.replace('<table cellpadding="0" cellspacing="0">', '') for i in big_information]
        big_information = [i.replace('<colgroup>', '').replace('<col/>', '').replace('<tr>', '') for i in big_information]
        big_information = [i.replace('<tbody>', '').replace('</colgroup>', '').replace('   ', '') for i in big_information]
        big_information = [i.replace('</tr>', '').replace('\xa0', '').replace('</div>', '') for i in big_information]
        big_information = [i.replace('</span>', '').replace('</table>', '') for i in big_information]
        big_information = [i.replace('</tbody>', '').replace('<span style="color: #ff0000;">', '') for i in big_information]

        # собираем индесы элеиентов, где просто пустые строки, что бы потом удалить
        del_index_need = []
        for i in range(len(big_information)):
            for j in range(5):
                if big_information[i] == ' ' * j:
                    del_index_need.append(i)
            if big_information[i] == '':
                del_index_need.append(i)
        del_index_need = list(set(del_index_need))
        del_index_need.reverse()
        for index in del_index_need:
            del big_information[index]  # удаляем

        # end_time = time.time()
        # print(end_time - start_time)

        info_dict['big information'] = big_information

        # цена
        price = soup.find('p', class_='price').text.strip()
        info_dict['price'] = price

        return info_dict


    try:
        if os.path.exists('data') == False:
            os.mkdir('data')
        for i in range(1, 13):
            url = f'https://spb.x-m.su/mototehnika/motocikly?PAGEN_1={i}'
            driver.get(url)
            driver.implicitly_wait(10)
            soup = BeautifulSoup(driver.page_source, 'lxml')
            items = soup.find_all('div', class_='tov first')
            count = 0
            for item in items:
                name = item.find('p', class_='name').find('a').text.strip()
                link = 'https://spb.x-m.su' + item.find('p', class_='name').find('a')['href']
                try:
                    info_dict = parse_info(link)
                    # если такой папки нет, то создаём её
                    if os.path.exists(f'data/{name.replace(" ","_").replace(".", "_")}') == False:
                        os.mkdir(f'data/{name.replace(" ","_")}')
                    # сохраняем всё в эту папку
                    with open(f'data/{name.replace(" ","_")}/{name.replace(" ","_")}.json', 'w') as file:
                        json.dump(info_dict, file, indent=4, ensure_ascii=False)
                except:
                    print(Back.RED + f'произошла ошибка с мотоциклом: {name} ссылка: {link}' + Style.RESET_ALL)
                count += 1
                print(f'собрали информацию с {count} из 15 на странице')

                # break
            print(Fore.CYAN + f'закончили с {i} страницей из 12' + Style.RESET_ALL)

            # break
    except Exception as ex:
        print(ex)

    finally:
        driver.close()
        driver.quit()

# pars()

# скачивает фотографии только если уже была запущена функция parse и ссылки сохрагнены были
def save_photos():
    lst_names_directories = os.listdir('data')
    all_count = len(lst_names_directories)
    count = 0
    for name in lst_names_directories:
        try:
            with open(f'data/{name}/{name}.json') as file:
                links = json.load(file)["photos urls"]
                # print(links)

            for i in range(len(links)):
                r = requests.get(links[i])

                with open(f'data/{name}/{i}.jpg', 'wb') as file:
                    file.write(r.content)
            count += 1
        except Exception as ex:
            print(Fore.RED + f'произошла ошибка в {name} -- {links[i]} -- вот такая: {ex}' + Style.RESET_ALL)
        print(f'скаченно {count} из {all_count} -- {name}')


save_photos()
