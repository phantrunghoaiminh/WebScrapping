#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from __future__ import print_function, division

"""
Created on Sat Apr 29 17:34:27 2017

@author: minh
"""

#------------------------------------------------------------------------------
# WEB SCRAPPING - UPWORK PROJECT - CHROME EXTENSION PAGE
#------------------------------------------------------------------------------

"""
This project will go to Chrome extension website, make a extensions search with
a search term (e.g. Youtube, Facebook, etc.), then extract some extensions'
information (details are in below).

Chrome extension URL: https://chrome.google.com/webstore/category/extensions

Things to do:

1. note if firefox or chrome [Done]
2. list of all extensions titles [Done]
3. link to extension page [Done]
4. search rank position for given search term [__???__]
5. numbers of active users [Done]
6. size [Done]
7. version [Done]
8. date of last update [Done]
9. # of reviews and overall rating [Done]
10. developer/program website link [Done]
11. developer/contact email [__???__]
"""

#------------------------------------------------------------------------------
# Libraries
#------------------------------------------------------------------------------

# Data handling packages
import pandas as pd

# Web scrapping packages
from bs4 import BeautifulSoup # Web scrapping
import urllib2
from urllib2 import urlopen # Download link

# If selenium does not run, do these things:
# (1) Downgrade it: pip install selenium==2.53.6
# (2) Downgrade Firefox to version 46
from selenium import webdriver as web # Open a web browser
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys

# Other packages
import os
import sys
import re
from time import sleep
from datetime import datetime

#------------------------------------------------------------------------------
# Self-defined functions
#------------------------------------------------------------------------------

def urlopen_wrapper(url, num_retry=3, delay=10):
    """
    Function to open a page, try several times if the page gets stuck
    """
    
    count_retry = 0
    while  count_retry < num_retry:
        try:
            page = urlopen(url, timeout=30)
            return page # If no error, end function
            
        except urllib2.URLError as e:
            print('Page load error:', e)
            print('Waiting and retrying...')
            count_retry += 1
            sleep(delay)
    
    # If try many times but failed
    print('Failed to load page...')
    return None

def BeautifulSoup_wrapper(url, num_retry=3, delay=5):
    """
    This function will try several times to extract the HTML structure of the page
    """
    
    count_retry = 0
    while count_retry < num_retry:
        try:
            page = urlopen_wrapper(url) # Try to open the page
            soup = BeautifulSoup(page, "html.parser") # Parse the page
            return soup # If no error, end function
            
        except:
            print('Extract HTML structure error. Retrying...')
            count_retry += 1
            sleep(delay)

    # If try many time but failed
    print('Failed to extract HTML structure...')
    return None

def click_wrapper(object_click, num_retry=5, delay=5):    
    """
    Function to simulate a click, try several times if cannot click
    """
    
    count_retry = 0
    while  count_retry < num_retry:
        try:
            object_click.click()
            #print('Click successful!')
            return True
            
        except:
            print('Click failed. Retrying...')
            count_retry += 1
            sleep(delay)
    
    return False

def extract_addonList(driver):
    """
    This function will extract all addons' names and urls. Chrome extensions
    page shows all addons in 1 page, but only show next addons when scrolling
    to the end of the page. This script also stimulates the scrolling action
    to get full list of addons.
    """

    # Try to scroll until the end of page, then wait for page load
    addonCount = 0
    
    while True:
    
        # Wait for the page to finish loading, then extract all addons' names and links
        loadingCircle = driver.find_element_by_css_selector('.h-a-Kd.a-Hd-mb')
        if loadingCircle.is_displayed():
            wait(driver, 30).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, '.h-a-Kd.a-Hd-mb')))
        
        addonItemList = driver.find_elements_by_css_selector('.h-Ja-d-Ac.a-u')
    
        # Scroll to last addon item
        if len(addonItemList) > 0:
            lastAddon = addonItemList[-1]
            driver.execute_script("return arguments[0].scrollIntoView();", lastAddon)
            #sleep(3) # Wait for the page to load
        
        # Click on "See other results" if any
        seeOther = driver.find_element_by_css_selector('.h-a-Hd-mb.a-Hd-mb')
        if seeOther.is_displayed(): click_wrapper(seeOther)
        
        # Check condition to exit the while loop
        if len(addonItemList) > addonCount:
            addonCount = len(addonItemList) # Update count
        else:
            break # End while loop
    
    # Loop through all addons, extract names and urls
    addonNameList = []
    addonURLList = []
    
    for addonItem in addonItemList:
        addonNameList.append(addonItem.find_element_by_css_selector('.a-na-d-w').text.strip())
        addonURLList.append(addonItem.get_attribute('href'))
    
    # Construct result table
    addonTb = pd.DataFrame({'addon_name':pd.Series(addonNameList),
                            'addon_url':pd.Series(addonURLList)},
                            columns=['addon_name', 'addon_url'])
    
    return addonTb

