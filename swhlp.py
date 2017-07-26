#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, date
import os
import signal
import requests
import argparse
import logging
import time
import pickle
import configparser
import shutil
from PIL import Image
from shutil import copyfile
import subprocess


##########################################
# LOGGER INFO
##########################################
# set up logging to file - see previous section for more details
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S',
                    filename='swhlp' + str(date.today()) + '.log',
                    filemode='a')
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.INFO)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)
# Now, define a couple of other loggers which might represent areas in application:
logger = logging.getLogger(__name__)

image_and_screen_size = (0, 0)


##########################################
# CONFIGURATION DATA
##########################################
VER = 212
adb_mode = 0
adb_path = 'tools\\'
pause = 0
key = ''
long_stage_timeout = 15
boss_timeout = 10
update = 0
sell_all_runes = 0
window_title = 'sw_farm'
window_x_coordinate = 0
window_y_coordinate = 0
view_only_mode = False
buy_energy_and_go = True
sleep_timeout_without_energy = 120


##########################################
# CONNECTION INFO
##########################################
# URL_API = "http://192.168.169.145:30001/api/UploadFile4Recognition"
# URL_SRV = "http://217.71.231.9:30001"
URL_SRV = "http://217.71.231.9:30001"
URL_API = URL_SRV + "/api/UploadFile4Recognition"
URL_UPD = URL_SRV + "/chkver"
STAT_UPD = URL_SRV + "/stat"


##########################################
# LOCAL FILES AND TEMP DATA
##########################################
IMAGE_TYPE = "screenshot"
IM_PATH = "screenshot.jpg"
supportFlag = True
uaddr = "unknown"
uname = "unknown"
img_meta = []

new_start_date = None
new_start_flag = None


##########################################
# GENERATE COMMENT AS KEY NAME 4 CONFIG
##########################################
def generate_clear_line_4_conf(config, section):
    line_value = ' '
    # Просмотр ключей секции, если нет такой строки пробелов, то она подойдёт,
    # это нужно т.к. одинаковых ключей быть не должно
    keys = list(config[section].keys())
    for key in keys:
        if key == line_value:
            line_value += ' '
        else:
            if str(key).strip(' ') == '':
                return line_value
    return line_value


