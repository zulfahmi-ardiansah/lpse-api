import json
import time

import requests

from bs4 import BeautifulSoup
from utility import fill_obj_if_exist

result_array = []
detail_array = []
paging_index = 1
paging_status = True

while paging_status:
    print(paging_index)
    list_url = "https://inaproc.id/lpse?page=" + str(paging_index)
    list_res = requests.get(list_url)
    list_res = BeautifulSoup(list_res.text, "html.parser")
    list_res = list_res.select("table tr td .title a")
    paging_index += 1
    paging_status = False
    for link_list in list_res:
        detail_array.append(link_list.get("href"))
        paging_status = True
    if paging_status is not True:
        break
    time.sleep(1)

for detail_url in detail_array:
    try:
        detail_res = requests.get(detail_url)
        if detail_res.status_code == 200:
            detail_res = BeautifulSoup(detail_res.text, "html.parser")
            sec_info = detail_res.select(".box:last-child .box-body strong, "
                                         ".box:last-child .box-body div, "
                                         ".box:last-child .box-body p.text-muted")
            sec_logo = detail_res.select_one(".profile-img.img-responsive")
            sec_name = detail_res.select_one(".profile-username.text-center")
            is_first = True
            prop_array = {}
            prop_title = ""
            prop_content = ""
            for sec_info_tag in sec_info:
                if sec_info_tag.name == "strong":
                    prop_title = str(sec_info_tag.string).strip().lower().replace(" ", "")
                    prop_array[prop_title] = ""
                else:
                    if sec_info_tag.string is not None:
                        prop_content = str(sec_info_tag.string).strip() + " "
                        prop_array[prop_title] += prop_content
            if sec_logo is not None:
                prop_array["logo"] = sec_logo.get("src")
            if sec_name is not None:
                prop_array["nama"] = str(sec_name.string).strip()
            if "url" in prop_array:
                prop_array["url"] = prop_array["url"].replace("/eproc4/", "")
                prop_array["url"] = prop_array["url"].replace("/eproc4", "")
                prop_array["url"] = prop_array["url"].replace("/eproc/", "")
                prop_array["url"] = prop_array["url"].replace("/eproc", "")
            result = {
                "id": fill_obj_if_exist(prop_array, "id"),
                "provinsi": fill_obj_if_exist(prop_array, "provinsi"),
                "alamat": fill_obj_if_exist(prop_array, "alamat"),
                "helpdesk": fill_obj_if_exist(prop_array, "helpdesk"),
                "url": fill_obj_if_exist(prop_array, "url"),
                "logo": fill_obj_if_exist(prop_array, "logo"),
                "nama": fill_obj_if_exist(prop_array, "nama")
            }
            print(result["nama"])
            result_array.append(result)
            with open('static/lpse-list.json', 'w') as outfile:
                json.dump(result_array, outfile, indent=4)
            time.sleep(1)
    except Exception as e:
        False
