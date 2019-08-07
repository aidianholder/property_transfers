from typing import Dict, Any, Callable

import requests
import dateutil.parser
from requests.adapters import HTTPAdapter
import requests.packages.urllib3.util.retry as Retry
import argparse
import datetime


city_name_lookup = ['Yakima', 'Union Gap', 'Cowiche', 'White Swan', 'Harrah', 'Selah', 'Sunnyside', 'Naches', 'Granger', 'Grandview', 'Mabton', 'Toppenish', 'Tieton', 'Zillah', 'Wapato', 'Moxee']


class PropertyList(object):
    def __init__(self, start, end, use):
        self.list = []
        self.start = start
        self.end = end
        self.use = use

    def populate_list(self):
        base_assessors_url = "https://yes.co.yakima.wa.us/AssessorAPI/SaleDetails/"
        type_url_fragment = {"residential": "GetBasicSales/U?salesType=use&saleDateFrom=", "commercial": "GetCommercialSales/?salesType=comm&saleDateFrom="}
        # 11 is assessor's code for SF residential###
        if self.use == '11':
            type_url = type_url_fragment["residential"]
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
        self.StructureType = None
        for k in kwargs:
            setattr(self, k, kwargs[k])
        self.SalePrice = int(self.SalePrice)
        p_data: Callable[[], Dict[str, Any]] = self.parcel_lookup
        self.Address = p_data["Address"]
        self.Buyer = p_data["Owner"]
        self.City = p_data["City"]
        self.Seller = self.excise_lookup()
        self.ExciseDate = self.format_excise_date()
        self.ExciseDateString = self.ExciseDate.strftime("%m/%d/%Y")

    @property
    def parcel_lookup(self):
        base_parcel_url = "https://yes.co.yakima.wa.us/AssessorAPI/ParcelDetails/GetByParcelString/"
        parcel_details_url = base_parcel_url + self.ParcelNumber
        parcel_data = requests.get(parcel_details_url, timeout=10).json()[0]
        property_address = parcel_data['SitusAddress']
        buyer = parcel_data['OwnerName']
        # pain point, not abstract-able w/out too much work####
        # residential property usually has comma between address and city###
        # commercial property has simple space between street address and city###
        comma_index = property_address.find(', ')
        if comma_index != -1:
            city_name = property_address.split(', ')[-1].strip()
        else:
            city_name = property_address.split()[-1].strip()
        if city_name == "Gap":
            city_name = "Union Gap"
        elif city_name == "Swan":
            city_name = "White Swan"
        if city_name not in city_name_lookup:
            city_name = 'Unincorporated'
        return {'Address': property_address, 'Owner': buyer, 'City': city_name}

        # city_name = property_address.split(', ')

        # city_name = property_address.split()[-1].strip()

        # comma_index: object = city_name.find(', ')
        # if comma_index != -1:
        #    city_name = city_name[comma_index:]
        # if city_name not in city_name_lookup:
        #    city_name = 'Unincorporated'
        # return {'Address': property_address, 'Owner': buyer, 'City': city_name}

    def excise_lookup(self):
        excise_url_base = "https://yes.co.yakima.wa.us/AssessorAPI/SaleDetails/GetExciseRecord/"
        excise_data = requests.get(excise_url_base + str(self.ExciseID), timeout=10)
        return excise_data.json()["GrantorName"]

    def format_excise_date(self):
        excise_date_iso = self.ExciseDate
        dt = dateutil.parser.parse(excise_date_iso)
        return dt

    def __str__(self):
        base = "{0}; ${1:,}; {2}; {3}; {4}".format(self.Address, self.SalePrice, self.Buyer, self.Seller, self.ExciseDateString)
        if self.StructureType:
            full = ', '.join([base, self.StructureType])
            return full
        else:
            return base


def run_residential(start, end):
    city_groups = {}
    outfile = open('residential.txt', 'w')
    res_transfers = PropertyList(start=start, end=end, use="11")
    res_transfers.populate_list()
    for home in res_transfers.list:
        p = PropertyTransfer(**home)
        if p.City in city_groups.keys():
            city_groups[p.City].append(p)
        else:
            city_groups[p.City] = []
            city_groups[p.City].append(p)
    for town in city_groups.keys():
        outfile.write(town)
        outfile.write('\n')
        for q in city_groups[town]:
            print(q)
            outfile.write(q.__str__())
            outfile.write('\n')
        outfile.write('\n')


        #properties_transferred.append(p)
    #for town in city_groups:
    #    for q in properties_transferred:
    #        if q.City == town:
     #           print(q)
      #          outfile.write(q.__str__())
       #         outfile.write('\n')
        #outfile.write("\n")


def run_commercial(start, end):
    outfile = open("commercial.txt", 'w')
    com_transfers = PropertyList(start=start, end=end, use=None)
    com_transfers.populate_list()
    com_properties_transferred = []
    for parcel in com_transfers.list:
        p = PropertyTransfer(**parcel)
        com_properties_transferred.append(p)
    for town in city_groups:
        for v in com_properties_transferred:
            if v.City == town:
                print(v)
                outfile.write(v.__str__())
                outfile.write("\n")
    outfile.close()

if __name__ == "__main__":
    #parser = argparse.ArgumentParser()
    #parser.add_argument("start")
    #parser.add_argument("end")
    #args = parser.parse_args()
    #run_residential(, args.end)
    run_residential('07/02/2019', '07/04/2019')
    #run_commercial('07/01/2019', '07/15/2019')