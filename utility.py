# Import Library
import html
import json
import logging
import re
import traceback
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from urllib.parse import urlparse

# Define Variable
lpse_version = "eproc4"
lpse_list = "http://www.inaproc.lkpp.go.id/agregasi/public/json/dt-lpse.json"


# Define Is Exisst
def fill_obj_if_exist(obj, key):
    if key in obj:
        return obj[key]
    else:
        return None


# Define Response
def define_response(data, status: int = 200, message: str = "Success"):
    return {
        "message": message,
        "status": status,
        "data": data
    }


# Initiation Chrome Driver
def init_chrome_driver(osname: str, is_heroku: bool, strategy: str = "eager"):
    # Extension
    chrome_path_ext = ".exe" if "nt" in osname or "windows" in osname else ""
    chrome_path = "driver/chromedriver" + chrome_path_ext
    if is_heroku:
        chrome_path = "/app/.chromedriver/bin/chromedriver"

    # Setting For Driver
    chrome_option = Options()
    chrome_prefs = {
        'profile.default_content_setting_values': {
            'images': 2, 'javascript': 2,
            'plugins': 2, 'popups': 2, 'geolocation': 2,
            'notifications': 2, 'auto_select_certificate': 2,
            'fullscreen': 2, 'mouselock': 2, 'mixed_script': 2,
            'media_stream': 2, 'media_stream_mic': 2,
            'media_stream_camera': 2, 'site_engagement': 2,
            'ppapi_broker': 2, 'automatic_downloads': 2,
            'midi_sysex': 2, 'push_messaging': 2, 'metro_switch_to_desktop': 2,
            'protected_media_identifier': 2, 'app_banner': 2,
        }
    }
    chrome_option.headless = True
    chrome_option.add_argument('--disable-gpu')
    chrome_option.add_argument('--no-sandbox')
    chrome_option.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_option.add_experimental_option('prefs', chrome_prefs)

    # Service For Driver
    chrome_caps = DesiredCapabilities().CHROME
    chrome_caps["pageLoadStrategy"] = strategy
    chrome_service = Service(executable_path=chrome_path)
    chrome_driver = webdriver.Chrome(service=chrome_service, options=chrome_option, desired_capabilities=chrome_caps)
    chrome_driver.set_page_load_timeout(60)

    # End Function
    return chrome_driver


# Strip Tags
def strip_tags(ret):
    ret = html.unescape(ret)
    ret = re.sub(re.compile("<.*?>"), "", str(ret))
    ret = ret.strip()
    ret = ret.replace("[...]", "")
    return ret


# Get List Tender
def tender_daftar(base_url: str, limit: int, chrome_driver: WebDriver, order: str = "desc"):
    # Variable
    result = {}
    base_url = base_url + lpse_version
    limit = 10 if limit == 0 else limit

    try:
        # Get Home Page
        chrome_driver.get(base_url + "/lelang")

        # Get Authenticity Token
        split_raw_html = chrome_driver.page_source.split("d.authenticityToken = '")
        split_raw_html = split_raw_html[1].split("';")
        authenticity_token = split_raw_html[0]

        # Get Tender JSON
        tender_url = base_url + "/dt/lelang"
        tender_url += "?columns[0][data]=0&columns[0][orderable]=true&order[0][column]=0&order[0][dir]=" + order + \
                      "&length=" + str(limit) + "&start=0"
        tender_url += "&authenticityToken=" + authenticity_token
        chrome_driver.get(tender_url)
        tender_json = json.loads(chrome_driver.find_element(By.TAG_NAME, "pre").text)

        # Iterate Every Tender
        tender_array = []
        for tender in tender_json["data"]:
            tender_dictionary = {
                "url_detail": base_url + "/lelang/" + strip_tags(tender[0]) + "/pengumumanlelang",
                "url_jadwal": base_url + "/lelang/" + strip_tags(tender[0]) + "/jadwal",
                "kode": strip_tags(tender[0]),
                "judul": strip_tags(tender[1]).replace("Tender Ulang", "(Tender Ulang)"),
                "instansi": strip_tags(tender[2]),
                "proses": strip_tags(tender[5]),
                "metode": strip_tags(tender[6]),
                "template": strip_tags(tender[7]),
                "nilai": strip_tags(tender[4]),
                "fase": strip_tags(tender[3])
            }
            tender_array.append(tender_dictionary)
        result = define_response(tender_array)
    except Exception as e:
        # Log Error
        logging.error(str(e))
        traceback.print_exc()
        result = define_response([], 500, "Error")
    finally:
        return result


