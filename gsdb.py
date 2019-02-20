# This Python file uses the following encoding: utf-8

'''
written by vancsisoft 2017.05.

Environmental notes:
The script is located on DNS-320 NAS /ffp/home/vancsi/scripts/gsdb/ , named as gsdb.py.
Needs Python 2.7 to run. Needs the gsdb.sqlite database containing the created tables in the same directory.
Also needs BeautifulSoup compiled python file in the same directory.
The script is started by cron: every hours:3min between 8am and 22pm.
'''

'''
Change log:
Improvements in v1_14:
- Quick fix in getItemsFromWeb(): div class name 'hirdeteslist_hirdetes' changed from 'hirdeteslist_hirdetes hirdeteslist_hirdetes'
  on the web page. Code modified to search for both formats.

Improvements in v1_13:
- getItemsFromWeb(): implemented errorHandling() in case of gsfanatic page url is not reachable.
- getItemStatsFromDb(): implemented errorHandling()
- getStatsFromDb() is renamed as getItemStatsFromDb()

Improvements in v1_12:
- errorHandling() is exported to utils.py
- sendMail() is exported to utils.py + new parameter implemented: mailSubject

Improvements in v1_11:
- initialization of logging is moved to utils.py
- config.py introduced, containing constants. It has to be imported.
- removed unused imports (they are moved to utils.py)

Improvements in v1_10:
- the nightly running functions are now moved to separate script, and deleted from here:
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

Improvements in v1_05:
- just debugging modification

Improvements in v1_04:
- getItemStatsFromDb returns the list sorted based on price.
- bug fix in getItemStatsFromDb: the for loop didn't work correctly!
- updated findCheapItems logic: sold items also has to be 25% but minimum 5000Ft more expensive.

Improvements in v1_03:
- normalizeString function: added parameter isLink. If not link, than '.', '/', ':' characters are also deleted.
- bug fix: getItemsFromWeb function: don't call normalizeString on 'link'! Call encodeString on it!
	- due to this bug, lot of links are incorrect in db! Have to fix them! --> no problem, links without '-' characters still work!
	- also rerun sellerUpdateScript, it was unsuccessful because of the faulty links!  --> no problem, links without '-' characters still work!
	- soldDate is still invalid for these faulty link items! They all seem to be active!  --> no problem, links without '-' characters still work!

Improvements in v1_02:
- added '+' character deletion in normalizeString function --> needs manual db update with script to normalize all name-s again!

Improvements in v1_01:
- database structure update in Instruments table:
	Manual steps to be done at live upgrade:
	- rename 'link' row to 'id'
	- create new row called 'link' (text)
	- copy 'id' contents to 'link' contents
	- delete contents of 'id'
	- modify 'id' type from text to integer
	- run link_to_id_script.py to generate 'id' row for existing items
- created new function getIdFromLink
- visitItemLink function renamed to visitLink, and called by getItemsFromWeb.
- bug fixes in adding new items to db

Improvements in v1_0
- generateMailContent function: doesn't list those references any more, where sellerName is the same.
- displays sellerName in the email both for item and reference items (just for check, later this should be deleted, as items with same sellerName are not listed!)

Improvements in v_099:
- After first successful nightly run of v_098, the existing, active links will be all fetched from web, and get the sellerData.
Afer it, the sellerData update can be removed from the nightly runnning part (checkWebForItemActive function!) This is done in this
v_099 version.
- Mail subject modification, now it contains the date as well.
- 2s delay implemented in dbAddNewItems, between visiting the links of newly added items to DB.

Improvements in v_098:
- generateMailContent simplificated, try: and expect: parts removed (no need for these with using normalizeString from v_096)
- footer is added to mail textBody
- new 'gsdbVersion' variable implemented to use it in strings
TBD:
- Add 'sellerName', 'sellerPhone', 'sellerTown' to Instruments table - this needs to be done manually!
- To collect sellerName, sellerPhone and sellerTown:
	- Write a separate script to try to scrap these data for the inactive links!
	- Implemented updateSellerToDb, getSellerDataFromSoup, visitItemLink functions. With the use of these, seller data
	is updated in db at every night run, when checking links wether they are active or not, and at every new item writed
	to db (dbAddNewItems function)
	NOT implemented yet: checking duplicated items, or same items based on seller data during reference item collection.

Improvements in v_097:
- MailNotificationList table is normalized in db by handling
- checkInMailNotificationList function updated accordingly - no normalization is needed in the function, it works with already normalized strings.

Improvements in v_096:
- normalizeString function implementation and use (for name and category, categoryInterested..)
- encodeString function implementation.
Hotpatch for v_096:
- Create new field to Instruments table, with name "displayName", and run db_update_script_01.py normalizing script (only once!!!)

Improvements in v_095:
- Logging to 2 different log files: log_debug.log; log_info.log
- utf-8 error handling with try: except: in several functions - temporarily solution, string normalizing function
is needed to be implement!


Planned improvements to be done:
- DB javítása, relációs adatbázisoknak megfelelően: külön táblák létrehozása az ismétlődő adatoknak, referenciákkal hivatkozva!
- Napi rendszerességű status mail küldése
- Új mezőket felvenni a hirdetés linkből: hirdető, telefonszám, helység. Ez alapján kiszűrni, ha ugyanaz a termék többször is meg volt hirdetve!
Update-elni a db-t, a legkésőbbi / legalacsonyabb árú hirdetésre (+ esetleg az összes hirdetés delta idejét összeadva letárolni!)
- Egész felvitele git-be.
- Név alapján történő kézi keresés a db-ben (ehhez esetleg web interface?)
- Multiple hozzáférést megoldani SQLite-ban: https://sqlite.org/threadsafe.html
- MySQL-re áttérni (?)
- Update price as well when checking items are active or not in nightly_check_script!

'''

