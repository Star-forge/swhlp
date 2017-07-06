#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import os
import requests
import argparse
import logging
import time
import pickle

import shutil
from PIL import Image
from shutil import copyfile

try:
    print("***Чтение файла авторизации.***")
    from auth import key
    print("Успешно. Ваша кодовая фраза: '%s'" % key)
except ImportError:
    key = "unauthorized user"
    f = open('auth.py', 'w')
    f.write("key = '' \n")
    f.close()
    print("Сбой. Ваша кодовая фраза: '%s'" % key)

try:
    print("***Чтение файла конфигурации.***")
    from CONF import long_stage_timeout, boss_timeout, update, sell_all_runes, window_title, window_x_coordinate, window_y_coordinate
    print("Успешно. \n   long_stage_timeout = %d \n   boss_timeout = %d \n   update = %d \n   sell_all_runes = %d \n   window_title = %s \n   window_x_coordinate = %d \n   window_y_coordinate = %d" % (long_stage_timeout, boss_timeout, update, sell_all_runes, window_title, window_x_coordinate, window_y_coordinate))
except ImportError:
    long_stage_timeout = 15
    boss_timeout = 10
    update = 0
    sell_all_runes = 0
    window_title = 'sw_farm' 
    window_x_coordinate = 0 
    window_y_coordinate = 0
    f = open('CONF.py', 'w')
    file_content = "'''Файл конфигурации''' \n#Программа не будет отправлять данные для анализа ИИ в этот промежуток времени. \n#прохождение до Боса \nlong_stage_timeout = 15 \n#прохождение самого Боса \nboss_timeout = 10 \n \n#Обновлять приложение (1 - да, 0 - нет) \nupdate = 0 \n \n#Продажа всех рун (1 - продавать, 0 - не продавать) \nsell_all_runes = 0 \n \n# параметры окна \nwindow_title = 'sw_farm' \nwindow_x_coordinate = 0 \nwindow_y_coordinate = 0"
    f.write(file_content)
    f.close()
    print("Сбой. \n   long_stage_timeout = %d \n   boss_timeout = %d \n   update = %d \n   sell_all_runes = %d \n   window_title = %s \n   window_x_coordinate = %d \n   window_y_coordinate = %d" % (long_stage_timeout, boss_timeout, update, sell_all_runes, window_title, window_x_coordinate, window_y_coordinate))
    
view_only_mode = False

VER = 177
# URL_API = "http://192.168.169.145:30001/api/UploadFile4Recognition"
# URL_SRV = "http://217.71.231.9:30001"
URL_SRV = "http://192.168.169.145:30001"
URL_API = URL_SRV + "/api/UploadFile4Recognition"
URL_UPD = URL_SRV + "/chkver"
STAT_UPD = URL_SRV + "/stat"

IMAGE_TYPE = "screenshot"
IM_PATH = "screenshot.jpg"
supportFlag = True
uaddr = "unknown"
uname = "unknown"
img_meta = []

new_start_date = None
new_start_flag = None

logger = logging.getLogger('sw')
ch = logging.StreamHandler()
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)

class Stat(object):
    def __init__(self, run_id, name, value):
        self.run_id = run_id
        self.name = name
        self.value = value

def get_image_from_path(image_path):
    # Чтение изображения
    im = Image.open(image_path).convert("RGBA")
    return im


def upload_to_web(im_path):
    global uaddr, uname
    files = {
        'file': ('image.jpg', open(im_path, 'rb'), 'image/jpg', {'Expires': '0'})
    }
    data = {
        'user_name': uname,
        'user_addr': uaddr,
        'key': key,
        'filename': "sw_screenshot"
    }

    result = requests.put(url=URL_API, files=files, data=data)

    response = result.json()
    callback_id = response.get('callback_id', None)     # <-- это распознанный тип
    message = response.get('Message', None)             # <-- это распознанный тип

    logger.debug("Recognize: %s" % message)

    return callback_id, message


def get_im_similarity_index(screenshot, previous_screenshot):
    result = 0

    im = get_image_from_path(screenshot)
    prev_im = get_image_from_path(previous_screenshot)

    x = min(im.size[0], prev_im.size[0])
    y = min(im.size[1], prev_im.size[1])
    pixels_for_check = [[int(x/10), int(y/10)],         # 5x5%
                        [int(x-x/10), int(y-y/10)],     # -5x-5%
                        [int(x/2), int(y/2)],           # center
                        [int(x/2-x/20), int(y/2)],      # l_center
                        [int(x/2), int(y/2-y/20)],      # u_center
                        [int(x/2), int(y/2+y/20)],      # d_center
                        [int(x/2+x/20), int(y/2)]]      # r_center

    rgb_im = im.convert('RGB')
    rgb_prev_im = prev_im.convert('RGB')
    for pix in pixels_for_check:
        im_rgb = rgb_im.getpixel((pix[0], pix[1]))
        prev_im_rgb = rgb_prev_im.getpixel((pix[0], pix[1]))

        if im_rgb == prev_im_rgb:
            result += 1

    return result


