import sqlite3
import pandas as pd
from sqlite3 import Error
import numpy
import sqlalchemy

def create_connection(db_file):
	"""
	Create a database connection to a SQLite database.

	Input: name of the .db file

	Output: n/a, should make a connection to the database in question
	"""
	try:
		conn = sqlite3.connect(db_file)
		# print sqlite3.version
	except Error as e:
		print e
		return None
	finally:
		conn.close()

def create_table(conn, create):
	"""
	Create a table from the create_table_sql statement.

	Input: connection object, CREATE (something here) statement

	Output: a new table in the db
	"""
	try:
		curs = conn.cursor()
		curs.execute(create)
	except Error as e:
		print e

def write_to_db(db, conn, dataframe):
	"""
	Writes the contents of a pandas DataFrame to a SQLite database

	Input: the connection object to the database, a pandas DataFrame

	Output: results written to the database
	"""
	engine = sqlalchemy.create_engine('sqlite:///chinook.db')
	dataframe = dataframe.drop(['SPY','max_leverage', 'net_leverage','information','transactions','period_open', 'period_label', 'period_close'], 1)

	# now write dataframe to sql
	dataframe.to_sql('performance measure', engine, if_exists='replace', index=False, index_label=False)
	# asdf.to_sql('results', engine, if_exists='replace', index=False, index_label=False)

def run(database, dataframe):
	# create a db connection
	conn = sqlite3.connect(database)

	if conn is not None:
		write_to_db(database, conn, dataframe)
	else:
		print "Cannot connect to the database."

	# close connection
	conn.close()

# if __name__ == '__main__':
# 	main()