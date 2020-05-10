import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from datetime import datetime, date, time
from dateutil.relativedelta import relativedelta

from flask import Flask, jsonify, request

#_____________________________________________________________________________________________________________

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station


#_______________________________________________________________________________________________________________
#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################



climate_app_art = "https://specials-images.forbesimg.com/imageserve/5e5b1230d378190007f4af78/960x0.jpg"

station_app = "http://127.0.0.1:5000/api/v1.0/stations"

precipitation_app = "http://127.0.0.1:5000/api/v1.0/precipitation"

tobs_app = "http://127.0.0.1:5000/api/v1.0/tobs"

specific_date_app = "http://127.0.0.1:5000/api/v1.0/2016-08-23"

specific_date_range_app = "http://127.0.0.1:5000/api/v1.0/2016-08-23/2017-08-23"

@app.route("/")

def home():
    return (
        f"<h1><center>Hawaii Climate App</h1></center><br>"
        f"<center><img src={climate_app_art}></center><br>"
        f"<b><center><h2>Available App Routes :: [Raw Data Sets]</b></h2></center><br>"
        f"<h2><center><a href={precipitation_app}>Hawaii [Precipitation] App</a></h2></center><br>"
        f"<h2><center><a href={station_app}>Hawaii [Stations] App</a></h2></center><br>"
        f"<h2><center><a href={tobs_app}>Hawaii [Observed Temperatures] App</a></h2></center><br>"
        f"<b><center><h2>Available App Routes :: [Min, Avg, Max Temperatures]</b></h2></center><br>"
        f"<h2><center><a href={specific_date_app}>Hawaii Observed Temperatures [Specific Date] App</a></h2></center><br>"
        f"<h2><center><a href={specific_date_range_app}>Hawaii Observed Temperatures [Specific Range] App</h2></center>"
    )


#____________________________________________________________________________________________________________

@app.route("/api/v1.0/precipitation")

def precipitation():
    # Create session from Python to the DB
    session = Session(engine)

    # Query all precipitation data
    results_prcp = session.query(Measurement.date, Measurement.prcp).all()

    session.close()
    
    precipitation_data = []
     # Loop through each list of tuples
    for date, prcp in results_prcp:
        precipitation_dict = {}
        precipitation_dict["Date"] = date
        precipitation_dict["Precipitation"] = prcp
        precipitation_data.append(precipitation_dict)  

    return jsonify(precipitation_data)

#___________________________________________________________________________________________________


@app.route("/api/v1.0/stations")

def stations():
    # Create session from Python to the DB
    session = Session(engine)

    # Query for list of Station Object
    results_station = session.query(Station).all()

    session.close()
    
    station_data = []
    
    # Loop through each station
    for row in results_station:
        station_dict = {}
        station_dict["Station ID"] = row.station
        station_dict["Station Name"] = row.name
        station_dict['Latitude'] = row.latitude
        station_dict['Longitude'] = row.longitude
        station_dict['Elevation'] = row.elevation
        station_data.append(station_dict)
    
    return jsonify(station_data)

#_____________________________________________________________________________________________________

@app.route("/api/v1.0/tobs")

def tobs():
    # Create session from Python to the DB
    session = Session(engine)
    
    # Most Active Station Record
    stations_count = func.count(Measurement.station)
    most_active_station = session.query(Measurement.station, stations_count).\
                           group_by(Measurement.station).\
                           order_by(stations_count.desc()).first()[0]
    print(f"Most active station is: {most_active_station}")
          
    
    
    # Latest Date in DataFrame
    
    last_date_query = session.query(Measurement.date).order_by(Measurement.date.desc()).first()
    last_date= datetime.strptime(last_date_query[0],"%Y-%m-%d").date()
    print(f"Last date in the data base is: {last_date}")  # outputs date as string
          
    # Calculate the date 1 year ago from the last data point in the database
    date_12months_ago = last_date - relativedelta(months= 12)
    print(f"Date (1 year) 12 Months ago from the last date is: {date_12months_ago}")     
       

    # Query for temperature in the last 12 months
    results_temp_last_12months = session.query(Measurement.date, Measurement.tobs).\
        filter_by(station = most_active_station).\
        filter(Measurement.date >= date_12months_ago).all()

    session.close()
    
    temperature_data = []
    for date, tobs in results_temp_last_12months:
        temperature_dict = {}
        temperature_dict["Date"] = date
        temperature_dict["Temperature"] = tobs
        temperature_data.append(temperature_dict)  

    return jsonify(temperature_data)


#______________________________________________________________________________________________________________


@app.route("/api/v1.0/<date>")

def temperature_date(date):
    
    # Create session from Python to the DB
    session = Session(engine)

    start_date = datetime.strptime(date, '%Y-%m-%d').date()

    temp_start_stats = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).\
        filter(Measurement.date >= start_date).all()

    temp_result= []
    for temp in temp_start_stats:
        temp_start_dict = {}
        temp_start_dict['Start Date:' ] = (date)
        temp_start_dict['The Minimum Temperature' ] = round(temp_start_stats[0][0],2)
        temp_start_dict['The Average Temperature' ] = round(temp_start_stats[0][1],2)
        temp_start_dict['The Maximum Temperature' ] = round(temp_start_stats[0][2],2)
        temp_result.append(temp_start_dict)

    session.close()   
    
    return jsonify({"Specific Date Temperature Data ": temp_result})
    
#     return(   
#         f"<center><h3>Temperature Stats For {date}:</h3></center><br>"    
#         f"<center>The Minimum temperature: {temp_start_dict['The Minimum temperature: ']} Fahrenheit.</center><br>"
#         f"<center>The Average temperature: {temp_start_dict['The Average temperature: ']} Fahrenheit.</center><br>"
#         f"<center>The Maximum temperature: {temp_start_dict['The Maximum temperature: ']} Fahrenheit.</center>"
#     )

# #_________________________________________________________________________________________________________________


@app.route("/api/v1.0/<start>/<end>")

def start_end_date_calc_temps(start, end):
    # Create session from Python to the DB
    session = Session(engine)

    start_date = datetime.strptime(start, '%Y-%m-%d').date()
    end_date = datetime.strptime(end, '%Y-%m-%d').date()

    temperature_stats = session.query(func.min(Measurement.tobs), func.max(Measurement.tobs), func.avg(Measurement.tobs)).\
        filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).all()


    temp_stats_data = []
    for temp in temperature_stats:
        temp_stats_dict = {}
        temp_stats_dict['Start Date'] = (start)
        temp_stats_dict['End Date'] = (end)
        temp_stats_dict['The Minimum Temperature'] = round(temperature_stats[0][0],2)
        temp_stats_dict['The Average Temperature'] = round(temperature_stats[0][1],2)
        temp_stats_dict['The Maximum Temperature'] = round(temperature_stats[0][2],2)
        
    temp_stats_data.append(temp_stats_dict)

    session.close()

    return jsonify({"Date Range Data ": temp_stats_data})

#     return(   
#         f"<center><h3>Temperature Stats Between {start} And {end}:</h3></center><br>"    
#         f"<center>The Minimum temperature: {temp_stats_dict['The Minimum temperature: ']} Fahrenheit.</center><br>"
#         f"<center>The Average temperature: {temp_stats_dict['The Average temperature: ']} Fahrenheit.</center><br>"
#         f"<center>The Maximum temperature: {temp_stats_dict['The Maximum temperature: ']} Fahrenheit.</center>"
#     )


#_____________________________________________________________________________________________________________________________

###IMPORTANT NOTE: this code must be included at the end of any app file


if __name__ == '__main__':
    app.run(debug=True)
