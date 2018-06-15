# This Python file uses the following encoding: utf-8

'''




!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
***************      IMPORTANT      ***************
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

This is a helper script, should be run only when database doesn't contain all sellerData (sellerName, sellerPhone, sellerTown).
It searches for items in db with no sellerName filled in, visits all the item links, and gets the sellerData if can.




'''

import urllib
import re
from BeautifulSoup import *
import sqlite3
import time
from gsdb import encodeString

#function updateSellerToDb
#Input: url (string), sellerName (str), sellerPhone (str), sellerTown (str)
#Check if the seller fields are NONE, and fills them with the inputed data
def updateSellerToDb(url, sellerName, sellerPhone, sellerTown):
	conn = sqlite3.connect('gsdb.sqlite')
	cur = conn.cursor()
	cur.execute('''UPDATE Instruments SET sellerName = ?, sellerPhone = ?, sellerTown = ? WHERE link = ?''', (sellerName, sellerPhone, sellerTown, url))
	conn.commit()
	cur.close()
	return

#Function getSellerDataFromSoup
#Input: item url (string), soup (BeautifulSoup object)
#Searches for sellerName, sellerPhone, sellerTown
#Returns a list of strings: sellerName, sellerPhone, sellerTown (strings are utf-8, no more encode or decode will be needed)
def getSellerDataFromSoup(url, soup):
	divs = soup('div')
	sellerName = 'notGiven'
	sellerPhone = 'notGiven'
	sellerTown = 'notGiven'
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


#Function visitItemLink
#Input: the link of the item (str)
#returns the soup (BeautifulSoup object)
def visitItemLink(url):
	html = urllib.urlopen(url).read()
	soup = BeautifulSoup(html)
	return soup


def checkWebForItemNotActive(url):
	soup = visitItemLink(url)
	sellerData = getSellerDataFromSoup(url, soup)
	updateSellerToDb(url, sellerData[0], sellerData[1], sellerData[2])
	return


def getNullLinksFromDb():
	nullLinks = []
	conn = sqlite3.connect('gsdb.sqlite')
	cur = conn.cursor()
	cur.execute('''SELECT * FROM Instruments WHERE sellerName IS NULL ''')
	for row in cur:
		nullLinks.append(str(row[0]))
	conn.commit()
	cur.close()
	return nullLinks


def getEmptyLinksFromDb():
	emptyLinks = []
	conn = sqlite3.connect('gsdb.sqlite')
	cur = conn.cursor()
	cur.execute('''SELECT * FROM Instruments WHERE sellerName = ? OR sellerPhone = ? OR sellerTown = ?''', ('','',''))
	for row in cur:
		emptyLinks.append(str(row[0]))
	conn.commit()
	cur.close()
	return emptyLinks


nullLinks = getNullLinksFromDb()
emptyLinks = getEmptyLinksFromDb()
links = nullLinks
for emptyLink in emptyLinks:
	links.append(emptyLink)
print (str(len(links))+' items are missing sellerData')
for link in links:
	checkWebForItemNotActive(link)
	print(link+' - updated with seller data')
	time.sleep(1)

