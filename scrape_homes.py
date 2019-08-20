from typing import Dict, Any, Callable

import requests
import dateutil.parser
import argparse
import datetime
import json


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

    def __str__(self):
        base = "{0}; ${1:,}; {2}; {3}; {4}".format(self.Address, self.SalePrice, self.Buyer, self.Seller, self.ExciseDateString)
        if self.StructureType:
            full = ', '.join([base, self.StructureType])
            return full
        else:
            return base


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


def run_residential(start, end, old):
    city_groups = {}
    outfile = open('residential.txt', 'w')
    res_transfers = PropertyList(start=start, end=end, use="11")
    res_transfers.populate_list()
    pr = OldTransfers(old)
    for home in res_transfers.list:
        p = PropertyTransfer(**home)
        pr.record_transfer(p.ExciseDate.strftime("%Y%m%d"), p.ParcelNumber, p.Address)
        if p.City in city_groups.keys():
            city_groups[p.City].append(p)
        else:
            city_groups[p.City] = []
            city_groups[p.City].append(p)
    pr.purge_oldest()
    pr.write_storage("residential")
    for town in city_groups.keys():
        outfile.write(town)
        outfile.write('\n')
        city_groups[town].sort(key=lambda x: x.ExciseDate)
        for q in city_groups[town]:
            print(q)
            outfile.write(q.__str__())
            outfile.write('\n')
        outfile.write('\n')
    outfile.close()


def run_commercial(start, end, old):
    outfile = open('commercial.txt', 'w')
    com_transfers = PropertyList(start=start, end=end, use=None)
    com_transfers.populate_list()
    com_properties_transferred = []
    pr = OldTransfers(old)
    for parcel in com_transfers.list:
        p = PropertyTransfer(**parcel)
        pr.record_transfer(p.ExciseDate.strftime("%Y%m%d"), p.ParcelNumber, p.Address)
        com_properties_transferred.append(p)
    pr.purge_oldest()
    pr.write_storage("commercial")
    com_properties_transferred.sort(key=lambda x: x.ExciseDate)
    for v in com_properties_transferred:
        print(v)
        outfile.write(v.__str__())
        outfile.write("\n")
    outfile.close()


if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument("start")
    # parser.add_argument("end")
    # parser.add_argument("old")
    # args = parser.parse_args()
    # run_residential(, args.end)
    run_residential('07/01/2019', '07/15/2019', None)
    run_commercial('07/01/2019', '07/15/2019', None)
