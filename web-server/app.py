#
# Created by Rui Santos
# Complete project details: http://randomnerdtutorials.com
#

import paho.mqtt.client as mqtt
from flask import Flask, render_template, request
import json
import matplotlib
import sqlite3
matplotlib.use('Agg')
import time
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from dateutil import parser

app = Flask(__name__)

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed 
    client.subscribe("/statistiques")

# The callback for when a PUBLISH message is received from the ESP8266.
def on_message(client, userdata, message):
	if message.topic == "/statistiques":
		print("Statistique updated")
		statistiques_json = int(message.payload)
		print(statistiques_json)
	        # connects to SQLite database. File is named "sensordata.db" without the quotes
	        # WARNING: your database file should be in the same directory of the app.py file or have the correct path
		conn=sqlite3.connect('OurDb.db')
		c=conn.cursor()
		c.execute("""INSERT INTO somnolence (Numero, currentdate, currentime, conducteur) VALUES((?), date('now'), time('now'), (?))""",(statistiques_json
            ,'fadi') )
		conn.commit()
		conn.close()


client=mqtt.Client()
client.connect("localhost",1883,60)
client.on_connect = on_connect
client.on_message = on_message
client.loop_start()


@app.route("/")
def main():
   
   # connects to SQLite database. File is named "sensordata.db" without the quotes
   # WARNING: your database file should be in the same directory of the app.py file or have the correct path 
   conn=sqlite3.connect('OurDb.db')
   conn.row_factory = dict_factory
   c=conn.cursor()
   c.execute("SELECT * FROM somnolence ORDER BY id DESC LIMIT 20")
   readings = c.fetchall()
   #print(readings)
   Numero = []
   timenow = []
   for row in readings:
       conducteur=row["conducteur"]
       Numero.append(row["Numero"])
       timenow.append(parser.parse(row["currentime"]))

   # Convert datetime.datetime to float days since 0001-01-01 UTC.
   dates = [mdates.date2num(t) for t in timenow]

   fig = plt.figure()
   ax1 = fig.add_subplot(111)
   ax1.set_title("Statistiques du :"+conducteur)

   # Configure x-ticks
   ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y %H:%M'))

   # Plot temperature data on left Y axis
   ax1.set_ylabel("Somnolence N:")
   ax1.plot_date(dates, Numero, '-', label="Tentatives", color='b')
   # Format the x-axis for dates (label formatting, rotation)
   fig.autofmt_xdate(rotation=60)
   fig.tight_layout()

   # Show grids and legends
   ax1.grid(True)
   ax1.legend(loc='best', framealpha=0.5)


   plt.savefig("static/figure.png")
   return render_template('main.html', readings=readings)

if __name__ == "__main__":
   app.run(host='192.168.43.62', port=8181, debug=False)
