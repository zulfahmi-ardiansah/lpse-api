# Import Library
from flask import Flask, request, jsonify, render_template
from utility import tender_daftar, tender_detail, lpse_daftar, define_response, init_chrome_driver, tender_jadwal
import os


# Initiate App
app = Flask(__name__)
app_port = 5000
chrome_driver = init_chrome_driver(os.name, True)


# Swagger Guide
@app.get("/")
def get_swagger_guide():
    return render_template("index.html")


# Daftar LPSE
@app.get("/daftarLpse")
def get_list_url():
    return jsonify(lpse_daftar())


# Daftar Tender
@app.post("/daftarTender")
def get_daftar_tender():
    sc_result = define_response([], 500, "Error : URL is empty")
    if request.is_json:
        if "url" in request.json:
            req_url = request.json["url"]
            req_limit = 0
            req_order = "desc"
            if "limit" in request.json:
                req_limit = int(request.json["limit"])
            if "order" in request.json:
                if str(request.json["order"]).lower() in ["desc", "asc"]:
                    req_order = str(request.json["order"]).lower()
            sc_url = req_url + ("" if req_url[-1] == "/" else "/")
            sc_result = tender_daftar(sc_url, int(req_limit), chrome_driver, req_order)
    return jsonify(sc_result)


# Detail Tender
@app.post("/detailTender")
def get_detail_tender():
    sc_result = define_response([], 500, "Error : URL is empty")
    if request.is_json:
        if "url" in request.json:
            sc_url = request.json["url"]
            sc_result = tender_detail(sc_url, chrome_driver)
    return jsonify(sc_result)


# Jadwal Tender
@app.post("/jadwalTender")
def get_jadwal_tender():
    sc_result = define_response([], 500, "Error : URL is empty")
    if request.is_json:
        if "url" in request.json:
            sc_url = request.json["url"]
            sc_result = tender_jadwal(sc_url, chrome_driver)
    return jsonify(sc_result)


# Start App
if __name__ == '__main__':
    app.run(debug=False, port=app_port)
