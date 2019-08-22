from typing import Dict, Any, Callable

import requests
import dateutil.parser
import argparse
import datetime
import json
import sqlite3
import geojson


class PropertyList(object):
    def __init__(self, start, end, use):
        self.list = []
        self.start = start
        self.end = end
        self.use = use

    def populate_list(self):
        base_assessors_url = "https://yes.co.yakima.wa.us/AssessorAPI/SaleDetails/"
        type_url_fragment = {
            "residential": "GetBasicSales/U?salesType=use&saleDateFrom=",
            "commercial": "GetCommercialSales/?salesType=comm&saleDateFrom="
        }
        # 11 is assessor's code for SF residential###
        if self.use == '11':
            type_url: str = type_url_fragment["residential"]
            use_url = "&useStr=" + self.use
        else:
            type_url = type_url_fragment["commercial"]
            use_url = None
        mid_url = self.start + "&saleDateTo=" + self.end
        property_url = base_assessors_url + type_url + mid_url
        if use_url:
            property_url += use_url
        property_url += "&parcelRadio=parcel&situsRadio=parcel&exciseRadio=parcel"
        r = requests.get(property_url, timeout=10).json()['IndividualResults']
        for property_listing in r:
            self.list.append(property_listing)


class PropertyTransfer(object):
    def __init__(self, **kwargs):
        self.SalePrice = 0
        self.ExciseDate = None
        self.ParcelNumber = ''
        self.ExciseID = None
        self.StructureType = "residential"
        for k in kwargs:
            setattr(self, k, kwargs[k])
        self.SalePrice = int(self.SalePrice)
        p_data = self.parcel_lookup
        self.Address = p_data["Address"]
        self.Buyer = p_data["Owner"]
        self.City = p_data["City"]
        try:
            self.ZipCode = int(p_data['ZipCode'])
        except TypeError:
            self.ZipCode = 0
        self.Seller = self.excise_lookup()
        self.ExciseDate = self.format_excise_date()
        self.ExciseDateString = self.ExciseDate.strftime("%m/%d/%Y")
        self.transaction_id = int(str(self.ExciseDate.toordinal()) + self.ParcelNumber[:6] + self.ParcelNumber[7:])
        self.parcel_int = int(self.ParcelNumber[:6] + self.ParcelNumber[7:])
        geographic_coordinates = self.get_coordinates()
        self.latitude = float(geographic_coordinates['latitude'])
        self.longitude = float(geographic_coordinates['longitude'])


    @property
    def parcel_lookup(self):
        base_parcel_url = "https://yes.co.yakima.wa.us/AssessorAPI/ParcelDetails/GetByParcelNumber/"
        parcel_num_string = self.ParcelNumber[:6] + self.ParcelNumber[7:]
        parcel_details_url = base_parcel_url + parcel_num_string
        parcel_data = requests.get(parcel_details_url, timeout=10).json()
        property_address = parcel_data['SitusAddresses'][0]
        address = property_address['AddressString']
        city = property_address['City']
        zip_c = property_address['ZipCode']
        grantees = parcel_data['OwnerRecords']
        buyer = []
        for grantee in grantees:
            buyer.append(grantee['Name'])
        if len(buyer) > 1:
            buyer_names = ", ".join(buyer)
        else:
            buyer_names = buyer[0]
        return dict(Address=address, City=city, ZipCode=zip_c, Owner=buyer_names)

    def excise_lookup(self):
        excise_url_base = "https://yes.co.yakima.wa.us/AssessorAPI/SaleDetails/GetExciseRecord/"
        excise_data = requests.get(excise_url_base + str(self.ExciseID), timeout=10)
        return excise_data.json()["GrantorName"]

    def format_excise_date(self):
        excise_date_iso = self.ExciseDate
        dt = dateutil.parser.parse(excise_date_iso)
        return dt

    def get_coordinates(self):
        conn = sqlite3.connect("transfers.db")
        cur = conn.cursor()
        parcel_num = int(self.ParcelNumber[:6] + self.ParcelNumber[7:])
        cur.execute("SELECT LONGITUDE, LATITUDE FROM parcel_centroids WHERE ASSESSOR_N=?", (parcel_num,))
        cords = cur.fetchone()
        try:
            return dict(longitude=cords[0], latitude=cords[1])
        except TypeError:
            return dict(longitude=0, latitude=0)

    def load_data(self):
        conn = sqlite3.connect("transfers.db")
        cur = conn.cursor()
        sql = """INSERT INTO transfers(
                        transaction_id, 
                        parcel_number, 
                        address, 
                        city, 
                        zip_code, 
                        seller, 
                        buyer, 
                        sale_price, 
                        excise_date,
                        structure_type,
                        longitude,
                        latitude
                        ) 
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?)"""
        property_values = (self.transaction_id, self.parcel_int, self.Address, self.City, self.ZipCode)
        property_values += (self.Seller, self.Buyer, self.SalePrice, self.ExciseDateString, self.StructureType)
        property_values += (self.longitude, self.latitude)
        try:
            cur.execute(sql, property_values)
            latest_sql = """INSERT INTO latest(transaction_id) VALUES(?)"""
            cur.execute(latest_sql, (self.transaction_id,))
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            print(self.Address + " already transferred on " + self.ExciseDateString)

    def __str__(self):
        base = "{0}; ${1:,}; {2}; {3}; {4}".format(self.Address, self.SalePrice, self.Buyer, self.Seller, self.ExciseDateString)
        if self.StructureType == 'residence':
            return base
        else:
            full = ', '.join([base, self.StructureType])
            return full


