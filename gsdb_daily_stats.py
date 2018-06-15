# This Python file uses the following encoding: utf-8

'''
written by vancsisoft 2017.05.

Environmental notes:
The script is located on DNS-320 NAS /ffp/home/vancsi/scripts/gsdb/ , named as gsdb_daily_stats.py.
Needs Python 2.7 to run. Needs the gsdb.sqlite database in the same directory.
The script is started by cron: every day at 8:01.
'''

'''
Change log:
Improvements in v1_00:
- implemented this python script:
	- checks the number of all rows (id-s) in db
	- checks the number of active items in db
	- checks the lastCheckedDay from db
	- checks the last successful run time of gsdb.py and gsdb_nightly_checkSold.py from logInfo.txt
	- generates mail body from the above listed database
	- sends status mail

'''


import sys
import re
import sqlite3
from utils import *
from config import *


daily_stats_version = 'v1.00'

#Function getStatsFromDb()
#Input: -
#Returns:
#	- number of rows (id-s) in Instruments table (int)
#	- number of active items in Instruments table (int)
#	- lastCheckedDay from db	(int)
def getStatsFromDb():
	conn = sqlite3.connect('gsdb.sqlite')
	cur = conn.cursor()
	cur.execute('''SELECT count(id) FROM Instruments''')
	for row in cur:
		noIds = str(row[0])
	cur.execute('''SELECT count(*) FROM Instruments WHERE active = ?''',(1, ))
	for row in cur:
		noActive = str(row[0])
	cur.execute('''SELECT * FROM LastCheckedDay''')
	for row in cur:
		lastCheckedDay = str(row[0])
	conn.commit()
	cur.close()
	return(noIds, noActive, lastCheckedDay)


def parseDataFromLog(paramName, f):
	runs = re.findall(paramName, f.read())
	f.seek(0) # setting the cursor back to the beginning of the file
	for run in runs: 
		result = run
	return result


#Function getLastRunFromLog()
#Input: -
#Return:
#	- last successful run date of gsdb.py
#	- last successful run date of gsdb_nightly_checkSold.py
def getLastRunFromLog():
	f = open('logInfo.log', 'r')
	gsdbMatchString = 'gsdb.py:[0-9]+ ([0-9]+-[0-9]+-[0-9]+ [0-9]+:[0-9]+:[0-9]+),.*INFO.*GSDB v.*finished.*'
	gsdbNightlyMatchString = 'gsdb_nightly_checkSold.py:[0-9]+ ([0-9]+-[0-9]+-[0-9]+ [0-9]+:[0-9]+:[0-9]+),.*INFO.*GSDB nightly check for sold items.*finished.*'
	last_gsdb_run = parseDataFromLog(gsdbMatchString,f)
	last_nightly_run = parseDataFromLog(gsdbNightlyMatchString,f)
	f.close()
	return(last_gsdb_run, last_nightly_run)


#Function generateStatsMailBody()
#Input: 
#Return:
def generateStatsMailBody(noIds, noActive, lastCheckedDay, last_gsdb_run, last_nightly_run):
	warningLastCheckedDay = ''
	warningLastGsdbRun = ''
	warningLastNightlyRun = ''
	if int(lastCheckedDay) != int(dateToday):
		warningLastCheckedDay = '\nlastCheckedDay IN DATABASE IS NOT UP-TO-DATE!\nIT SEEMS gsdb_nightly_checkSold.py DID NOT RUN OR FINIS RUNNING LAST NIGHT!'
#	if int(last_gsdb_run) < (int(dateToday)-1):
#		warningLastGsdbRun = '\ngsdb.py SEEMS DID NOT RUN OR FINIS RUNNING YESTERDAY!'
#	if int(last_nightly_run) != int(dateToday):
#		warningLastNightlyRun = '\ngsdb_nightly_checkSold.py SEEMS DID NOT RUN OR FINIS RUNNING LAST NIGHT!'
	mailBody = ''
	mailBody = mailBody+'GSDB database and script daily statistics at '+dateToday+'\n\n'
	mailBody = mailBody+'Number of total items in DB: '+noIds+'\n'
	mailBody = mailBody+'Number of active items in DB: '+noActive+'\n'
	mailBody = mailBody+'Last nightly check of active items on web according to DB data: '+lastCheckedDay+'\n'
	mailBody = mailBody+'Last successful finish of gsdb.py according to logs: '+last_gsdb_run+'\n'
	mailBody = mailBody+'Last successful finish of gsdb_nightly_checkSold.py according to logs: '+last_nightly_run+'\n'
	if (warningLastCheckedDay != ''):
		mailBody = mailBody+'\n'+warningLastCheckedDay
	if (warningLastGsdbRun != ''):
		mailBody = mailBody+'\n'+warningLastGsdbRun
	if (warningLastNightlyRun != ''):
		mailBody = mailBody+'\n'+warningLastNightlyRun
	mailBody = mailBody+'\n\n\nMail sent by vancsisoft, gsdb'
	return(mailBody)




#-----------------------------------------
#                   MAIN
#-----------------------------------------
def main():
	debug('***************************************************')
	info(' ***        GSDB daily stats %s started         ***' % (daily_stats_version))
	debug('***************************************************')
	debug('dateToday: '+str(dateToday))

	noIds = getStatsFromDb()[0]
	noActive = getStatsFromDb()[1]
	lastCheckedDay = getStatsFromDb()[2]
	last_gsdb_run = getLastRunFromLog()[0]
	last_nightly_run = getLastRunFromLog()[1]
	mailBody = generateStatsMailBody(noIds, noActive, lastCheckedDay, last_gsdb_run, last_nightly_run)
	sendMail(mailBody, mailSubjectStatus, mailFrom, mailTo, smtpHost, smtpPort, smtpUsername, smtpPassword)

	debug('***************************************************')
	info(' ***        GSDB daily stats %s finished        ***' % (daily_stats_version))
	debug('***************************************************')



if __name__ == '__main__':
	sys.exit(main())
