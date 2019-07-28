import requests
import csv


city_groups = ['Yakima', 'Union Gap', 'Cowiche', 'White Swan', 'Selah', 'Naches', 'Granger', 'Grandview', 'Mabton', 'Toppenish', 'Zillah', 'Wapato', 'Moxee']
properties_transferred = []


class PropertyList(object):
    def __init__(self, start, end, use):
        self.list = []
        self.start = start
        self.end = end
        self.use = use

    def populate_list(self):
        start_url = "https://yes.co.yakima.wa.us/AssessorAPI/SaleDetails/GetBasicSales/U?salesType=use&saleDateFrom="
        mid_url = self.start + "&saleDateTo=" + self.end + "&useStr=" + self.use
        end_url = "&parcelRadio=parcel&situsRadio=parcel&exciseRadio=parcel"
        property_url = start_url + mid_url + end_url
        r = requests.get(property_url).json()['IndividualResults']
        for home in r:
            self.list.append(home)


class ResProperty(object):
    def __init__(self, parcel_number, exciseid, excisedate, saleprice):
        self.parcel_number = parcel_number
        self.excise_id = exciseid
        self.excise_date = excisedate
        self.price = saleprice
        base_parcel_url = "https://yes.co.yakima.wa.us/AssessorAPI/ParcelDetails/GetByParcelString/"
        parcel_details_url = base_parcel_url + self.parcel_number
        u = requests.get(parcel_details_url).json()[0]
        self.address = u['SitusAddress']
        c = self.address.split(',')[-1].strip()
        try:
            city_groups.index(str(c))
        except ValueError:
            c = 'Unincorporated'
        self.city = c
        self.buyer = u['OwnerName']
        seller_url = "https://yes.co.yakima.wa.us/AssessorAPI/SaleDetails/GetExciseRecord/"
        seller_data = requests.get(seller_url + str(self.excise_id))
        self.seller = seller_data.json()["GrantorName"]

    def __str__(self):
        return "{0}; {1:,}; {2}; {3}".format(self.address, self.price, self.buyer, self.seller)


class ComProperty(object):
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])
        base_parcel_url = "https://yes.co.yakima.wa.us/AssessorAPI/ParcelDetails/GetByParcelString/"
        parcel_details_url = base_parcel_url + self.ParcelNumber
        u = requests.get(parcel_details_url).json()[0]
        self.address = u['SitusAddress']
        c = self.address.split(',')[-1].strip()
        try:
            city_groups.index(str(c))
        except ValueError:
            c = 'Unincorporated'
        self.City = c
        self.Buyer = u['OwnerName']
        seller_url = "https://yes.co.yakima.wa.us/AssessorAPI/SaleDetails/GetExciseRecord/"
        seller_data = requests.get(seller_url + str(self.ExciseID))
        self.Seller = seller_data.json()["GrantorName"]

    def __str__(self):
        return "{0}"




"""def get_property_base(start, end, use):
    start_url = "https://yes.co.yakima.wa.us/AssessorAPI/SaleDetails/GetBasicSales/U?salesType=use&saleDateFrom="
    mid_url = start + "&saleDateTo=" + end + "&useStr=" + use
    end_url = "&parcelRadio=parcel&situsRadio=parcel&exciseRadio=parcel"
    property_url = start_url + mid_url + end_url
    r = requests.get(property_url)
    j = r.json()['IndividualResults']
    for home in j:
        build_home(home, use)


def build_home(home, use_code):
    a = Property(home["ParcelNumber"])
    a.excise_id = home["ExciseID"]
    a.price = home["SalePrice"]
    a.excise_date = home["ExciseDate"]
    a.use_code = use_code
    seller_url = "https://yes.co.yakima.wa.us/AssessorAPI/SaleDetails/GetExciseRecord/"
    seller_data = requests.get(seller_url + str(a.excise_id))
    seller = seller_data.json()["GrantorName"]
    a.seller = seller
    #attrs = vars(a)
    #print(', '.join("%s: %s" % item for item in attrs.items()))
    chill_homes.append(a)"""


#get_property_base("06/01/2019", "06/30/2019", "11")

if __name__ == "__main__":



"""    transfers = PropertyList(start="06/01/2019", end="06/05/2019", use="11")
    transfers.populate_list()
    for parcel in transfers.list:
        p = Property(parcel['ParcelNumber'], parcel['ExciseID'], parcel['ExciseDate'], parcel['SalePrice'])
        properties_transferred.append(p)
    for town in city_groups:
        print(town)
        for q in properties_transferred:
            if q.city == town:
                print(q)"""



"""transferwriter = csv.writer(outcsv)
for group in city_groups:
    print(group)
    outtext.write(group + '\n')
    outcsv.write(group + '\n')
    for home_sold in chill_homes:
        if home_sold.city == group:
            buyer = home_sold.buyer
            address = home_sold.address
            seller = home_sold.seller
            price = int(home_sold.price)
            #transaction_string = f"{buyer} bought {address} for ${price} from {seller}"
            #outtext.write(transaction_string + '\n')
            transferwriter.writerow([address, str(price), buyer, seller])
            #print(transaction_string)
    #print('\n')

outcsv.close()"""