import sys
import re
import sqlite3
import time
from datetime import datetime
import operator							# sorting list of dicts
from utils import *
from config import *

gsdbVersion = 'v1.14'


#function updateSellerToDb
#Input: url (string), sellerName (str), sellerPhone (str), sellerTown (str)
#Check if the seller fields are NONE, and fills them with the inputed data
def updateSellerToDb(url, sellerName, sellerPhone, sellerTown):
	conn = sqlite3.connect('gsdb.sqlite')
	cur = conn.cursor()
	cur.execute('''UPDATE Instruments SET sellerName = ?, sellerPhone = ?, sellerTown = ? WHERE link = ?''', (sellerName, sellerPhone, sellerTown, url))
	conn.commit()
	cur.close()
	debug('updateSellerToDb: seller data updated to db: '+url+' '+sellerName+' '+sellerPhone+' '+sellerTown)
	return

#Function getSellerDataFromSoup
#Input: item url (string), soup (BeautifulSoup object)
#Searches for sellerName, sellerPhone, sellerTown
#Returns a list of strings: sellerName, sellerPhone, sellerTown (strings are utf-8, no more encode or decode will be needed)
def getSellerDataFromSoup(url, soup):
	divs = soup('div')
	sellerName = ''
	sellerPhone = ''
	sellerTown = ''
	for div in divs:
		if (div.get('id') == 'hirdetes_adatlap'):
			try:
				sellerName = encodeString(re.findall('Hirdető : <span id="hirdetes_adatsor"><a href=".*">(.*)</a></span>',str(div))[0])
			except:
				sellerName = 'notGiven'
			try:
				sellerPhone = encodeString(re.findall('Telefonszám : <span id="hirdetes_adatsor">(.*)</span><br />',str(div))[0])
			except:
				sellerPhone = 'notGiven'
			try:
				sellerTown = encodeString(re.findall('Helység : <span id="hirdetes_adatsor">(.*)</span>',str(div))[0])
			except:
				sellerTown = 'notGiven'
			break
	return [sellerName, sellerPhone, sellerTown]


#Function getCategoryInterestedFromDb
#Reading CategoryInterested table from DB, returns a list.
def getCategoryInterestedFromDb():
	categoryInterested = []
	conn = sqlite3.connect('gsdb.sqlite')
	cur = conn.cursor()
	cur.execute('''SELECT * FROM CategoryInterested''')
	for row in cur:
		categoryInterested.append(normalizeString(row[0]))
	conn.commit()
	cur.close()
	return categoryInterested


#function getItemsFromWeb
#in url: the url for the gsfanatic page to parse as a string
#return: list of items (list elements are dictionaries with name, category, price, displayName, link, id).
def getItemsFromWeb(url):
	try:
		soup = visitLink(url)
	except:
		isExit = True
		isMail = True
		errorHandling(isExit, isMail, 'getItemsFromWeb()', 'could not open url: '+url)
	divs = soup('div')
	items = []
	categoryInterested = getCategoryInterestedFromDb()
	for div in divs:
		if (div.get('class') == 'hirdeteslist_hirdetes') or (div.get('class') == 'hirdeteslist_hirdetes hirdeteslist_hirdetes'):
			if not (re.search('(AJÁNLATOT VÁR)',str(div)) or re.search('(hirdeteslist_ar_szoveges)',str(div))):
				category = normalizeString(re.findall('\t\t\t(.*)<br />',str(div.a))[1])
				if not category in categoryInterested : continue
				displayName = encodeString(re.findall('<span class=\"hirdetes_list_cim\">(.*)</span>',str(div))[0])
				name = normalizeString(displayName)
				price = re.findall('<div class=\"hirdeteslist_ar\"><!--// ([0-9]+)//-->',str(div))[0]
				link = encodeString(str(div.a['href']))
				items.append({
					'name': name,
					'category': category,
					'price': price,
					'link': link,
					'displayName': displayName,
					'id': getIdFromLink(link)})
	debug('getItemsFromWeb output: '+str(items))
	info(str(len(items))+' item(s) fetched from web, after filtering based on category.')
	return(items)


