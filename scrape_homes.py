import requests
from datetime import datetime


city_groups = ['Yakima', 'Union Gap', 'Cowiche', 'White Swan', 'Selah', 'Naches', 'Granger', 'Grandview', 'Mabton', 'Toppenish', 'Zillah', 'Wapato', 'Moxee']
res_properties_transferred = []
com_properties_transferred = []


class PropertyList(object):
    def __init__(self, start, end, use):
        self.list = []
        self.start = start
        self.end = end
        self.use = use

    def populate_list(self):
        base_assesors_url = "https://yes.co.yakima.wa.us/AssessorAPI/SaleDetails/"
        type_url_fragment = {"residential": "GetBasicSales/U?salesType=use&saleDateFrom=", "commercial": "GetCommercialSales/?salesType=comm&saleDateFrom="}
        if self.use == '11': #11 is assesor's code for SF residential
            type_url = type_url_fragment["residential"]
            use_url = "&useStr=" + self.use
        else:
            type_url = type_url_fragment["commercial"]
            use_url = None
        mid_url = self.start + "&saleDateTo=" + self.end
        property_url = base_assesors_url + type_url + mid_url
        if use_url: property_url += use_url
        property_url += "&parcelRadio=parcel&situsRadio=parcel&exciseRadio=parcel"
        r = requests.get(property_url).json()['IndividualResults']
        for property_listing in r:
            self.list.append(property_listing)


        """start_url = "https://yes.co.yakima.wa.us/AssessorAPI/SaleDetails/GetBasicSales/U?salesType=use&saleDateFrom="
        mid_url = self.start + "&saleDateTo=" + self.end + "&useStr=" + self.use
        end_url = "&parcelRadio=parcel&situsRadio=parcel&exciseRadio=parcel"
        property_url = start_url + mid_url + end_url
        r = requests.get(property_url).json()['IndividualResults']
        for home in r:
            self.list.append(home)"""


        # res_url = "GetBasicSales/U?salesType=use&saleDateFrom="
        # com_url = "GetCommercialSales/?salesType=comm&saleDateFrom="
        #use_url = "&useStr=" + self.use

class ResProperty(object):
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])
        p_data = self.parcel_lookup
        self.Address = p_data['Address']
        self.Buyer = p_data['Owner']
        self.City = p_data['City']
        self.Seller = self.excise_lookup()

    def parcel_lookup(self):
        base_parcel_url = "https://yes.co.yakima.wa.us/AssessorAPI/ParcelDetails/GetByParcelString/"
        parcel_details_url = base_parcel_url + self.ParcelNumber
        parcel_data = requests.get(parcel_details_url).json()[0]
        property_address = parcel_data['SitusAddress']
        buyer = parcel_data['OwnerName']
        ####pain point, not abstractable w/out too much work####
        city_name = property_address.split()[-1].strip()
        comma_index = city_name.find(',')
        if comma_index != -1:
            city_name = city_name[comma_index:]
        return {'Address': property_address, 'Owner': buyer, 'City': city_name}

    def excise_lookup(self):
        excise_url_base = "https://yes.co.yakima.wa.us/AssessorAPI/SaleDetails/GetExciseRecord/"
        excise_data = requests.get(excise_url_base + str(self.ExciseID))
        return excise_data.json()["GrantorName"]

    def __str__(self):
        return "{0}; ${1:,}; {2}; {3}; {4}".format(self.address, self.SalePrice, self.Buyer, self.Seller, self.ExciseDate)


"""class ComPropertyList(object):
    def __init__(self, start, end):
        self.list = []
        self.start = start
        self.end = end

    def populate_list(self):
        base_url = "https://yes.co.yakima.wa.us/AssessorAPI/SaleDetails/GetCommercialSales/?salesType=comm&saleDateFrom="
        dates_url = self.start + "&saleDateTo=" + self.end
        end_url = "&parcelRadio=parcel&situsRadio=parcel&exciseRadio=parcel"
        property_url = base_url + dates_url + end_url
        r = requests.get(property_url).json()['IndividualResults']
        for commercial_prop in r:
            self.list.append(commercial_prop)


class ComProperty(object):
    def __init__(self, **kwargs):
        for k in kwargs:
            setattr(self, k, kwargs[k])
        base_parcel_url = "https://yes.co.yakima.wa.us/AssessorAPI/ParcelDetails/GetByParcelString/"
        parcel_details_url = base_parcel_url + self.ParcelNumber
        u = requests.get(parcel_details_url).json()[0]
        self.address = u['SitusAddress']
        c = self.address.split(' ')[-1].strip()
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
        return "{0}; {1}; ${2:,}; {3}; {4}; {5}".format(self.address, self.StructureType, self.SalePrice, self.Buyer, self.Seller, self.ExciseDate)




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
    chill_homes.append(a)"""


if __name__ == "__main__":
    outfile = open('outfile.txt', 'w')
    res_transfers = ResPropertyList(start="06/01/2019", end="06/07/2019", use="11")
    outfile.write("RESIDENTIAL PROPERTY")
    outfile.write("\n")
    res_transfers.populate_list()
    for home in res_transfers.list:
        p = ResProperty(**home)
        res_properties_transferred.append(p)
    for town in city_groups:
        for q in res_properties_transferred:
            if q.city == town:
                print(q)
                outfile.write(q.__str__())
                outfile.write("\n")
    outfile.write("\n")
    outfile.write("COMMERCIAL PROPERTY")
    outfile.write("\n")
    transfers = ComPropertyList(start="06/01/2019", end="06/07/2019")
    transfers.populate_list()
    for parcel in transfers.list:
        p = ComProperty(**parcel)
        com_properties_transferred.append(p)
    for town in city_groups:
        for v in com_properties_transferred:
            if v.City == town:
                print(v)
                outfile.write(v.__str__())
                outfile.write("\n")
    outfile.close()




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


"""base_parcel_url = "https://yes.co.yakima.wa.us/AssessorAPI/ParcelDetails/GetByParcelString/"
        parcel_details_url = base_parcel_url + self.ParcelNumber
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
        seller_data = requests.get(seller_url + str(self.ExciseID))
        self.seller = seller_data.json()["GrantorName"]"""