def collect_output():
    output = []
    conn = sqlite3.connect("transfers.db")
    cur = conn.cursor()
    cur.execute("SELECT transaction_id FROM transfers")
    tid = cur.fetchall()
    for transaction in tid:
        for row in cur.execute("SELECT * FROM transfers WHERE transaction_id=?", transaction):
            output.append(row)
    return output


def build_print(properties):
    city_groups = {}
    outfile = open('residential.txt', 'w')
    for p in properties:
        city = p[3]
        if city == "":
            city = 'Unincorporated'
        if city in city_groups.keys():
            city_groups[city].append(p)
        else:
            city_groups[city] = []
            city_groups[city].append(p)
    for town in city_groups:
        outfile.write(town)
        outfile.write('\n')
        city_groups[town].sort(key=lambda x: x[8])
        for q in city_groups[town]:
            print(q)
            p_string = "{0}; ${1:,}; {2}; {3}; {4}".format(q[2], q[7], q[5], q[6], q[8])
            outfile.write(p_string)
            outfile.write('\n')
    outfile.write('\n')
    outfile.close()


def commercial_print(properties):
    outfile = open('commercial.txt', 'w')
    for p in properties:
        p_string = "{0}; ${1:,}; {2}; {3}; {4}".format(p[2], p[7], p[5], p[6], p[8], p[9])
        outfile.write(p_string)
        outfile.write('\n')
    outfile.close()

def web_commercial(properties):
    outfile = open('commercial.geojson', 'w')
    features = []
    for p in properties:
        point = geojson.Point((p[10], p[11]))
        f = geojson.Feature(geometry=point, properties={'Address': p[2], 'City': p[3], 'Buyer': p[5], 'Seller': p[6], 'Price': p[7], 'Date': p[8], 'Building Type': p[9]})
        features.append(f)
    commercial_transfers = geojson.FeatureCollection(features)
    dumps = geojson.dumps(commercial_transfers)
    outfile.write(dumps)
    outfile.close()


def build_web(properties):
    no_map = []
    features = []
    outfile = open('transfers.geojson', 'w')
    for p in properties:
        if p[10] == 0:
            no_map.append(p)
        else:
            point = geojson.Point((p[10], p[11]))
            f = geojson.Feature(geometry=point, properties={'Address': p[2], 'City': p[3], 'Buyer': p[5], 'Seller': p[6], 'Price': p[7], 'Date': p[8]})
            features.append(f)
    latest_transfers = geojson.FeatureCollection(features)
    dumps = geojson.dumps(latest_transfers)
    outfile.write(dumps)
    outfile.close()


class OldTransfers(object):
    def __init__(self, file_storage):
        if file_storage is None:
            self.transfers = {}
        else:
            try:
                self.transfers = json.load(open(file_storage, "r"))
            except FileNotFoundError:
                self.transfers = {}

    def record_transfer(self, record_date, record_parcel, record_address):
        if record_date not in self.transfers.keys():
            self.transfers[record_date] = [record_parcel]
        elif record_parcel not in self.transfers[record_date]:
            self.transfers[record_date].append(record_parcel)
        else:
            report_string = " ".join([record_address, 'already transferred on', record_date])
            print(report_string)

    def purge_oldest(self):
        old_dates = []
        threshold = datetime.date.today() - datetime.timedelta(days=90)
        # can't delete wile looping through dict, so using this instead ###
        for k in self.transfers.keys():
            kd = datetime.datetime.strptime(k, "%Y%m%d").date()
            if kd < threshold:
                old_dates.append(k)
        for d in old_dates:
            del self.transfers[d]

    def write_storage(self, property_type):
        output_file_name = "".join([property_type, datetime.date.today().strftime("%Y%m%d"), ".json"])
        output = json.dumps(self.transfers, sort_keys=True, indent=4)
        outfile = open(output_file_name, "w")
        outfile.write(output)
        outfile.close()

    def __str__(self):
        json.dumps(self.transfers, sort_keys=True, indent=4)


def run_residential(start, end):
    # city_groups = {}
    # outfile = open('residential.txt', 'w')
    res_transfers = PropertyList(start=start, end=end, use="11")
    res_transfers.populate_list()
    for home in res_transfers.list:
        p = PropertyTransfer(**home)
        p.load_data()
    collect_output()


def run_commercial(start, end):
    com_transfers = PropertyList(start=start, end=end, use=None)
    com_transfers.populate_list()
    for parcel in com_transfers.list:
        p = PropertyTransfer(**parcel)
        p.load_data()
    z = collect_output()
    build_print(z)
    build_web(z)


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("start")
    # parser.add_argument("end")
    # parser.add_argument("old")
    # args = parser.parse_args()
    # run_residential(, args.end)
    # run_residential('07/15/2019', '07/16/2019')
    # run_commercial('07/01/2019', '07/15/2019', None)
    z = collect_output()
    build_web(z)