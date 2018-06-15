# This Python file uses the following encoding: utf-8

'''

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
***************      IMPORTANT      ***************
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

This is a helper script, should be run only once when updating database with new 'id' row (row[0]) from data from new 'link' row.
It gets the id from the link.

'''

import re
import sqlite3

def getIdFromLink(link):
	try:
		id = int(re.findall('.*gsfanatic.com/hu/hirdetes/([0-9]+)/.*',link)[0])
	except:
		id = int(000000)
	return(id)


def getLinksFromDb():
	links = []
	conn = sqlite3.connect('gsdb.sqlite')
	cur = conn.cursor()
	cur.execute('''SELECT link FROM Instruments ''')
	for row in cur:
		links.append(row[0])
	conn.commit()
	cur.close()
	return links


def setIdInDb(links):
	conn = sqlite3.connect('gsdb.sqlite')
	cur = conn.cursor()
	for link in links:
		id = getIdFromLink(link)
		cur.execute('''UPDATE Instruments SET id = ? WHERE link = ?''', (id, link))
	conn.commit()
	cur.close()
	return


#Main:
links = getLinksFromDb()
setIdInDb(links)
print('Done.')