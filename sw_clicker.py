#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime, date
import os, signal
import requests
import argparse
import logging
import time
import pickle
import configparser
import shutil
from PIL import Image
from shutil import copyfile


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


##########################################
# CONFIGURATION DATA
##########################################
VER = 181
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
# (RE)WRITE CONFIGURATION FILE
##########################################
def write_config(conf):
    conf.clear()

    conf.add_section('main')
    conf.set('main', '# Файл конфигурации программы SUMMONERS WAR HELPER')
    conf.set('main', '')
    conf.set('main', '# Версия программы')
    conf.set('main', 'version', VER)
    conf.set('main', ' ')
    conf.set('main', '# Обновлять приложение (1 - да, 0 - нет)')
    conf.set('main', 'update', update)
    conf.set('main', '  ')
    conf.set('main', '# Параметры окна, необходимо для перемещения')
    conf.set('main', '# Название окна программы, если перемещение не требуется - сделайте пустым или несуществующим')
    conf.set('main', 'window_title', window_title)
    conf.set('main', '   ')
    conf.set('main', '# Координата по оси X, куда будет перемещаться окно')
    conf.set('main', 'window_x_coordinate', window_x_coordinate)
    conf.set('main', '    ')
    conf.set('main', '# Координата по оси Y, куда будет перемещаться окно')
    conf.set('main', 'window_y_coordinate', window_y_coordinate)
    conf.set('main', '# Конец секции main')

    conf.add_section('gameplay')
    conf.set('gameplay', '# Программа не будет отправлять данные для анализа ИИ в этот промежуток времени.')
    conf.set('gameplay', '# Таймаут обновления во время от запуска до боса')
    conf.set('gameplay', 'long_stage_timeout', long_stage_timeout)
    conf.set('gameplay', '')
    conf.set('gameplay', '# Таймаут обновления во время убийства боса')
    conf.set('gameplay', 'boss_timeout', boss_timeout)
    conf.set('gameplay', ' ')
    conf.set('gameplay', '# Продажа всех выбитых рун (1 - продавать, 0 - не продавать)')
    conf.set('gameplay', 'sell_all_runes', sell_all_runes)
    conf.set('gameplay', '  ')
    conf.set('gameplay', '# Режим только просмотра, программа только отправляет данные на сервер, но не вмешивается в процесс')
    conf.set('gameplay', 'view_only_mode', view_only_mode)
    conf.set('gameplay', '   ')
    conf.set('gameplay', '# Покупать энергию за кристаллы и продолжать.')
    conf.set('gameplay', 'buy_energy_and_go', buy_energy_and_go)
    conf.set('gameplay', '    ')
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
def read_config():
    global VER, key, update, window_title, window_x_coordinate, window_y_coordinate
    global long_stage_timeout, boss_timeout, sell_all_runes, view_only_mode, buy_energy_and_go, sleep_timeout_without_energy

    try:
        logger.info('Reading configuration in swhelp.conf')
        conf = configparser.RawConfigParser(allow_no_value=True)
        conf.read('swhlp.conf')
        if conf.has_option('main', 'version'):
            VER = conf.getint('main', 'version')
        if conf.has_option('authentication', 'key'):
            key = conf.get('authentication', 'key')
        if conf.has_option('main', 'update'):
            update = conf.getint('main', 'update')
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

        logger.info('Версия: [%s]' % VER)
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

        return True

    except Exception:
        logger.error('Failed read config swhlp.conf, reconfiguration...', exc_info=True)
        write_config(conf)
        logger.info('Reconfiguration complete')
        return False



##########################################
# CONNECTION INFO
##########################################
# URL_API = "http://192.168.169.145:30001/api/UploadFile4Recognition"
# URL_SRV = "http://217.71.231.9:30001"
URL_SRV = "http://192.168.169.145:30001"
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


class Stat(object):
    def __init__(self, run_id, name, value):
        self.run_id = run_id
        self.name = name
        self.value = value

def get_image_from_path(image_path):
    # Чтение изображения
    im = Image.open(image_path).convert("RGBA")
    return im


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


def calc_and_write_stat(run_id):
    new_value = 0
    try:
        with open('stat.pkl', 'rb') as input:
            stat_data = pickle.load(input)
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
    if(step > 0):
        text = ("\r"+text+"                      ") % step
        # logger.debug(text)
        print(text, end="")
    elif(step == 0):
        print("\r***ПОЛУЧЕНИЕ И ОБРАБОТКА ИНФОРМАЦИИ***             ", end="")
        logger.debug("***ПОЛУЧЕНИЕ И ОБРАБОТКА ИНФОРМАЦИИ***             ")
    else:
        logger.warning("print_waiting step < 0 ")


##########################################
# MAIN FUNCTION
##########################################
def run():
    global supportFlag, long_stage_timeout, new_start_date, new_start_flag, sleep_timeout_without_energy
    try:
        os.remove("screenshot.jpg")
    except IOError:
        logger.error('err: old scr not found', exc_info=True)
        pass
    datetime_before_scrshot = datetime.now()
    os.system("PCLinkScr.exe")
    last_modify_date = datetime.fromtimestamp(os.path.getatime("screenshot.jpg"))
    while last_modify_date < datetime_before_scrshot:
        last_modify_date = datetime.fromtimestamp(os.path.getatime("screenshot.jpg"))
        time.sleep(0.5)
        logger.debug(last_modify_date, datetime_before_scrshot)

    copyfile("screenshot.jpg", "previous_screenshot.jpg")

    im = get_image_from_path("screenshot.jpg")
    im_resized = im.resize((299, 299), Image.LANCZOS)
    # im_resized.show()
    im_resized.save(IM_PATH)
    result = None
    try:
        file = open(IM_PATH)
    except IOError:
        logger.error(('Image not found at path: ', IM_PATH), exc_info=True)
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
        logger.debug("long_stage_timeout = %s, new_start_date = %s, new_start_flag = %s" % (long_stage_timeout, new_start_date, new_start_flag))
        if not new_start_flag:
            if long_stage_timeout > 30 :
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
        if buy_energy_and_go:
            if not do_mouse_click("PCLinkClk.exe 0 0 40 60"):
                return callback_id
        else:
            if not do_mouse_click("PCLinkClk.exe 0 0 60 60"):
                return callback_id
            i = sleep_timeout_without_energy*60
            text = "***ЭНЕРГИЯ ЗАКОНЧИЛАСЬ - ОЖИДАНИЕ %d СЕКУНД***"
            logger.debug(text % i )
            while i >= 0:
                print_waiting(text, i)
                time.sleep(1)
                i -= 1
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
    os.exit(0)
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

    # Чтение файла конфигурации
    logger.debug("***ЧТЕНИЕ ФАЙЛА КОНФИГУРАЦИИ***")
    while(not read_config()):
        read_config()
    
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

    logger.debug("***ПЕРЕМЕЩЕНИЕ ОКНА***")
    os.system("wndmove.exe %s %d %d" % (window_title, window_x_coordinate, window_y_coordinate))

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

    while True:
        startdate = datetime.now()

        # Main Function
        callback_id = run()

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
