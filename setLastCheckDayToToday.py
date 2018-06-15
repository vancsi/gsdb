# This Python file uses the following encoding: utf-8

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