# Get Tender Jadwal
def tender_jadwal(url: str, chrome_driver: WebDriver):
    # Variable
    result = {}

    try:
        # Get Detail Page
        chrome_driver.get(url)

        # Get Data
        jadwal_array = []
        jadwal_array_final = []
        jadwal_title = []
        is_first = True
        table = chrome_driver.find_element(By.TAG_NAME, "table")
        for table_row in table.find_elements(By.TAG_NAME, "tr"):
            if is_first:
                for table_data in table_row.find_elements(By.TAG_NAME, "th"):
                    jadwal_title.append(strip_tags(table_data.text).strip().lower().replace(" ", "_"))
                    is_first = False
            else:
                idx = 0
                jadwal = {}
                for table_data in table_row.find_elements(By.TAG_NAME, "td"):
                    jadwal[jadwal_title[idx]] = table_data.text
                    idx += 1
                jadwal_array.append(jadwal)
        for jadwal in jadwal_array:
            jadwal_final = {"no": fill_obj_if_exist(jadwal, "no"), "mulai": fill_obj_if_exist(jadwal, "mulai"),
                            "sampai": fill_obj_if_exist(jadwal, "sampai"), "tahap": fill_obj_if_exist(jadwal, "tahap"),
                            "perubahan": fill_obj_if_exist(jadwal, "perubahan")}
            jadwal_array_final.append(jadwal_final)
        result = define_response(jadwal_array_final)

    except Exception as e:
        # Log Error
        logging.error(str(e))
        result = define_response([], 500, "Error")
    finally:
        return result


# Get Tender Detail
def tender_detail(url: str, chrome_driver: WebDriver):
    # Variable
    result = {}

    try:
        # Get Detail Page
        chrome_driver.get(url)

        # Get Data
        is_row_head = False
        row_title = ""
        row_content = ""
        detail = {}
        table = chrome_driver.find_element(By.TAG_NAME, "table")
        for table_element in \
            table.find_elements(By.CSS_SELECTOR, "table tr th.bgwarning, table tr th.bg-warning, table tr td"):
            if table_element.tag_name == "th" and not is_row_head:
                is_row_head = True
                row_content = ""
                row_title = strip_tags(table_element.get_attribute("innerHTML").strip()).replace(" ", "_").lower()
            elif table_element.tag_name == "td" and is_row_head:
                is_row_head = False
                row_content = table_element.get_attribute("innerHTML").strip()
                if "<table" not in row_content \
                        and "<ul" not in row_content \
                        and "<ol" not in row_content:
                    row_content = strip_tags(row_content)
                if "nama_tender" in row_title \
                        or "nama_lelang" in row_title:
                    row_content = row_content.replace("Tender Ulang", "(Tender Ulang)")
                detail[row_title] = row_content

        detail_final = {"kode_tender": fill_obj_if_exist(detail, "kode_tender"),
                        "nama_tender": fill_obj_if_exist(detail, "nama_tender"),
                        "satuan_kerja": fill_obj_if_exist(detail, "satuan_kerja"),
                        "nilai_pagu_paket": fill_obj_if_exist(detail, "nilai_pagu_paket"),
                        "nilai_hps_paket": fill_obj_if_exist(detail, "nilai_hps_paket"),
                        "kualifikasi_usaha": fill_obj_if_exist(detail, "kualifikasi_usaha"),
                        "jenis_kontrak": fill_obj_if_exist(detail, "jenis_kontrak"),
                        "kategori": fill_obj_if_exist(detail, "jenis_pengadaan"),
                        "tahap_tender": fill_obj_if_exist(detail, "tahap_tender_saat_ini"),
                        "tahun_anggaran": fill_obj_if_exist(detail, "tahun_anggaran"),
                        "tanggal_pembuatan": fill_obj_if_exist(detail, "tanggal_pembuatan"),
                        "sistem_pengadaan": fill_obj_if_exist(detail, "metode_pengadaan"),
                        "syarat_kualifikasi": fill_obj_if_exist(detail, "syarat_kualifikasi"),
                        "peserta_tender": fill_obj_if_exist(detail, "peserta_tender"),
                        "instansi": fill_obj_if_exist(detail, "k/l/pd"),
                        "cara_pembayaran": fill_obj_if_exist(detail, "cara_pembayaran")}
        result = define_response(detail_final)

    except Exception as e:
        # Log Error
        logging.error(str(e))
        result = define_response([], 500, "Error")
    finally:
        return result


# Get List LPSE
def lpse_daftar():
    # Variable
    result = {}

    try:
        # Get List
        request_res = requests.get(lpse_list)
        url_data_json = json.loads(request_res.text)
        url_result = []

        # Process List
        for url_data in url_data_json["data"]:
            url_parse = urlparse(url_data[2])
            url_domain = str(url_parse.scheme) + "://" + str(url_parse.netloc)
            url_data = {
                "nama": url_data[1],
                "url": url_domain,
                "status": url_data[3]
            }
            url_result.append(url_data)

        result = define_response(url_result)
    except Exception as e:
        # Log Error
        logging.error(str(e))
        result = define_response([], 500, "Error")
    finally:
        return result