def extract_activeUser(addonSoup):
    """
    This function will return the number of active users in an addon page.
    If it cannot find that number, it will return 0.
    """
    
    try:
        activeUser = int(re.sub('[^0-9]', '', addonSoup.find('span', attrs={'class':'e-f-ih'}).text.strip()))
        return activeUser
    except:
        return 0

def extract_size(addonSoup):
    """
    This function will return the size of the addon in addon page. The size number
    will be a text with size + size unit (e.g. KiB, MB, etc.)
    If it cannot find that number, it will return blank string.
    """
    
    try:
        size = addonSoup.find('span', attrs={'class':'C-b-p-D-Xe h-C-b-p-D-za'}).text.strip()
        return size
    except:
        return ''
        
def extract_version(addonSoup):
    """
    This function will return the version of the addon in addon page (string).
    If it cannot find that version number, it will return and blank string.
    """
    
    try:
        version = addonSoup.find('span', attrs={'class':'C-b-p-D-Xe h-C-b-p-D-md'}).text.strip()
        return version
    except:
        return ''
        
def extract_releaseDate(addonSoup):
    """
    This function will return the release date of the addon in addon page. The 
    result will be a text of that date.
    If it cannot find that date, it will return and blank string.
    """
    
    try:
        releaseDate = addonSoup.find('span', attrs={'class':'C-b-p-D-Xe h-C-b-p-D-xh-hh'}).text.strip()
        return releaseDate
    except:
        return ''
        
def extract_numberReview(addonSoup):
    """
    This function will return the number of users giving rates to this addon.
    If it cannot find that number, it will return 0.
    """
    
    try:
        numberReview = int(re.sub('[^0-9]', '', addonSoup.find('span',  attrs={'class':'q-N-nd'}).text.strip()))
        return numberReview
    except:
        return 0
    
def extract_avgRating(addonSoup):
    """
    This function will return the average rating of this addon.
    If it cannot find that number, it will return value 0.0 (float).
    """
    
    try:
        avgRating = float(addonSoup.find('div', attrs={'class':'rsw-stars'}).get('g:rating_override'))
        return avgRating
    except:
        return 0.0

def extract_authorInfo(addonSoup):
    """
    This function will extract all information of the author if possible.
    """
    
    def extract_authorName(addonSoup):
        """
        This function will return the author name from the author extension page.
        If it cannot find that name, it will return a blank string.
        """
        
        try:
            authorName = addonSoup.find('a', attrs={'class':'e-f-y'}).text.strip()
            return authorName
        except:
            return ''
        
    def extract_authorHomepage(addonSoup):
        """
        This function will return the home page of author from the author extension page.
        If it cannot find that page url, it will return a blank string.
        """
        
        try:
            authorHomepage = addonSoup.find('a', attrs={'class':'e-f-y'}).get('href')
            return authorHomepage
        except:
            return ''
    
    # Get the extension URL of the author
    authorName = extract_authorName(addonSoup)
    authorHomepage = extract_authorHomepage(addonSoup)
    
    return authorName, authorHomepage

def extract_addonInfo(addonName, addonURL):
    """
    This function extract all information of an addon page, then return data in
    a data frame.
    """
    
    # Initiate connection to a specific addon page
    addonSoup = BeautifulSoup_wrapper(addonURL)
    
    # Extract addon information
    activeUser = extract_activeUser(addonSoup) # Active (daily) users
    size = extract_size(addonSoup) # Addon size
    version = extract_version(addonSoup) # Addon version
    releaseDate = extract_releaseDate(addonSoup) # Release date
    numberReview = extract_numberReview(addonSoup) # Number of reviews
    avgRating = extract_avgRating(addonSoup) # Average ratings
    authorName, authorHomepage = extract_authorInfo(addonSoup) # Extrac author info
    
    # Construct result table
    addonInfo = pd.DataFrame.from_dict({'addon_name':addonName,
                                        'addon_url':addonURL,
                                        'active_user':activeUser,
                                        'size':size,
                                        'version':version,
                                        'release_date':releaseDate,
                                        'number_review':numberReview,
                                        'rating':avgRating,
                                        'author_name':authorName,
                                        'author_homepage':authorHomepage},
                                        orient='index').T
    
    # Re-arrange columns
    addonInfo = addonInfo[['addon_name', 'addon_url', 'active_user',
                           'size', 'version', 'release_date', 'number_review',
                           'rating', 'author_name', 'author_homepage']]
    
    return addonInfo