##########################################
# (RE)WRITE CONFIGURATION FILE
##########################################
def write_config(conf):
    conf.clear()

    conf.add_section('main')
    conf.set('main', '# Файл конфигурации программы SUMMONERS WAR HELPER')
    conf.set('main', generate_clear_line_4_conf(conf, 'main'))
    conf.set('main', '# Версия программы')
    conf.set('main', 'version', VER)
    conf.set('main', generate_clear_line_4_conf(conf, 'main'))
    conf.set('main', '# Режим работы ADB. (1 - вкл, 0 - выкл)')
    conf.set('main', 'adb_mode', adb_mode)
    conf.set('main', generate_clear_line_4_conf(conf, 'main'))
    conf.set('main', '# Путь к ADB')
    conf.set('main', 'adb_path', adb_path)
    conf.set('main', generate_clear_line_4_conf(conf, 'main'))
    conf.set('main', '# Обновлять приложение (1 - да, 0 - нет)')
    conf.set('main', 'update', update)
    conf.set('main', generate_clear_line_4_conf(conf, 'main'))
    conf.set('main', '# Поставить игру на паузу')
    conf.set('main', 'pause', pause)
    conf.set('main', generate_clear_line_4_conf(conf, 'main'))
    conf.set('main', '# Параметры окна, необходимо для перемещения')
    conf.set('main', '# Название окна программы, если перемещение не требуется - сделайте пустым или несуществующим')
    conf.set('main', 'window_title', window_title)
    conf.set('main', generate_clear_line_4_conf(conf, 'main'))
    conf.set('main', '# Координата по оси X, куда будет перемещаться окно')
    conf.set('main', 'window_x_coordinate', window_x_coordinate)
    conf.set('main', generate_clear_line_4_conf(conf, 'main'))
    conf.set('main', '# Координата по оси Y, куда будет перемещаться окно')
    conf.set('main', 'window_y_coordinate', window_y_coordinate)
    conf.set('main', '# Конец секции main')

    conf.add_section('gameplay')
    conf.set('gameplay', '# Программа не будет отправлять данные для анализа ИИ в этот промежуток времени.')
    conf.set('gameplay', '# Таймаут обновления во время от запуска до боса')
    conf.set('gameplay', 'long_stage_timeout', long_stage_timeout)
    conf.set('gameplay', generate_clear_line_4_conf(conf, 'gameplay'))
    conf.set('gameplay', '# Таймаут обновления во время убийства боса')
    conf.set('gameplay', 'boss_timeout', boss_timeout)
    conf.set('gameplay', generate_clear_line_4_conf(conf, 'gameplay'))
    conf.set('gameplay', '# Продажа всех выбитых рун (1 - продавать, 0 - не продавать)')
    conf.set('gameplay', 'sell_all_runes', sell_all_runes)
    conf.set('gameplay', generate_clear_line_4_conf(conf, 'gameplay'))
    conf.set('gameplay', '# Режим только просмотра, программа только отправляет данные на сервер, но не вмешивается в процесс')
    conf.set('gameplay', 'view_only_mode', view_only_mode)
    conf.set('gameplay', generate_clear_line_4_conf(conf, 'gameplay'))
    conf.set('gameplay', '# Покупать энергию за кристаллы и продолжать.')
    conf.set('gameplay', 'buy_energy_and_go', buy_energy_and_go)
    conf.set('gameplay', generate_clear_line_4_conf(conf, 'gameplay'))
    conf.set('gameplay', '# Таймаут ожиидания, после которого будет предпринята попытка продолжить прохождение.')
    conf.set('gameplay', '# Используется при buy_energy_and_go = False - когда энергия не покупается. ')
    conf.set('gameplay', '# Таймаут исчисляется в минутах, Если вам нужно 2 часа, то необходимо указать: sleep_timeout_without_energy = 120')
    conf.set('gameplay', 'sleep_timeout_without_energy', sleep_timeout_without_energy)
    conf.set('gameplay', '# Конец секции gameplay')

    conf.add_section('authentication')
    conf.set('authentication', '# Ваша кодовая фраза')
    conf.set('authentication', 'key', key)
    conf.set('authentication', '# Конец секции authentication')

    with open('swhlp.conf', 'w') as configfile:
        conf.write(configfile)


