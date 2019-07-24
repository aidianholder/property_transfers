import requests
import csv


city_groups = ['Yakima', 'Union Gap', 'Cowiche', 'White Swan', 'Selah', 'Naches', 'Granger', 'Grandview', 'Mabton', 'Toppenish', 'Zillah', 'Wapato', 'Moxee']
chill_homes = []


class Property(object):
    def __init__(self, parcel_number):
        self.parcel_number = parcel_number
        base_parcel_url = "https://yes.co.yakima.wa.us/AssessorAPI/ParcelDetails/GetByParcelString/"
        parcel_details_url = base_parcel_url + self.parcel_number
        p = requests.get(parcel_details_url)
        t = p.json()
        u = t[0]
        self.address = u['SitusAddress']
        #cities = ['Yakima', 'Union Gap', 'Cowiche', 'White Swan', 'Selah', 'Naches', 'Granger', 'Grandview',
                       #'Mabton', 'Toppenish', 'Zillah', 'Wapato', 'Moxee']
        c = self.address.split(',')[-1].strip()
        try:
            city_groups.index(str(c))
        except ValueError:
            c = 'Unincorporated'
        self.city = c
        self.buyer = u['OwnerName']


def get_property_base(start, end, use):
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
    chill_homes.append(a)


get_property_base("06/01/2019", "06/30/2019", "11")

outtext = open('prop_transfer.txt', 'w')
outcsv = open('property_transfers.csv', 'w', newline='')


transferwriter = csv.writer(outcsv)
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

outcsv.close()