#function dbAddNewItems
#Function updates the db element
#Input a list of fetched items from web. Function checks if it already exists in DB or not.
#Returns the newly added items list
def dbAddNewItems(items):
	conn = sqlite3.connect('gsdb.sqlite')
	cur = conn.cursor()
	addedNewItems = []
	#TODO: Create it only if needed! Do it in a separate function at the begining of the script, with try:, create whole DB if needed.
	#cur.execute('''DROP TABLE IF EXISTS Instruments''')
	#cur.execute('''CREATE TABLE Instruments (link TEXT, name TEXT, category TEXT, price INTEGER, addedDate DATE, soldDate DATE, active BOOLEAN)''')
	for item in items:
		id = item['id']
		name = item['name']
		category = item['category']
		price = item['price']
		added = dateToday
		active = 1
		displayName = item['displayName']
		link = item['link']
		cur.execute('''SELECT name FROM Instruments WHERE id = ?''', (id, ))
		try:
			row = cur.fetchone()[0]
			debug('dbAddNewItems: Item found in DB: '+str(id))
		except:
			soup = visitLink(link)
			sellerData = getSellerDataFromSoup(link, soup)
			debug('dbAddNewItems: item not found in DB, adding the new item to DB: '+str(item))
			debug('dbAddNewItems: sellerData fetched from item link: '+sellerData[0]+' '+sellerData[1]+' '+sellerData[2])
			cur.execute('''INSERT INTO Instruments (id, name, category, price, addedDate, active, displayName, sellerName, sellerPhone, sellerTown, link) VALUES ( ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ? )''', (id, name, category, price, added, active, displayName, sellerData[0], sellerData[1], sellerData[2], link) )
			item['sellerName'] = sellerData[0]
			item['sellerPhone'] = sellerData[1]
			item['sellerTown'] = sellerData[2]
			addedNewItems.append(item)
			time.sleep(antiDosTimerDay)
	conn.commit()
	cur.close()
	info('DB was updated with '+str(len(addedNewItems))+' new item(s).')
	return(addedNewItems)


#Function checkInMailNotificationList
#Function searches items from getItemsFromWeb for marked, interesting elements based on name, price, category
#Returns a list
def checkInMailNotificationList(items):
	returnList = []
	conn = sqlite3.connect('gsdb.sqlite')
	cur = conn.cursor()
	cur.execute('''SELECT * FROM MailNotificationList''')
	for row in cur:
		interestingName = row[0]
		interestingPrice = int(row[1])
		for item in items:
			if item['name'] != u'':
				itemName = item['name']
				itemPrice = int(item['price'])
				itemDisplayName = item['displayName']
				if ((interestingName in itemName) or (itemName in interestingName)):
					if interestingPrice >= itemPrice:
						returnList.append(item)
						debug('checkInMailNotificationList: item passed MailNotificationList filter.\nItem: '+str(item)+'\nFilter criteria passed: '+str(row))
	conn.commit()
	cur.close()
	info('Found '+str(len(returnList))+' item(s) to send by mail, based on category and price.')
	return(returnList)


#function getItemStatsFromDb
#Function gets db rows with itemName, except the actual one
#Input: itemName(str), itemId(int); output: itemList: list of items from db (whole row: id, name, category, price, addedDate, soldDate, active, sellerName, sellerPhone, sellerTown, link)
def getItemStatsFromDb(itemName, itemId):
	try:
		itemName = normalizeString(itemName)
	except:
		error('getItemStatsFromDb: could not normalize itemName with function normalizeString()')
		isExit = False
		isMail = True
		errorHandling(isExit, isMail, 'getItemStatsFromDb()', 'could not normalize itemName with function normalizeString(): '+itemName)
	conn = sqlite3.connect('gsdb.sqlite')
	cur = conn.cursor()
	itemList = []
	try:
		cur.execute('''SELECT * FROM Instruments WHERE name = ?''', (itemName, ))
	except Exception as ex_dbRead:
		#If the db read is not successful, try to remove .decode('utf-8') from above!
		error('getItemStatsFromDb: DB read unsuccessful: '+ex_dbRead.message)
		isExit = False
		isMail = True
		errorHandling(isExit, isMail, 'getItemStatsFromDb()', 'DB read unsuccessful: '+ex_dbRead.message)
	try:
		row = cur.fetchone()
		while (row != None):
			if itemId == row[0]:
				row = cur.fetchOne()
				continue
			itemList.append(list(row))
			row = cur.fetchone()
			debug('getItemStatsFromDb: Item found in db with name: '+itemName)
	except:
		debug('getItemStatsFromDb: Item not in db with name: '+itemName)
	conn.commit()
	cur.close()
	itemList.sort(key=operator.itemgetter(3,4))
	return(itemList)


