from csv import DictReader, DictWriter
from pyoscar import OSCARClient

client = OSCARClient(env='prod')

idx = 0

outfile = open("stations.csv", "w", newline="")
field_names = ['RegionalAssociation', 'Country', 'Station', 'OSCARName',
               'WMONumber', 'WIGOSID', 'OSCARPrimaryWSI', 'latitude',
               'longitude', 'elevation', 'link']

writer = DictWriter(outfile, fieldnames=field_names)
writer.writeheader()
OSCAR_URL="https://oscar.wmo.int/surface/#/search/station/stationReportDetails/"

country_codes = {}
countries = {}

with open("countries.csv") as fh:
    reader = DictReader(fh)
    for row in reader:
        country_codes[row.get('country')] = row.get('code')

with open("clino_all_stations_wigos.txt", encoding="utf8") as fh:
    rows = DictReader(fh, delimiter=" ")
    for row in rows:
        station = {}
        wsi = row.get("WIGOSID","")
        tsi = row.get("WMONumber", "")
        if wsi in ("X-XXXXX-X-XXXXX", "", "NA", None):
            wsi = f"0-20000-0-{tsi}"

        # Australia haven't updated OSCAR SURFACE to use new WSIs
        if row.get("Country","") == "Australia":
            wsi = f"0-20000-0-{tsi}"

        if tsi in ("", "NA","XXXXX",None):
            station = {}
        else:
            try:
                station = client.get_station_report(wsi, format_="XML", summary=True)
            except Exception as e:
                print(f"Error fetching station {tsi}/{wsi}: {e}")
                print(station)
                raise

            if station.get("wigos_station_identifier","") == "":  # station not found
                print(f"Station {tsi} not found")
                iso3 = country_codes.get(row.get("Country",""),"")
                # try with country code rather than 20000 series
                wsi = f"{0}-{iso3}-{0}-{tsi}"
                try:
                    station = client.get_station_report(wsi, format_="XML", summary=True)
                except Exception as e:
                    print(f"Error fetching station {tsi}/{wsi}: {e}")

                if station.get("wigos_station_identifier", "") == "":
                    # get country code
                    countries[row.get("Country")] = row.get("Country")

        row['OSCARName'] = station.get('station_name','').title()
        row['OSCARPrimaryWSI'] = station.get('wigos_station_identifier', '')
        row['latitude'] = station.get('latitude','')
        row['longitude'] = station.get('longitude','')
        row['elevation'] = station.get('elevation','')

        if row['OSCARPrimaryWSI'] != "":
            row['link'] = f"{OSCAR_URL}{row['OSCARPrimaryWSI']}"
        else:
            row['link'] = ""

        try:
            writer.writerow(row)
        except Exception as e:
            print(f"Error {e}")
            print(row)

outfile.close()

#with open("countries2.csv","w", newline="") as fh:
#    writer = DictWriter(fh,fieldnames=["country","code"])
#    writer.writeheader()
#    for c,v in countries.items():
#        writer.writerow({"country": c, "code": v})