def do_mouse_click(com):
    os.system("PCLinkScr.exe")
    idx = get_im_similarity_index("screenshot.jpg", "previous_screenshot.jpg")
    if idx < 3:
        logger.debug('err: image similarity index too small (lower than 3)!')
        return False
    else:
        os.system(com)
        return True


def calc_and_write_stat(run_id):
    new_value = 0
    try:
        with open('stat.pkl', 'rb') as input:
            stat_data = pickle.load(input)
            _run_id = stat_data.run_id
            _name = stat_data.name
            _value = stat_data.value

            _now = datetime.now()
            print(_value, _now, run_id, (_now - run_id).seconds, new_value)
            new_value = (_value + (datetime.now() - run_id).seconds) / 2

            with open('stat.pkl', 'wb') as output:
                stat = Stat(run_id, 'start-boss', new_value)
                pickle.dump(stat, output, pickle.HIGHEST_PROTOCOL)
            print("stat %s --> %s" % (_value, new_value))

    except IOError:
        with open('stat.pkl', 'wb') as output:
            stat = Stat(run_id, 'start-boss', new_value)
            pickle.dump(stat, output, pickle.HIGHEST_PROTOCOL)
        print("stat init %s" % new_value)

    return int(new_value)


def print_waiting(step):
    print("\r***ОЖИДАНИЕ " + str(step) + " СЕКУНД***", end="")


def run():
    global supportFlag, long_stage_timeout, new_start_date, new_start_flag
    try:
        os.remove("screenshot.jpg")
    except IOError:
        logger.debug('err: old scr not found')
    datetime_before_scrshot = datetime.now()
    os.system("PCLinkScr.exe")
    last_modify_date = datetime.fromtimestamp(os.path.getatime("screenshot.jpg"))
    while last_modify_date < datetime_before_scrshot:
        last_modify_date = datetime.fromtimestamp(os.path.getatime("screenshot.jpg"))
        time.sleep(0.5)
        print(last_modify_date, datetime_before_scrshot)

    copyfile("screenshot.jpg", "previous_screenshot.jpg")

    im = get_image_from_path("screenshot.jpg")
    im_resized = im.resize((299, 299), Image.LANCZOS)
    # im_resized.show()
    im_resized.save(IM_PATH)
    result = None
    try:
        file = open(IM_PATH)
    except IOError:
        logger.debug(u'Image not found at path: ', IM_PATH)
    else:
        with file:
                logger.debug('***ОТПРАВКА ИЗОБРАЖЕНИЯ НА СЕРВЕР***')
                callback_id, result = upload_to_web(IM_PATH)
    if result:
        logger.debug("complete")
    else:
        logger.debug("failed")
        result = "failed upload_to_web"
    
    if view_only_mode:
        return callback_id

    if not new_start_date:
        new_start_date = datetime.now()

    if result == "Error!!":
        pass
    elif result == "01start":
        new_start_date = datetime.now()
        new_start_flag = None
        os.system("PCLinkClk.exe 0 0 85 70")
    elif (result == "02boot") | (result == "03st"):
        print(long_stage_timeout, new_start_date, new_start_flag)
        if not new_start_flag:
            if long_stage_timeout > 30 :
                long_stage_timeout -= 30
            logger.debug("***ОЖИДАНИЕ %d СЕКУНД***" % long_stage_timeout)
            if long_stage_timeout > 120:
                i = long_stage_timeout / 2
                if new_start_flag == 10:
                    new_start_flag = 1
                else:
                    new_start_flag = 10

            else:
                i = long_stage_timeout
                new_start_flag = 1
            while i > 0:
                print_waiting(i)
                time.sleep(1)
                i -= 1
            print("\n")
        else:
            logger.debug("***ПОВТОРНЫЙ ЗАПРОС - ОЖИДАНИЕ %d СЕКУНД***" % 10)
            i = 10
            while i > 0:
                print_waiting(i)
                time.sleep(1)
                i -= 1
            print("\n")
        pass
    elif result == "07boss1":
        logger.debug("***ОЖИДАНИЕ %d СЕКУНД***" % boss_timeout)
        i = boss_timeout
        while i > 0:
            print_waiting(i)
            time.sleep(1)
            i -= 1
        print("\n")
        pass
    elif result == "11victory1":
        long_stage_timeout = calc_and_write_stat(new_start_date)
        os.system("PCLinkClk.exe")
        time.sleep(0.5)
        os.system("PCLinkClk.exe")
        new_start_date = None
    elif result == "11revive":
        os.system("PCLinkClk.exe 0 0 65 65")
    elif result == "12victory2":
        os.system("PCLinkClk.exe")
    elif result == "13other no rune":
        os.system("PCLinkClk.exe 0 0 50 75")
        os.system("PCLinkClk.exe 0 0 50 80")
    # elif (result == "13rune 5"):
    #     os.system("PCLinkClk.exe 0 0 37 78")
    elif (result == "13rune 6") | ("13rune" in result):
        if sell_all_runes == 1:
            logger.debug("Продажа всех рун ВКЛ")
            if not do_mouse_click("PCLinkClk.exe 0 0 37 78"):
                return callback_id
        else:
            logger.debug("Продажа всех рун НЕ вкл")
            if not do_mouse_click("PCLinkClk.exe 0 0 63 78"):
                return callback_id
    elif result == "15replay":
        os.system("PCLinkClk.exe 0 0 45 50")
        new_start_date = None
    elif result == "14sell":
        if not do_mouse_click("PCLinkClk.exe 0 0 37 60"):
            return callback_id
    elif (result == "16no energy") | (result == "18buy energy"):
        if not do_mouse_click("PCLinkClk.exe 0 0 40 60"):
            return callback_id
    elif result == "17click energy":
        if supportFlag:
            pass
            if not do_mouse_click("PCLinkClk.exe 0 0 30 50"):
                return callback_id
        else:
            if not do_mouse_click("PCLinkClk.exe 0 0 83 17"):
                return callback_id
        supportFlag = not supportFlag
    elif result == "19buy energy ok":
        if not do_mouse_click("PCLinkClk.exe 0 0 50 60"):
            return callback_id
    elif result == "20energy full":
        if not do_mouse_click("PCLinkClk.exe 0 0 83 17"):
            return callback_id

    return callback_id


