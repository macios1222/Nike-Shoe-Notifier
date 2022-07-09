from bs4 import BeautifulSoup
import requests
from datetime import datetime
import json
import re
import pandas as pd
import time
from twilio.rest import Client 

now = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
f = open(f'logs/{now}_app.log', "w+")
f.write(f'Starting program at: {now}')
print(f'Starting program at: {now}')
config_file = open("config.json", "r")
config = json.load(config_file)
banner = """


███▄▄▄▄      ▄████████ ███▄▄▄▄   
███▀▀▀██▄   ███    ███ ███▀▀▀██▄ 
███   ███   ███    █▀  ███   ███ 
███   ███   ███        ███   ███ 
███   ███ ▀███████████ ███   ███ 
███   ███          ███ ███   ███ 
███   ███    ▄█    ███ ███   ███ 
 ▀█   █▀   ▄████████▀   ▀█   █▀  
                                 

                            
"""

print(banner)


def get_available_sizes(site):
    try:
        page = requests.get(site)
        soup = BeautifulSoup(page.content, 'html.parser')
        model_name = soup.find(id="pdp_product_title").get_text()
        price = soup.find(class_="product-price css-11s12ax is--current-price css-tpaepq").get_text()
        data = json.loads(soup.find('script',text=re.compile('INITIAL_REDUX_STATE')).text.replace('window.INITIAL_REDUX_STATE=','')[0:-1])  
        product_id = soup.find(class_="description-preview__style-color ncss-li").get_text().strip("Styl: ")
        skus = data['Threads']['products'][product_id]['skus']
        sizes = data['Threads']['products'][product_id]['availableSkus']
        df_skus = pd.DataFrame(skus)
        sizes = pd.DataFrame(sizes)
        av_sizes = df_skus.merge(sizes[['skuId','available']], on ='skuId')
        li = []
        for sizee in (av_sizes['localizedSize']):
            li.append(sizee)
        return li, price, model_name
    except:
        pass
    
    return [4], "5", "NONE"

def send_sms(data):
    try:
        price = data[0]
        model_name = data[1]
        size = data[2]
        link = data[3]

        account_sid = config["account_sid"]
        auth_token = config["auth_token"]
        client = Client(account_sid, auth_token)    
        phone_number = config["phone_number"]

        message = client.messages.create(  
                                messaging_service_sid=config["messaging_service_sid"], 
                                body=f'Model: {model_name}, \nPrice: {price}, \nAvailable size: {size}, \n\nLink: {link}',      
                                to=phone_number
                            )
        now = str(datetime.now()) 
        f.write(now + f' Sent SMS to: {phone_number}' + "\n")
        print(now + f' Sent SMS to: {phone_number}')
    except Exception as e:
        print(e)



def main_loop():
    print(config["links"])
    sites = ((config["links"]).replace(";", " ")).split()
    sizes = ((config["sizes"]).replace(";", " ")).split()
    while True:
        for site in sites:
            now = str(datetime.now())
            f.write(now + " Checking: " + site + "\n")
            print(now + " Checking: " + site)
            data = get_available_sizes(site)
            av_sizes = data[0]
            price = data[1]
            model = data[2]
            for size in sizes:
                if size in av_sizes:
                    send_sms([price, model, size, site])
                    now = str(datetime.now())
                    f.write(now + f" Size: {size} Is available, Link: " + site + "\n")
                    print(now + f" Size: {size} Is available, Link: " + site)
            now = str(datetime.now())
            f.write(now + " Checked: " + site + "\n")
            print(now + " Checked: " + site + " Sizes: ", sizes)
            time.sleep(1)
        f.write("Checked all shoes, waiting 5 seconds" + "\n")
        print("Checked all shoes, waiting 5 seconds")
        time.sleep(5)

main_loop()