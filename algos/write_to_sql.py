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

def add_column(index, column, df):
	"""
	Concatenates a column and a DataFrame

	Input: index position of column in DataFrame, name of column, name of pandas DataFrame

	Output: augmented DataFrame with extra column
	"""
	df.insert(index, column, pd.Series(strat_name, index=df.index))
	return None

def write_to_db(db, results, strat_name):
	"""
	Writes the contents of a pandas DataFrame to a SQLite database

	Input: the connection object to the database, a pandas DataFrame, and the name of the trading strategy used

	Output: results written to the database
	"""
	# create sqlalchemy engine
	engine = sqlalchemy.create_engine('sqlite:///test.db')

	# round column numbers and remove problematic columns
	results = results.drop(['SPY','period_open', 'period_label', 
								'period_close','orders', 'positions', 'transactions'], 1)
	results = results.round(3)
	results = results.tail(n=1)

	# combine trading_strat and results
	metrics = results.iloc[0]

	# initialize "final" dataframe	
	dataframe = pd.Series.to_frame(metrics)

	# add name of strategy
	dataframe.insert(0, 'Trading Strategy', pd.Series(strat_name, index=results.index))

	# add names of metrics
	dataframe.insert(1, 'Metric', pd.Series(list(results)))

	# now write dataframe to sql
	dataframe.to_sql('test', engine, if_exists='replace', index=False, index_label=False)

def run(database, dataframe, strat_name):
	# create a db connection
	conn = sqlite3.connect(database)

	if conn is not None:
		write_to_db(database, dataframe, strat_name)
	else:
		print "Cannot connect to the database."

	# close connection
	conn.close()