def script_update(path):
    # update_script = "update.py"
    #
    # if not os._exists(update_script):
    #     r = requests.get(URL_SRV + "/static/update.py", stream=True)
    #     if r.status_code == 200:
    #         with open(update_script, 'wb') as f:
    #             for chunk in r.iter_content(1024):
    #                 f.write(chunk)
    #
    # update_path = update_script + ' --path="' + path + '/sw_clicker.py"'
    # Popen(update_path, shell=True)
    sw_path =  path + "/sw_clicker.py"
    file = requests.get(sw_path, stream=True)
    dump = file.raw
    shutil.copy2("sw_clicker.py", "old_sw_clicker.py")
    with open("sw_clicker.py", 'wb') as location:
        shutil.copyfileobj(dump, location)
    exit("exit for updating main file")


def check_new_version():
    response = requests.get(url=URL_UPD).json()
    version = response.get('version', None)
    if version:
        if (int(version) > VER):
            if update != 1:
                print("Обнаружена новая версия = %s. Текущая версия = %s. Update is off. \nYou can switch on update in 'CONF.py'." % (version, VER))
            else:
                print("Обнаружена новая версия = %s. Текущая версия = %s. Обновление через 5 сек..." % (version, VER))
                script_update(URL_SRV + "/static/" + version)
        else:
            print("У вас последняя версия.")



if __name__ == "__main__":
    
    logger.debug("***ПЕРЕМЕЩЕНИЕ ОКНА***")
    os.system("wndmove.exe %s %d %d" % (window_title, window_x_coordinate, window_y_coordinate))
    
    # global addr, user
    logger.debug("***АНАЛИЗ ПАРАМЕТРОВ ЗАПУСКА***")
    parser = argparse.ArgumentParser(description='summoners war clicker')
    parser.add_argument(
        "-t",
        "--timeout",
        type=int,
        required=False,
        default=1,
        help="Периодичность отправки, секунд"
    )

    args = parser.parse_args()
    try:
        uaddr = requests.get('https://api.ipify.org').text
    except Exception as e:
        print(e)
    uname = key

    check_new_version()


    while True:
        startdate = datetime.now()

        # Main Function
        callback_id = run()

        enddate = datetime.now()
        data = {
            'client_startdate': startdate,
            'client_enddate': enddate,
            'client_version': VER,
            'callback_id': callback_id
        }

        result = requests.post(url=STAT_UPD, data=data)

        logger.debug("***ЗАДЕРЖКА ОТПРАВКИ %d СЕКУНД***" % args.timeout)
        time.sleep(args.timeout)
