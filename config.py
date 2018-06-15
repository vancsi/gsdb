# This Python file uses the following encoding: utf-8

'''
written by vancsisoft 2017.05.
This python file is a config file for gsdb.
It is imported to gsdb scripts.

'''

import time

gsurl = 'http://gsfanatic.com/hu/legfrissebb-hangszer/kinal'

mailTo = 'vancso.peter@gmail.com'
mailFrom = 'vancsisoft@gmai.com'
mailSubjectFyi = '[GS DB] GS fanatic hangszerek FYI - '+str(time.strftime('%Y %m %d'))
mailSubjectError = '[GS DB] SERVER FAILURE NOTIFICATION - '+str(time.strftime('%Y %m %d'))
mailSubjectStatus = '[GS DB] Daily server status mail - '+str(time.strftime('%Y %m %d'))
smtpHost = 'smtp.gmail.com'
smtpPort = 465
smtpUsername = 'vancsisoft@gmail.com'
smtpPassword = 'Fill_Me'


antiDosTimerDay = 3
antiDosTimerNight = 3
