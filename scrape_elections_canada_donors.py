
# coding: utf-8

# In[15]:

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from time import sleep
from itertools import product
import json
import traceback
import os
import datetime

import sys
assert sys.version[:3] == "2.7", "This script uses Selenium, which only works in Python 2.7.X"


# In[10]:

empty = '[]'
for fn in ['done.json', 'errors.json', 'to_drilldown.json']:
    if not os.path.isfile(fn):
        with open(fn, 'w+') as f:
            f.write(empty)


# In[11]:

scrape_postal_codes = True
use_dates = True
date_offsetin_days = 12
download_folder_path = "D:/Downloads"


# In[22]:

today = datetime.date.today()
from_date = today + datetime.timedelta(days=-12)
from_date = from_date.strftime("%Y-%m-%d")
to_date = today.strftime("%Y-%m-%d")


# In[12]:

master_to_do = []

entities = ["1", "2", "3", "5", "6"]
provinces = ["48", "59", "46", "13", "10", "61", "12", "62", "35", "11", "24", "47", "60"]
major_parties = ["1", "3", "10", "28"]
minor_parties = ["32", "22", "26", "21", "33", "5", "24", "30", "25", "9", "13",
                 "38", "23", "41", "34", "39", "29", "36", "40", "31", "37"]
donation_ranges = [[0.01, 50], [50.01, 200], [200.01, 1000], [1000.01, 9000000000]]

for entity, party in product(entities, minor_parties):
    master_to_do.append([entity, "-1", party, [0.01, 9000000000]])

for entity, province, party, range_ in product(entities, provinces, major_parties, donation_ranges):
    master_to_do.append([entity, province, party, range_]) #, range_])

with open('master_to_do.json', 'w+') as f:
    f.write(json.dumps(master_to_do))


# In[13]:

def save_jsons():
    with open('to_do.json', 'w+') as f:
        f.write(json.dumps(to_do))
    with open('done.json', 'w+') as f:
        f.write(json.dumps(done))
    with open('errors.json', 'w+') as f:
        f.write(json.dumps(errors))
    with open('to_drilldown.json', 'w+') as f:
        f.write(json.dumps(to_drilldown))
    f.close()


# In[14]:

def update_to_do():
    """Reloads to_do in case user has changed it during run."""
    global to_do
    with open('to_do.json', 'r') as f:
        to_do = json.loads(f.read())
    try:
        to_do.remove([entity, province, party, range_])
    except:
        pass
        


# In[23]:

stop_everything = False

if not use_dates:
    print "Remaining: ",

