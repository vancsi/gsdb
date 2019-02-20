# This Python file uses the following encoding: utf-8

'''
written by vancsisoft 2017.05.

Environmental notes:
The script is located on DNS-320 NAS /ffp/home/vancsi/scripts/gsdb/ , named as gsdb.py.
Needs Python 2.7 to run. Needs the gsdb.sqlite database containing the created tables in the same directory.
Also needs BeautifulSoup compiled python file in the same directory.
'''

'''
Change log:
Improvements in v1_03:
- Improved debugging in errorHandling() function
- Implemented errorHandling() in sendMail() function

Improvements in v1_02:
- improved errorHandling() - with alert e-mail sending option
- moved sendMail() function from gsdb.py to utils.py

Improvements in v1_01:
- logging is now a function only in utils.py. It has to be called at the begining of main() functions.

Improvements in v1_00:
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

'''

import urllib
import re
from BeautifulSoup import *
import time
from datetime import datetime
from email.mime.text import MIMEText
import smtplib
import logging
import logging.config
from config import *


utils_version = 'v1.03'

dateToday = time.strftime('%y%m%d')


#Initalization of logging
logging.config.fileConfig('gsdb_log.config')
logger=logging.getLogger(__name__)
debug=logger.debug
info=logger.info
warning=logger.warning
error=logger.error
crit=logger.critical



#Function visitLink
#Input: the link of the item (str)
#returns the soup (BeautifulSoup object)
def visitLink(url):
	try:
		html = urllib.urlopen(url).read()
		soup = BeautifulSoup(html)
	except:
		info('visitLink: could not open url: '+url)
		if url == gsurl:
			isExit = True
		else:
			isExit = False
		isMail = False
		errorHandling(isExit, isMail, 'visitLink()', 'could not open url: '+url)
	return soup


#Function getIdFromLink
#input: link(str)
#returns: id(int)
def getIdFromLink(link):
	try:
		id = int(re.findall('.*gsfanatic.com/hu/hirdetes/([0-9]+)/.*',link)[0])
	except:
		id = int(000000)
		debug('getIdFromLink: couldn\'t find id in link: '+link)
	return(id)


#Function calculateDeltaTime
#Function calculates the days between two dates given in yymmdd format.
#Input values must be strings! : date1, date2, where date2 is a later date (bigger number)
#Output: number of delta days (int)
def calculateDeltaTime(startDate, stopDate):
	startDate = datetime.strptime(startDate, '%y%m%d')
	stopDate = datetime.strptime(stopDate, '%y%m%d')
	return abs((stopDate - startDate).days)


#Function normalizeString(stringToStrip)
#Deletes the following characters from the string: " ", ",", "'","-", "_"
#Modifies string to lower case, and rstrips
#checks if it is ascii or unicode, and codes to unicode if it is ascii.
#Returns a string as a result
def normalizeString(stringToNormalize):
	normalizedString = stringToNormalize
	if isinstance(normalizedString, str):
		try:
			normalizedString = normalizedString.decode('utf-8')
		except:
			debug('normalizeString: string decode unsuccessful, trying to encode it: '+stringToNormalize)
			try:
				normalizedString = normalizedString.encode('utf-8')
			except:
				debug('normalizeString: string encode unsuccessful, string stays untouched: '+stringToNormalize)
	normalizedString = normalizedString.lower()
	normalizedString = normalizedString.rstrip()
	normalizedString = normalizedString.replace(' ', '')
	normalizedString = normalizedString.replace(',', '')
	normalizedString = normalizedString.replace('\'', '')
	normalizedString = normalizedString.replace('\"', '')
	normalizedString = normalizedString.replace('-', '')
	normalizedString = normalizedString.replace('_', '')
	normalizedString = normalizedString.replace('+','')
	normalizedString = normalizedString.replace('.','')
	normalizedString = normalizedString.replace('\\','')
	normalizedString = normalizedString.replace('/','')
	normalizedString = normalizedString.replace(':','')
	normalizedString = normalizedString.replace(u'á', 'a')
	normalizedString = normalizedString.replace(u'é', 'e')
	normalizedString = normalizedString.replace(u'í', 'i')
	normalizedString = normalizedString.replace(u'ó', 'o')
	normalizedString = normalizedString.replace(u'ö', 'o')
	normalizedString = normalizedString.replace(u'ő', 'o')
	normalizedString = normalizedString.replace(u'ú', 'u')
	normalizedString = normalizedString.replace(u'ü', 'o')
	normalizedString = normalizedString.replace(u'ű', 'u')

	return(normalizedString)


#Function encodeString(stringToEncode)
#Check if input string is asccii or unicode, and codes to unicode if it is ascii.
#To be used only for name of items to display.
#Returns a string as a result.
def encodeString(stringToEncode):
	encodedString = stringToEncode
	if isinstance(encodedString, str):
		try:
			encodedString = encodedString.decode('utf-8')
		except:
			debug('encodeString:  string decode unsuccessful, trying to encode it: '+stringToEncode)
			try:
				encodedString = encodedString.encode('utf-8')
			except:
				debug('encodeString: string encode unsuccessful, string stays untouched: '+stringToEncode)
	return(encodedString)


#Function sendMail
#Function sends email with interesting items from result of checkInMailNotificationList
def sendMail(mailBody, mailSubject, mailFrom, mailTo, smtpHost, smtpPort, smtpUsername, smtpPassword):
	msg = MIMEText(mailBody, 'plain', 'utf-8')
	msg['Subject'] = mailSubject
	msg['From'] = mailFrom
	msg['To'] = mailTo
	debug('sendMail: establishing ssl connection...')
	try:
		s = smtplib.SMTP_SSL(smtpHost, smtpPort)
		debug('sendMail: ssl connection OK, trying to login...')
		s.login(smtpUsername, smtpPassword)
		debug('sendMail: smtp login OK')
		s.sendmail(mailFrom, [mailTo], msg.as_string())
		info('Email sent.')
		s.quit()
	except:
		isExit = False
		isMail = False
		errorHandling(isExit, isMail, 'sendMail()', 'Could not send e-mail.')
	return


#Function errorHandling
#Input:
#	isExit (boolean): needs to exit or not
#	isMail (boolean): needs to send e-mail about the problem or not.
#	calledFrom (str): the function from where errorHandling is called
#	errorMessage (str): the error message
#Return: -
#Function is called from exceptions. It terminates running.
def errorHandling(isExit, isMail, calledFrom, errorMessage):
	debug('errorHandling() is called from: '+calledFrom+' with message: '+errorMessage)
	if isMail:
		footer = 'Mail sent by vancsisoft, gsdb'
		mailBody = 'errorHandling() is called from '+calledFrom+' at '+time.strftime('%y%m%d %H:%M:%S')+'\n'+errorMessage+'\n\n\n'+footer
		sendMail(mailBody, mailSubjectError, mailFrom, mailTo, smtpHost, smtpPort, smtpUsername, smtpPassword)
	if isExit:
		debug('errorHandling(): exiting...')
		sys.exit()
	return
