# This Python file uses the following encoding: utf-8

'''
written by vancsisoft 2017.05.

Environmental notes:
The script is located on DNS-320 NAS /ffp/home/vancsi/scripts/gsdb/ , named as gsdb_nightly_checkSold.py.
Needs Python 2.7 to run. Needs the gsdb.sqlite database in the same directory.
Also needs BeautifulSoup compiled python file in the same directory.
The script is started by cron: every day at 0:03.
'''

'''
Change log:
Improvements in v1_02:
- checkWebForItemActive() is improved with errorHandling()

Improvements in v_1_01:
- initialization of logging is moved to utils.py
- config.py introduced, containing constants. It has to be imported.
- removed unused imports (they are moved to utils.py)

Improvements in v1_00:
- the nightly running functions are now moved to this separate script:
	getLastCheckedDay
	setLastCheckedDay
	checkWebForItemActive
	getActiveLinksFromDb
	dbUpdateSold

Common functions put to utils.py:
	visitLink
	getIdFromLink
	calculateDeltaTime
	normalizeString
	encodeString


'''

import sys
import re
import sqlite3
import time
from datetime import datetime
from utils import *
from config import *


nightly_check_version = 'v1.02'


#Function getLastCheckedDay
#Returns the day (int) when db items were last checked if they still exist or not. Format: int, %y%m%d (e.g.: 161227)
def getLastCheckedDay():
	conn = sqlite3.connect('gsdb.sqlite')
	cur = conn.cursor()
	cur.execute('''SELECT * FROM LastCheckedDay''')
	for row in cur:
		day = int(row[0])
	conn.commit()
	cur.close()
	debug('getLastCheckedDay: day fetched: '+str(day))
	return day


#Function setLastCheckedDay
#Sets the inputed day to DB. Input: str.
def setLastCheckedDay(day):
	conn = sqlite3.connect('gsdb.sqlite')
	cur = conn.cursor()
	cur.execute('''SELECT * FROM LastCheckedDay''')
	cur.execute('''UPDATE LastCheckedDay SET day = ?''', (day, ))
	conn.commit()
	cur.close()
	debug('setLastCheckedDay: day set: '+str(day))
	info('Last check for sold items is set to: '+str(dateToday))
	return


#Function setItemSoldInDb
#Input: int(id), int(date)
#Function searches the item with the given id in DB, and updates it as sold with the given date (today)
def setItemSoldInDb(id, date):
	conn = sqlite3.connect('gsdb.sqlite')
	cur = conn.cursor()
	try:
		cur.execute('''UPDATE Instruments SET soldDate = ?, active = ? WHERE id = ?''', (date, 0, id))
		debug('setItemSoldInDb: item set to sold with date: '+str(date)+', id: '+str(id))
	except Exception as ex_update:
		debug('setItemSoldInDb: db update to set item sold was unsuccessful.')
		debug(ex_update)
	conn.commit()
	cur.close()
	return


#Function checkWebForItemActive
#Input: a link (str)
#Checks the inputed link, returns True if item is still active, and False when link is inactive (item sold)
def checkWebForItemActive(url):
	isActive = True
	try:
		soup = visitLink(url)
		divs = soup('div')
		for div in divs:
			if div.get('id') == 'hirdetes':
				if re.search('(INAKTÍV HIRDETÉS)',str(div)):
					debug('checkWebForItemActive: sold item found. link: '+url)
					isActive = False
	except:
		debug('checkWebForItemActive(): could not check item page: '+url)
		isExit = False
		isMail = True
		errorHandling(isExit, isMail, 'checkWebForItemActive()', 'could not check item page: '+url)
	return isActive


#Function getActiveLinksFromDb
#Returns a list with the links of unsold items from DB.
def getActiveLinksFromDb():
	links = []
	conn = sqlite3.connect('gsdb.sqlite')
	cur = conn.cursor()
	cur.execute('''SELECT * FROM Instruments WHERE active = ?''', (1, ))
	for row in cur:
		links.append(str(row[11]))
	conn.commit()
	cur.close()
	debug('getActiveidsFromDb: links fetched: '+str(links))
	info(str(len(links))+' active links fetched from DB.')
	return links


#function dbUpdateSold
#Function updates item as sold, with days needed to sell
#Runs only once a day
def dbUpdateSold():
	if (int(getLastCheckedDay()) == int(dateToday)):
		debug('dbUpdateSold: This function has been run today. Exiting.')
	else:
		soldItemsNumber = 0
		activeLinksInDb = getActiveLinksFromDb()
		for link in activeLinksInDb:
			if not checkWebForItemActive(link):
				id = getIdFromLink(link)
				setItemSoldInDb(id, dateToday)
				soldItemsNumber += 1
			time.sleep(antiDosTimerNight)
		info('DB updated with '+str(soldItemsNumber)+' sold item(s).')
		setLastCheckedDay(dateToday)
	return


#-----------------------------------------
#                   MAIN
#-----------------------------------------
def main():
	debug('***************************************************')
	info(' ***GSDB nightly check for sold items %s started***' % (nightly_check_version))
	debug('***************************************************')
	debug('dateToday: '+str(dateToday))

	dbUpdateSold()

	debug('***************************************************')
	info(' ***GSDB nightly check for sold items %s finished***' % (nightly_check_version))
	debug('***************************************************')



if __name__ == '__main__':
	sys.exit(main())