##########################################
# READ AND CHECK CONFIGURATION FILE
##########################################
def read_config(return_key_value):
    global VER, adb_mode, adb_path, key, update, window_title
    global window_x_coordinate, window_y_coordinate, pause
    global long_stage_timeout, boss_timeout, sell_all_runes, view_only_mode
    global buy_energy_and_go, sleep_timeout_without_energy

    try:
        conf = configparser.RawConfigParser(allow_no_value=True)
        conf.read('swhlp.conf')

        if return_key_value:
            for section in conf.sections():
                if conf.has_option(section, return_key_value):
                    return conf.get(section, return_key_value)
                else:
                    return None

        logger.info('Reading configuration in swhelp.conf')
        if conf.has_option('main', 'version'):
            VER = conf.getint('main', 'version')
        if conf.has_option('main', 'adb_mode'):
            adb_mode = conf.getint('main', 'adb_mode')
        if conf.has_option('main', 'adb_path'):
            adb_path = conf.get('main', 'adb_path')
        if conf.has_option('authentication', 'key'):
            key = conf.get('authentication', 'key')
        if conf.has_option('main', 'update'):
            update = conf.getint('main', 'update')
        if conf.has_option('main', 'pause'):
            pause = conf.getint('main', 'pause')
        if conf.has_option('main', 'window_title'):
            window_title = conf.get('main', 'window_title')
        if conf.has_option('main', 'window_x_coordinate'):
            window_x_coordinate = conf.getint('main', 'window_x_coordinate')
        if conf.has_option('main', 'window_y_coordinate'):
            window_y_coordinate = conf.getint('main', 'window_y_coordinate')
        if conf.has_option('gameplay', 'long_stage_timeout'):
            long_stage_timeout = conf.getint('gameplay', 'long_stage_timeout')
        if conf.has_option('gameplay', 'boss_timeout'):
            boss_timeout = conf.getint('gameplay', 'boss_timeout')
        if conf.has_option('gameplay', 'sell_all_runes'):
            sell_all_runes = conf.getint('gameplay', 'sell_all_runes')
        if conf.has_option('gameplay', 'view_only_mode'):
            view_only_mode = conf.getboolean('gameplay', 'view_only_mode')
        if conf.has_option('gameplay', 'buy_energy_and_go'):
            buy_energy_and_go = conf.getboolean('gameplay', 'buy_energy_and_go')
        if conf.has_option('gameplay', 'sleep_timeout_without_energy'):
            sleep_timeout_without_energy = conf.getint('gameplay', 'sleep_timeout_without_energy')

        write_config(conf)

        view_config()

        return True

    except Exception:
        logger.error('Failed read config swhlp.conf, reconfiguration...', exc_info=True)
        write_config(conf)
        logger.info('Reconfiguration complete')
        return False


def view_config():
    global VER, adb_mode, adb_path, key, update, window_title
    global window_x_coordinate, window_y_coordinate, pause
    global long_stage_timeout, boss_timeout, sell_all_runes, view_only_mode
    global buy_energy_and_go, sleep_timeout_without_energy

    # Очистка окна от данных этапа подготовки
    os.system('cls' if os.name == 'nt' else 'clear')

    logger.info('Версия: [%s]' % VER)
    logger.info('ADB включен: [%s]' % ('ДА' if adb_mode else 'НЕТ'))
    logger.info('Путь к ADB: [%s]' % adb_path)
    logger.info('Ваша кодовая фраза: [%s]' % key)
    logger.info('Обновлять приложение: [%s]' % ('ДА' if update else 'НЕТ'))
    logger.info('Название окна программы: [%s]' % window_title)
    logger.info('Координата по оси X: [%s]' % window_x_coordinate)
    logger.info('Координата по оси Y: [%s]' % window_y_coordinate)
    logger.info('Таймаут обновления во время от запуска до боса: [%sсек]' % long_stage_timeout)
    logger.info('Таймаут обновления во время убийства боса: [%sсек]' % boss_timeout)
    logger.info('Продажа всех выбитых рун: [%s]' % ('ДА' if sell_all_runes else 'НЕТ'))
    logger.info('Режим "только просмотр": [%s]' % ('ДА' if view_only_mode else 'НЕТ'))
    logger.info('Покупать энергию за кристаллы и продолжать": [%s]' % ('ДА' if buy_energy_and_go else 'НЕТ'))
    logger.info('Таймаут ожидания пока не накопится энергия: [%sмин]' % sleep_timeout_without_energy)

    logger.info('')
    logger.info('Ваш адрес = [%s]' % uaddr)
    logger.info('Ваше имя = [%s]' % uname)


class Stat(object):
    def __init__(self, run_id, name, value):
        self.run_id = run_id
        self.name = name
        self.value = value

def get_image_from_path(image_path):
    while True:
        try:
            # Чтение изображения
            im = Image.open(image_path).convert("RGBA")
            return im
        except:
            logger.debug('image not opened')
            time.sleep(0.2)
            pass


##########################################
# UPLOAD IMAGE TO WEB-SERVER AND GET ANSWER
##########################################
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


##########################################
# CHECK IMAGE SIMILARITY
##########################################
def get_im_similarity_index(screenshot, previous_screenshot):
    sim_result = 0

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
            sim_result += 1

    return sim_result