#Function findCheapItems
#Input: addedNewItemsToDb (list) Function returns a list of items, which seem to be cheap based on filter criterias,
#based on database data.
#Filter criteria:
#	- Sold item found in db, which is sold within 15 days cheaper than the actual item.
#	- Active item found in db (not sold), but it is 25% (but at least 5000Ft) more expensive than the actual item.
def findCheapItems(addedNewItemsToDb):
	cheapItems = []
	for item in addedNewItemsToDb:
		if item['name'] != u'':
			actualPrice = int(item['price'])
			for itemFromDb in getItemStatsFromDb(item['name'], item['id']):
				dbPrice = itemFromDb[3]
				dbActive = itemFromDb[6]
				if ((dbActive == 0) and (actualPrice <= dbPrice*0.75) and (dbPrice - actualPrice > 5000)):
					dbSoldDateDelta = calculateDeltaTime(itemFromDb[4], itemFromDb[5])
					if dbSoldDateDelta < 15:
						cheapItems.append(item)
						debug('findCheapItems: sold item found in db: '+str(itemFromDb))
						break
				else:
					if ((dbActive == 1) and (actualPrice <= dbPrice*0.75) and (dbPrice - actualPrice > 5000 )):
						cheapItems.append(item)
						debug('findCheapItems: active item found in db: '+str(itemFromDb))
						break
	info(str(len(cheapItems))+' Cheap item(s) found.')
	return(cheapItems)


#Function generateMailContent link
#Function generates and formats text body of the email to be sent.
#Input: itemsForMail (list). Returns the generated text as string.
def generateMailContent(mailNotificationList):
	textBody = ''
	referenceText = 'Reference items found in db:'
	tabText = '     '
	footer = 'Mail sent by vancsisoft, gsdb version %s' % (gsdbVersion)
	for item in mailNotificationList:
		referenceItems = ''
		oneItem = item['displayName'] + '  ' + item['category'] + '  ' + str(item['price']) + ' Ft ' + item['sellerName'] + ' ' + item['link'] + '\n'
		for refItem in getItemStatsFromDb(item['name'], item['id']):
			refSellerName = refItem[8]
			refSellerPhone = refItem[9]
			refSellerLink = refItem[11]
			if refSellerName != item['sellerName']:
				if refItem[6] == 0:
					deltaTime = calculateDeltaTime(refItem[4], refItem[5])
					referenceItems = referenceItems + tabText + str(refItem[3]) + 'Ft by ' + refSellerName + ' sold in ' + str(deltaTime) + ' days, on ' + refItem[5] + ' ' + refSellerLink + '\n'
				else:
					referenceItems = referenceItems + tabText + str(refItem[3]) + 'Ft by ' + refSellerName + ' still advertising from ' + refItem[4] + ' ' + refSellerLink + '\n'
		textBody = textBody + oneItem + tabText + referenceText + '\n' + referenceItems + '\n\n'
	textBody = textBody + '\n\n\n' + footer
	debug('generateMailContent: textBody generated: '+textBody)
	info('Mail body text content generated.')
	return textBody


#-----------------------------------------
#                   MAIN
#-----------------------------------------
def main():
	debug('****************************************')
	info(' ***        GSDB %s started        ***' % (gsdbVersion))
	debug('****************************************')
	debug('dateToday: '+str(dateToday))

	#Reading items from webpage ('ELADÓ', with price), which are in the categoryInterested list:
	itemsFromWeb = getItemsFromWeb(gsurl)

	#Runing dbAdd adds new elements to db from output of getItemsFromWeb(), returns a list with newly added elements to
	#checkInMailNotificationList function, which checks if newly added items are in the mailNotificationList, and returns the filtered list.
	addedNewItemsToDb = dbAddNewItems(itemsFromWeb)
	if addedNewItemsToDb != []:
		itemsForMail = checkInMailNotificationList(addedNewItemsToDb)
		cheapItems = findCheapItems(addedNewItemsToDb)
		if cheapItems != []:
			for cheapItem in cheapItems:
				if cheapItem not in itemsForMail:
					itemsForMail.append(cheapItem)
		if itemsForMail != []:
			mailBody = generateMailContent(itemsForMail)
			#Sending mail witn newly added items, which are categoryInterested, newly added to DB, and filtered by mailNotificationList.
			sendMail(mailBody, mailSubjectFyi)

	debug('****************************************')
	info(' ***       GSDB %s finished       ***' % (gsdbVersion))
	debug('****************************************')

if __name__ == '__main__':
	sys.exit(main())