while not stop_everything:
    f.close() # I was getting a too many open files error and I'm not sure why

    if not use_dates:
        with open('to_do.json', 'r') as f:
            to_do = json.loads(f.read())
        with open('done.json', 'r') as f:
            done = json.loads(f.read())
        with open('errors.json', 'r') as f:
            errors = json.loads(f.read())
        with open('to_drilldown.json', 'r') as f:
            to_drilldown = json.loads(f.read())

        entity, province, party, range_ = to_do[0]
        dolstart = str(range_[0])
        dolend = str(range_[1])
        if dolstart == 0.01 and dolend > 1000:
            dolname = 'all'
        else:
            dolname = dolend
        print len(to_do),
    try:
        driver = webdriver.Chrome()
        driver.get("http://www.elections.ca/WPAPPS/WPF/EN/CCS?returntype=1")
        try:
            element = WebDriverWait(driver, 10).until(
                          EC.presence_of_element_located((By.ID, "buttonFind")))
        except:
            raise Exception, 'Landing page did not load in time'

        if not use_dates:
            driver.find_element_by_id('rbAsAudited').click()
            # driver.find_element_by_id('rbAsSubmitted').click()
            sel = Select(driver.find_element_by_id('entities'))
            sel.select_by_value(entity)
            sel = Select(driver.find_element_by_id('province'))
            sel.select_by_value(province)
            sel = Select(driver.find_element_by_id('partyList'))
            sel.select_by_value(party)
            el = driver.find_element_by_id('rangefrom')
            el.send_keys(dolstart)
            el = driver.find_element_by_id('rangeto')
            el.send_keys(dolend)
        else:
            driver.find_element_by_id('rbAsAudited').click()
            driver.find_element_by_id('selectallentities').click()
            sel = Select(driver.find_element_by_id('province'))
            sel.select_by_value("-1")
            driver.find_element_by_id('selectallparties').click()
            el = driver.find_element_by_id('FromDate')
            el.send_keys(from_date)
            el = driver.find_element_by_id('ToDate')
            el.send_keys(to_date)
        
        driver.find_element_by_id('buttonFind').click()

        try:
            element = WebDriverWait(driver, 10).until(
                          EC.presence_of_element_located((By.ID, "FooterLinklnk")))
        except:
            errtxt = str(sys.exc_type) + str(sys.exc_value)
            raise Exception, errtxt
        
        stop_this_loop = False
        exceeded = False
                
        soup = BeautifulSoup(driver.page_source)
        if soup.decode('utf-8').find('There are no contributions for your search criteria.') != -1:
            stop_this_loop = True
        elif soup.decode('utf-8').find('Max records exceeded.') != -1:
            exceeded = True
            stop_this_loop = True
                
        if not stop_this_loop:
            
            if not scrape_postal_codes:
                driver.find_element_by_id('DTDownloadLink').click()

                try:
                    element = WebDriverWait(driver, 10).until(
                                  EC.presence_of_element_located((By.ID, "downloadFormatDiv")))
                except:
                    errtxt = str(sys.exc_type) + str(sys.exc_value)
                    raise Exception, errtxt

                sel = Select(driver.find_element_by_id('dloptn'))
                sel.select_by_value("1")
                driver.find_element_by_id('DownloadButton').click()

                csv_path = os.path.join(download_folder_path, 'downloadreport.csv')

                for i in range(30):
                    if os.path.isfile(csv_path):
                        break
                    else:
                        sleep(1)
                        if i == 29:
                            raise Exception, 'Downloader timed out'

                new_path = csv_path.replace('downloadreport', 
                                            'donor_download_{}_{}_{}_{}.tsv'.format(entity, province, party, dolname))

                os.rename(csv_path, new_path)

            else:

                results = {}
                for column in ['contr_full_nme', 'pltcl_prty_nme', 'contr_givn_to_nme', 'recvd_dt', 'event_end_dt', 'financl_rpt_nme',
                               'contr_class_orgnl_nme', 'contr_mon_amt', 'contr_non_mon_amt', 'contr_thrgh_org_nme', 'aifullname',
                               'city', 'province', 'postalcode']:
                    results[column] = []


                while not stop_this_loop:
                        table = soup.find("table", { "id" : "contribrpt" })
                        rownum = -1
                        for row in table.findAll("tr"):
                            cells = row.findAll("td")
                            if len(cells) == 10:
                                rownum += 1
                                alinkn = 'addresslink'+str(rownum)
                                for cell in cells:
                                    header = cell.attrs['headers'][0]
                                    results[header].append(cell.text.strip())
                                    if header == 'contr_full_nme':
                                        try:
                                            assert alinkn == cell.contents[1].attrs['id'] # find, e.g. addresslink199
                                        except:
                                            raise Exception, 'alinkn did not match id attribute'
                                el = driver.find_element_by_id(alinkn)
                                el.click()
                                for timer in range(20): # to wait for page refresh to complete
                                    success = False
                                    try:
                                        el = driver.find_element_by_id('closelink1')
                                        assert el.get_attribute('href').find(alinkn) != -1
                                        success = True
                                    except:
                                        sleep(0.5)
                                    if success:
                                        break
                                    if timer == 19:
                                        raise Exception, 'Page refresh timed out.'
                                soup2 = BeautifulSoup(driver.page_source.encode('utf-8'))
                                fieldset = soup2.find("fieldset", {'id': 'addrssinfo2'})
                                for div in fieldset.findAll("div"):
                                    subhead = div.find("input").attrs['id']
                                    results[subhead].append(div.find("input").attrs['value'])
                        if str(soup).find("id=\"nextpagelink\">Next 200</a>") != -1:
                            driver.find_element_by_id('closelink1').click()
                            sleep(0.5)
                            driver.find_element_by_id('nextpagelink').click()
                            sleep(3)
                            try:
                                element = WebDriverWait(driver, 10).until(
                                              EC.presence_of_element_located((By.ID, "sortlink9")))
                            except:
                                raise Exception, "Next page did not load in time"
                        else:
                            stop_this_loop = True
                if len(results['contr_full_nme']) > 0:
                    df = pd.DataFrame(results)
                    if use_dates:
                        fn = "donors_update_{}_{}.tsv".format(from_date, to_date)
                    else:
                        fn = 'donors_{}_{}_{}_{}.tsv'.format(entity, province, party, dolname)
                    
                    df.to_csv(index=False, sep='\t', encoding='utf-8')
        if not use_dates:
            update_to_do()
            if exceeded:
                to_drilldown.append([entity,province,party, range_])
            else:
                done.append([entity, province, party, range_])
        driver.close()
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        errtxt = "{}: {} {}".format(exc_traceback.tb_lineno, sys.exc_type, sys.exc_value)
        if not use_dates:
            update_to_do()
            errors.append([[entity, province, party, range_], errtxt])
            driver.close()
        else:
            print errtxt
    if not use_dates:
        save_jsons()

    if len(to_do) == 0:
        stop_everything = True


# In[ ]:



