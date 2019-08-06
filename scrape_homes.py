from typing import Dict, Any, Callable

import requests
import dateutil.parser
import argparse
import datetime


city_groups = ['Yakima', 'Union Gap', 'Cowiche', 'White Swan', 'Selah', 'Naches', 'Granger', 'Grandview', 'Mabton', 'Toppenish', 'Zillah', 'Wapato', 'Moxee']


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
        for k in kwargs:
            setattr(self, k, kwargs[k])
        self.SalePrice = int(self.SalePrice)
        p_data: Callable[[], Dict[str, Any]] = self.parcel_lookup()
        self.Address = p_data['Address']
        self.Buyer = p_data['Owner']
        self.City = p_data['City']
        self.Seller = self.excise_lookup()
        self.ExciseDate = self.format_excise_date()
        self.ExciseDateString = self.ExciseDate.strftime("%m/%d/%Y")

    def parcel_lookup(self):
        base_parcel_url = "https://yes.co.yakima.wa.us/AssessorAPI/ParcelDetails/GetByParcelString/"
        parcel_details_url = base_parcel_url + self.ParcelNumber
        parcel_data = requests.get(parcel_details_url, timeout=10).json()[0]
        property_address = parcel_data['SitusAddress']
        buyer = parcel_data['OwnerName']
        # pain point, not abstract-able w/out too much work####
        # commercial property has simple space between street address and city###
        city_name = property_address.split()[-1].strip()
        # residential property usually has comma between address and city###
        comma_index = city_name.find(',')
        if comma_index != -1:
            city_name = city_name[comma_index:]
        return {'Address': property_address, 'Owner': buyer, 'City': city_name}

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
        if self.StructureType != -1:
            full = ', '.join([base, self.StructureType])
            return full
        else:
            return base



def run_residential(start, end):
    outfile = open('residential.txt', 'w')
    res_transfers = PropertyList(start=start, end=end, use="11")
    res_transfers.populate_list()
    properties_transferred = []
    for home in res_transfers.list:
        p = PropertyTransfer(**home)
        properties_transferred.append(p)
    for town in city_groups:
        for q in properties_transferred:
            if q.City == town:
                print(q)
                outfile.write(q.__str__())
                outfile.write('\n')
        outfile.write("\n")


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
    run_commercial('06/01/2019', '06/15/2019')