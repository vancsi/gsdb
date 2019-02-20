# This Python file uses the following encoding: utf-8

'''
written by vancsisoft 2017.05.

Environmental notes:
The is a helper script, only for use during testing, or updating the script on the server where it is running.
'''

from gsdb_nightly_checkSold import *

def main():
	debug('****************************************')
	info(' ***setLastCheckDay.py script started ***')
	debug('****************************************')

	setLastCheckedDay(dateToday)

	debug('****************************************')
	info(' ***setLastCheckDay.py script finished***')
	debug('****************************************')

	return


if __name__ == '__main__':
	sys.exit(main())