def extract_addonInfo_wrapper(addonName, addonURL, num_retry=3, delay=10):
    """
    This function will try several times to extract the addonInfo.
    """
    
    count_retry = 0
    while  count_retry < num_retry:
        try:
            addonInfo = extract_addonInfo(addonName, addonURL)
            return addonInfo # If no error, end function
            
        except:
            print('ERROR. Waiting and retrying...')
            count_retry += 1
            sleep(delay)
    
    # If try many times but failed
    print('Failed to extract this add on information...')
    return None

def extract_allAddonInfo(addonTb):
    """
    This function will go to each extension page, then extract all of their
    information if possible. The result is in data frame format.
    """
    
    addonInfoTb = pd.DataFrame()
    
    # Loop through all extension page
    addonCount = 0
    for index, row in addonTb.iterrows():
    
        addonName, addonURL = row[0], row[1]
        addonCount += 1
        print('Extension', str(addonCount) + '/' + str(addonTb.shape[0]), ':', addonName)
        
        # Extract addon info
        addonInfo = extract_addonInfo_wrapper(addonName, addonURL)
        if addonInfo is not None: # Successful extract
            addonInfoTb = addonInfoTb.append(addonInfo, ignore_index=True)
        else: # Failed to extract, record errors log
            update_errorLog('SINGLE_ADDON_ERROR' + ',' + addonName + ',' + addonURL)
        
    return addonInfoTb

def verify(addonTb, addonInfoTb):
    """
    This function will verify the data collected from addonInfoTb table with
    the given list in addonTb table
    """
    
    addonTb = addonTb.reset_index(drop=True)
    addonInfoTb = addonInfoTb.reset_index(drop=True)
    
    if (addonTb == addonInfoTb[['addon_name', 'addon_url', 'extension_page']]).all().all():
        return True
    else:
        return False
    
def update_errorLog(text):
    """
    This function will append the error log file in ./log folder.
    """
    
    with open('log/errorsLog.txt', 'a') as f:
        f.write(str(datetime.now()), ':', text)
        f.write('\n')

#------------------------------------------------------------------------------
# MAIN
#------------------------------------------------------------------------------

if __name__ == '__main__':
    
    # Change os directory
    #os.chdir(os.path.join('/', 'home', 'minh', 'Python', 'WebScrapping', 'Chrome_extensions'))
    
    #--------------------------------------------------------------------------    
    # STEP 1. INITIATE CONNECTION
    #--------------------------------------------------------------------------
    
    print("Step 1. Connect to the extension page")
    
    # Define the search term and global variables (DO NOT change the vars' names)
    searchTerm = sys.argv[1] # '12345678'
    url = "https://chrome.google.com/webstore/search/" + searchTerm + "?_category=extensions"
    
    # Open a web browser with the given url
    driver = web.Firefox()
    driver.set_window_position(0, 0) # Move windows to the top-left corner
    driver.set_window_size(600, 400) # Resize Firefox windows
    driver.get(url)
    
    # Wait a bit for the page to load (find the first addon item block)
    wait(driver, 10).until(lambda driver: driver.find_element_by_css_selector('.h-Ja-d-Ac.a-u'))

    #--------------------------------------------------------------------------
    # STEP 2. EXTRACT ADDONS' NAMES AND LINKS
    #--------------------------------------------------------------------------
    
    print("Step 2. Extract all addons' names and links")
    
    addonTb = extract_addonList(driver)
    addonTb['extension_page'] = 'Chrome'
    fileOut = 'output/' + searchTerm + '_Chrome_addonList.csv'
    addonTb.to_csv(fileOut, index=False, encoding='utf-8')
    driver.quit() # Close browser, no longer need to use selenium
    
    #--------------------------------------------------------------------------
    # STEP 3. GO TO EACH ADDON PAGE, EXTRACT INFORMATION
    #--------------------------------------------------------------------------
    
    print('Step 3. Go to each extension page, extract their information')
    
    addonInfoTb = extract_allAddonInfo(addonTb)
    addonInfoTb['extension_page'] = 'Chrome'
    print('Verified:', verify(addonTb, addonInfoTb))
    
    fileOut = 'output/' + searchTerm + '_Chrome_addonInfo.csv'
    addonInfoTb.to_csv(fileOut, index=False, encoding='utf-8')
    
    print()
    
#------------------------------------------------------------------------------
# Refs
#------------------------------------------------------------------------------

"""
http://stackoverflow.com/questions/30942041/slow-scrolling-down-the-page-using-selenium
http://stackoverflow.com/questions/19803963/efficient-method-to-scroll-though-pages-using-selenium
http://www.diveintopython.net/scripts_and_streams/command_line_arguments.html
https://sqa.stackexchange.com/questions/15484/how-to-minimize-the-browser-window-which-was-launched-via-selenium-webdriver
"""

#------------------------------------------------------------------------------