##########################################
# DO ACTION IN GAME
##########################################
def do_mouse_click(com):
    os.system("PCLinkScr.exe")
    idx = get_im_similarity_index("screenshot.jpg", "previous_screenshot.jpg")
    if idx < 3:
        logger.debug('err: image similarity index too small (lower than 3)!')
        return False
    else:
        os.system(com)
        return True

##########################################
# DO ALTERNATE ACTION IN GAME VIA ADB
##########################################
def do_adb_tap(X, Y):
    global image_and_screen_size
    if image_and_screen_size[0] > 0:
        procId = subprocess.Popen(adb_path+'adb shell', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        tap_x = str(int(image_and_screen_size[0] * X / 100))
        tap_y = str(int(image_and_screen_size[1] * Y / 100))
        shell_command_str = 'input tap ' + tap_x + ' ' + tap_y + '\nexit\n'
        shell_command_line = str.encode(shell_command_str)
        out, err = procId.communicate(shell_command_line)
        logger.debug('выполнение команды adb shell:'+shell_command_str.replace('\n', ' '))
        logger.debug(out.decode("utf-8").replace('\n', ' ').replace('\r', ' ').strip())
    else:
        logger.debug("resolution[0] <= 0")


##########################################
# DO SCREENSHOT VIA ADB
##########################################
def adb_do_screenshot():
    try:
        adb_path = ''
        print_waiting('***ОЖИДАНИЕ ПОДКЛЮЧЕНИЯ К УСТРОЙСТВУ***', -1)
        logger.debug(str(subprocess.check_output(adb_path+'adb wait-for-device', shell=True)).replace('\n', ' '))
        logger.debug(str(subprocess.check_output(adb_path+'adb shell screencap -p /data/local/tmp/tmp.png', shell=True)).replace('\n', ' '))
        procId = subprocess.Popen('adb pull /data/local/tmp/tmp.png screenshot.jpg', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = procId.communicate()
        # logger.debug('Получение скрина: ' + err.decode("utf-8").replace('\n', ' ').replace('\r', ' ').strip())
        logger.debug(str(subprocess.check_output(adb_path+'adb shell rm /data/local/tmp/tmp.png', shell=True)).replace('\n', ' '))
        # get_image_from_path("screenshot.jpg") # use it if file not loaded correctly
        print_waiting('***ИЗОБРАЖЕНИЕ ПОЛУЧЕНО***', -1)
        return True
    except:
        return None


##########################################
# GET STAT DATA
##########################################
def calc_and_write_stat(run_id):
    new_value = 0
    try:
        with open('stat.pkl', 'rb') as stats:
            stat_data = pickle.load(stats)
            _run_id = stat_data.run_id
            _name = stat_data.name
            _value = stat_data.value

            _now = datetime.now()
            logstr = "дата из файла = [%s], сейчас = [%s], дата начала = [%s], новая дельта (время выполнения) в секундах = [%s], предыдущая дельта в секундах = [%s]" % (_value, _now, run_id, (_now - run_id).seconds, new_value)
            logger.debug(logstr)
            new_value = (_value + (datetime.now() - run_id).seconds) / 2
            logstr = "стабилизация времени выполнения - вероятно в следствии ошибки выполнения. Время выполнения (дельта) = "
            if new_value > 600:
                new_value = 600
                logger.debug(logstr + "[%s] приведено к [%s]" % (new_value, "600"))
            if new_value < 20:
                new_value = 20
                logger.debug(logstr + "[%s] приведено к [%s]" % (new_value, "20"))

            with open('stat.pkl', 'wb') as output:
                stat = Stat(run_id, 'start-boss', new_value)
                pickle.dump(stat, output, pickle.HIGHEST_PROTOCOL)
            logger.debug("stat %s --> %s" % (_value, new_value))

    except IOError:
        with open('stat.pkl', 'wb') as output:
            stat = Stat(run_id, 'start-boss', new_value)
            pickle.dump(stat, output, pickle.HIGHEST_PROTOCOL)
        logstr = ("stat init %s" % new_value)
        logger.error(logstr, exc_info=True)

    return int(new_value)


##########################################
# PRINT WAITING TIME TO CONSOLE IN ONE STRING
##########################################
def print_waiting(text, step):
    max_str_len = 75
    if step > 0:
        text = (text) % step
    elif step == 0:
        text = '***ПОЛУЧЕНИЕ И ОБРАБОТКА ИНФОРМАЦИИ***'
    else:
        pass

    while len(text) < max_str_len:
        text += ' '
    text = "\r"+text+""
    print(text, end="")
    logger.debug(text)


##########################################
# MAIN FUNCTION
##########################################
def run():
    global supportFlag, long_stage_timeout, new_start_date, new_start_flag, sleep_timeout_without_energy, image_and_screen_size
    try:
        os.remove('screenshot.jpg')
    except IOError:
        pass
    datetime_before_scrshot = datetime.now()
    if adb_mode:
        while not adb_do_screenshot():
            text = "***УСТРОЙСТВО НЕ ПОДКЛЮЧЕНО - ПЕРЕПОДКЛЮЧЕНИЕ ЧЕРЕЗ %s СЕК***"
            i = 5
            logger.debug(text % i)
            while i >= 0:
                print_waiting(text, i)
                time.sleep(1)
                i -= 1
    else:
        os.system("PCLinkScr.exe")
    try:
        with open('screenshot.jpg') as file:
            last_modify_date = datetime.fromtimestamp(os.path.getatime('screenshot.jpg'))
            i = 0
            while (last_modify_date < datetime_before_scrshot) & (i < 3):
                last_modify_date = datetime.fromtimestamp(os.path.getatime('screenshot.jpg'))
                time.sleep(0.5)
                i += 1 
                # logger.debug(str(last_modify_date), str(datetime_before_scrshot))
    except IOError:
        logger.debug('scr not found', exc_info=True)
        return
    except Exception:
        logger.debug("scr file info exc", exc_info=True)
        time.sleep(1)
        pass

    copyfile("screenshot.jpg", "previous_screenshot.jpg")

    im = get_image_from_path("screenshot.jpg")
    image_and_screen_size = im.size
    logger.debug('image_and_screen_size = ' + image_and_screen_size.__str__())
    im_resized = im.resize((299, 299), Image.LANCZOS)
    # im_resized.show()
    im_resized.save(IM_PATH)
    result = None
    callback_id = None
    try:
        file = open(IM_PATH)
    except IOError:
        logger.error(('Image not found at path: ', IM_PATH), exc_info=True)
    else:
        with file:
                msg_txt = '***ОТПРАВКА ИЗОБРАЖЕНИЯ НА СЕРВЕР***'
                logger.debug(msg_txt)
                print_waiting(msg_txt, -1)
                callback_id, result = upload_to_web(IM_PATH)
    if result:
        msg_txt = ('***ОТВЕТ ПОЛУЧЕН: [%s] ***' % result)
        print_waiting(msg_txt, -1)
        logger.debug(msg_txt)
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
        if adb_mode:
            do_adb_tap(85, 70)
        else:
            os.system("PCLinkClk.exe 0 0 85 70")
    elif (result == "02boot") | (result == "03st"):
        logger.debug("long_stage_timeout = %s, new_start_date = %s, new_start_flag = %s" % (long_stage_timeout, new_start_date, new_start_flag))
        if not new_start_flag:
            if long_stage_timeout > 30:
                long_stage_timeout -= 30
            logger.debug("***ОЖИДАНИЕ %d СЕКУНД***" % long_stage_timeout)
            if long_stage_timeout > 120:
                i = int(long_stage_timeout / 2)
                if new_start_flag == 10:
                    new_start_flag = 1
                else:
                    new_start_flag = 10

            else:
                i = long_stage_timeout
                new_start_flag = 1
            text = "***ОЖИДАНИЕ %d СЕКУНД***"
            while i >= 0:
                print_waiting(text, i)
                time.sleep(1)
                i -= 1
            # print("\n")
        else:
            text = "***ПОВТОРНЫЙ ЗАПРОС - ОЖИДАНИЕ %d СЕКУНД***"
            logger.debug(text % 10)
            i = 10
            while i >= 0:
                print_waiting(text, i)
                time.sleep(1)
                i -= 1
            # print("\n")
        pass
    elif result == "07boss1":
        text = "***ОЖИДАНИЕ %d СЕКУНД***"
        logger.debug(text % boss_timeout)
        i = boss_timeout
        while i >= 0:
            print_waiting(text, i)
            time.sleep(1)
            i -= 1
        # print("\n")
        pass
    elif result == "11victory1":
        long_stage_timeout = calc_and_write_stat(new_start_date)
        if adb_mode:
            do_adb_tap(50, 50)
        else:
            os.system("PCLinkClk.exe")
        time.sleep(0.5)
        if adb_mode:
            do_adb_tap(50, 50)
        else:
            os.system("PCLinkClk.exe")
        new_start_date = None
    elif result == "11revive":
        if adb_mode:
            do_adb_tap(65, 65)
        else:
            os.system("PCLinkClk.exe 0 0 65 65")
    elif result == "12victory2":
        if adb_mode:
            do_adb_tap(50, 50)
        else:
            os.system("PCLinkClk.exe")
    elif result == "13other no rune":
        if adb_mode:
            do_adb_tap(50, 75)
            do_adb_tap(50, 80)
        else:
            os.system("PCLinkClk.exe 0 0 50 75")
            os.system("PCLinkClk.exe 0 0 50 80")
    # elif (result == "13rune 5"):
    #     os.system("PCLinkClk.exe 0 0 37 78")
    elif (result == "13rune 6") | ("13rune" in result):
        if sell_all_runes == 1:
            logger.debug("Продажа всех рун ВКЛ")
            if adb_mode:
                do_adb_tap(37, 78)
            else:
                if not do_mouse_click("PCLinkClk.exe 0 0 37 78"):
                    return callback_id
        else:
            logger.debug("Продажа всех рун НЕ вкл")
            if adb_mode:
                do_adb_tap(63, 78)
            else:
                if not do_mouse_click("PCLinkClk.exe 0 0 63 78"):
                    return callback_id
    elif result == "15replay":
        if adb_mode:
            do_adb_tap(45, 50)
        else:
            os.system("PCLinkClk.exe 0 0 45 50")
        new_start_date = None
    elif result == "14sell":
        if adb_mode:
            do_adb_tap(37, 60)
        else:
            if not do_mouse_click("PCLinkClk.exe 0 0 37 60"):
                return callback_id
    elif (result == "16no energy") | (result == "18buy energy"):
        if buy_energy_and_go:
            if adb_mode:
                do_adb_tap(40, 60)
            else:
                if not do_mouse_click("PCLinkClk.exe 0 0 40 60"):
                    return callback_id
        else:
            if adb_mode:
                do_adb_tap(60, 60)
            else:
                if not do_mouse_click("PCLinkClk.exe 0 0 60 60"):
                    return callback_id
            i = sleep_timeout_without_energy*60
            text = "***ЭНЕРГИЯ ЗАКОНЧИЛАСЬ - ОЖИДАНИЕ %d СЕКУНД***"
            logger.debug(text % i)
            while i >= 0:
                print_waiting(text, i)
                time.sleep(1)
                i -= 1
    elif result == "17click energy":
        if supportFlag:
            pass
            if adb_mode:
                do_adb_tap(30, 50)
            else:
                if not do_mouse_click("PCLinkClk.exe 0 0 30 50"):
                    return callback_id
        else:
            if adb_mode:
                do_adb_tap(83, 17)
            else:
                if not do_mouse_click("PCLinkClk.exe 0 0 83 17"):
                    return callback_id
        supportFlag = not supportFlag
    elif result == "19buy energy ok":
        if adb_mode:
            do_adb_tap(50, 60)
        else:
            if not do_mouse_click("PCLinkClk.exe 0 0 50 60"):
                return callback_id
    elif result == "20energy full":
        if adb_mode:
            do_adb_tap(83, 17)
        else:
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
    sw_path = path + '/sw_clicker.py'
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
        if int(version) > VER:
            if update != 1:
                logger.info("Обнаружена новая версия = %s. Текущая версия = %s. Update is off. \nYou can switch on update in 'CONF.py'." % (version, VER))
            else:
                logger.info("Обнаружена новая версия = %s. Текущая версия = %s. Обновление через 5 сек..." % (version, VER))
                script_update(URL_SRV + "/static/" + version)
        else:
            logger.info("У вас последняя версия = %s." % VER)


##########################################
# KILL ALL RUNNING UTILITIES
##########################################
def clearing():
    logger.debug('Уборка мусора')
    os.system('taskkill /IM PCLinkScr.exe /F')
    os.system('taskkill /IM PCLinkClk.exe /F')
    os.system('taskkill /IM wndmove.exe /F')


##########################################
# IF PROGRAM CLOSING - ***NOT WORKS***
##########################################
def on_stop(*args):
    logger.debug('Распознано закрытие окна.')
    clearing()
    logger.debug('Завершение работы.')
    exit(0)
for sig in (signal.SIGBREAK, signal.SIGINT, signal.SIGTERM):
    signal.signal(sig, on_stop)


##########################################
# MAIN FUNCTION
##########################################
if __name__ == "__main__":
    logger.debug("\n\n\n")
    logger.debug("***ЗАПУСК ПРОГРАММЫ В [%s]***" % datetime.today())
    clearing()
    # Очистка окна от данных этапа подготовки
    os.system('cls' if os.name == 'nt' else 'clear')
    cmd = 'config_menu.exe swhlp.conf'
    subprocess.Popen(cmd, shell=True)
    # Чтение файла конфигурации
    logger.debug("***ЧТЕНИЕ ФАЙЛА КОНФИГУРАЦИИ***")
    while(not read_config(None)):
        read_config(None)
    
    # global addr, user, pause
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

    logger.debug("***ПЕРЕМЕЩЕНИЕ ОКНА***")
    os.system("wndmove.exe %s %d %d" % (window_title, window_x_coordinate, window_y_coordinate))
    os.system("wndmove.exe %s %d %d" % ('Conf', window_x_coordinate, window_y_coordinate))
    logger.info('')
    try:
        uaddr = requests.get('https://api.ipify.org').text
        logger.info('Ваш адрес = [%s]' % uaddr)
    except Exception as e:
        logger.error('Failed to get IP info from ipify.org', exc_info=True)
    uname = key
    logger.info('Ваше имя = [%s]' % uname)

    logger.info('')
    check_new_version()

    logger.info('')
    logger.info('***НАЧАЛО РАБОТЫ ПРОГРАММЫ***\n')
    callback_id = None
    while True:
        startdate = datetime.now()

        read_config(None)
        while pause:
            read_config(None)
            print_waiting('Пауза', -1)
            time.sleep(0.2)

        view_config()

        # Main Function
        try:
            callback_id = run()
        except Exception as e:
            logger.error('main function error', exc_info=True)

        enddate = datetime.now()
        data = {
            'user_name': uname,
            'client_startdate': startdate,
            'client_enddate': enddate,
            'client_version': VER,
            'callback_id': callback_id
        }

        result = requests.post(url=STAT_UPD, data=data)

        logger.debug("***ЗАДЕРЖКА ОТПРАВКИ %d СЕКУНД***" % args.timeout)
        time.sleep(args.timeout)
[main]
pause=1
[gameplay]
sell_all_runes=1
