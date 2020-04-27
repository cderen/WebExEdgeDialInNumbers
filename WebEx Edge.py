from bs4 import BeautifulSoup
import requests
import re
import csv

def parse_soup(customer, soup):
    # define regex for compliling dial in numbers URL
    pattern1 = re.compile("(var theUrl =) \'(.*)\'")
    pattern2 = re.compile("(/webcomponents)(.*)")
    pattern3 = re.compile("(siteurl=)(.*)")

    url1 = re.search(pattern1, soup.text).group(2)
    url2 = re.search(pattern2, soup.text).group(1) + re.search(pattern2, soup.text).group(2).replace("?'", "?")
    url3 = re.search(pattern3, soup.text).group(1) + re.search(pattern3, soup.text).group(2).replace("';", "")

    edge_url = requests.get(f'https://{customer}.webex.com' + url1 + url2 + url3, timeout=2)
    edge_soup = BeautifulSoup(edge_url.content, 'html.parser')

    dial_in_numbers = []

    for tb in edge_soup.find_all('table'):
        for row in tb.find_all('td'):
            pair = []
            if 'mc-txt-region' in str(row):
                country = (row.text).replace('\n', '').strip()
            if 'mc-txt-phoneNumber' in str(row):
                number = row.text.replace('\n', '').strip()
                pair = [country, number]
                dial_in_numbers.append(pair)

    return dial_in_numbers


def generate_axl_file(dial_in_numbers, route_list):
    file_name = "webedxedge_route_patterns.tsv"
    with open(file_name, 'w') as file:

        rp_dict = {"Route Pattern": '',
                   "Partition": "US LD Globalize and Route",
                   "Description": '',
                   "Dial Plan Name": 'NANP',
                   "Route Filter": '',
                   "Route List": '',
                   "Route or Block": "Route",
                   "Provide Dial Tone": "TRUE",
                   "Use Calling Party's Ext Mask": 'TRUE',
                   "Called Party Prefix Digits": '',
                   "Calling Party Transform Mask": '',
                   "Calling Line Presentation": '',
                   "Calling Name Presentation": '',
                   "Network Location": 'OffNet',
                   "Authorization Level Required": '0',
                   "Authorization Code Required": 'FALSE',
                   "Immediate Match": 'TRUE'
                   }

        fieldnames = []
        for k in rp_dict.keys():
            fieldnames.append(k)


        writer = csv.DictWriter(file, fieldnames=fieldnames ,delimiter='\t')
        writer.writeheader()

        print("\nCalling from , Call-in Numbers\n--------------------------------------------")
        for i in dial_in_numbers:
            print(i[0], ",", i[1])
            if str(i[1]).startswith('+'):
                pattern = "\\" + i[1]
            else:
                pattern = '\\+' + i[1]
            pattern = pattern.replace(" ", "").replace("-", "")

            rp_dict["Route Pattern"] = pattern
            rp_dict["Description"] = 'WebEx edge for ' + i[0]
            rp_dict["Route List"] = route_list

            writer.writerow(rp_dict)
        print(f"\nSucessfully created {file_name} AXL input file. Some patterns may need to be adjusted with proper country codes.")


def main():
    customer = input("Enter customer webex site name:")
    route_list = input("Enter Route List name for webex edge audio:")

    try:
        customer_url = requests.get(f'https://{customer}.webex.com/{customer}/globalcallin.php',timeout=2)
        soup = BeautifulSoup(customer_url.content, 'html.parser')
        dial_in_numbers = parse_soup(customer, soup)
        generate_axl_file(dial_in_numbers, route_list)
    except:
        print("Webex site does not exist")

if __name__ == '__main__':
    main()
