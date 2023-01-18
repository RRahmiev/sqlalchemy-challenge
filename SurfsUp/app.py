import numpy as np
import sqlalchemy
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from dateutil.relativedelta import relativedelta
import datetime as dt
from flask import Flask, jsonify

# Reflecting the tables from our database

engine = create_engine("sqlite:///Resources/hawaii.sqlite")

Base = automap_base()

Base.prepare(engine, reflect=True)

# Saving the references to the tables

Measurement = Base.classes.measurement
Station = Base.classes.station

# Setting up Flask

app = Flask(__name__)

# Setting up homepage and all routes

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"<h1>Climate Analysis API App</h1>"
        f"Welcome to the Climate API App.<br/>"
        f"Below you will find a list of names of all the routes in this app and a short description of their functions.</br>"
        f"To use these functions please use the hyperlinks in the bottom of the page which are in the same order."
        f"<h2>Static Route Names:</h2>"
        f"/api/v1.0/precipitation - Returns the most recent 12 months of precipitation data.<br/>"
        f"/api/v1.0/stations - Returns a JSON list of all the stations in the data set.<br/>"
        f"/api/v1.0/tobs - Returns a JSON list of the dates and temperatures of the most active station.<br/>"
        f"/api/v1.0/start - Returns a JSON list of the minimum, average and maximum temperatures in the data after a specified date.<br/>"
        f"/api/v1.0/start/end - Returns a JSON list of the MIN, AVG and MAX temperatures between a specified start and end date.<br/>"
        f"<h2>Route Hyperlinks:</h2>"
        f"<ol><li><a href=http://127.0.0.1:5000/api/v1.0/precipitation>"
        f"Most recent 12 months of precipitation data</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/stations>"
        f"List of all stations in dataset</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/tobs>"
        f"Temperatures at most active station</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/2017-08-23>"
        f"MIN, MAX and AVG temperatures after a specified start date</a></li><br/><br/>"
        f"<li><a href=http://127.0.0.1:5000/api/v1.0/2016-08-23/2017-08-23>"
        f"MIN, MAX and AVG temperatures of specified date range</a></li></ol><br/>"
       
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
   
    session = Session(engine)

    # Calculating the date 1 year prior to the latest date

    last_measurement_data_point_tuple = session.query(
        Measurement.date).order_by(Measurement.date.desc()).first()
    (latest_date, ) = last_measurement_data_point_tuple
    latest_date = dt.datetime.strptime(latest_date, '%Y-%m-%d')
    latest_date = latest_date.date()
    date_year_ago = latest_date - relativedelta(years=1)

    # Fetching the data

    data_from_last_year = session.query(Measurement.date, Measurement.prcp).filter(
        Measurement.date >= date_year_ago).all()

    session.close()

    # Converting query results to a dictionary

    all_precipication = []
    for date, prcp in data_from_last_year:
        if prcp != None:
            precip_dict = {}
            precip_dict[date] = prcp
            all_precipication.append(precip_dict)

    # Return the JSON list

    return jsonify(all_precipication)


@app.route("/api/v1.0/tobs")
def tobs():

    session = Session(engine)

    # Calculating the date 1 year prior to the latest date

    last_measurement_data_point_tuple = session.query(
        Measurement.date).order_by(Measurement.date.desc()).first()
    (latest_date, ) = last_measurement_data_point_tuple
    latest_date = dt.datetime.strptime(latest_date, '%Y-%m-%d')
    latest_date = latest_date.date()
    date_year_ago = latest_date - relativedelta(years=1)

    # Finding most active station

    most_active_station = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count().desc()).\
        first()

    # Get the station ID

    (most_active_station_id, ) = most_active_station

    # Query the temperature data for the most active station

    data_from_last_year = session.query(Measurement.date, Measurement.tobs).filter(
        Measurement.station == most_active_station_id).filter(Measurement.date >= date_year_ago).all()

    session.close()

    # Converting quary result to a dictionary

    all_temperatures = []
    for date, temp in data_from_last_year:
        if temp != None:
            temp_dict = {}
            temp_dict[date] = temp
            all_temperatures.append(temp_dict)
    
    return jsonify(all_temperatures)


@app.route("/api/v1.0/stations")
def stations():

    session = Session(engine)

    stations = session.query(Station.station, Station.name,
                             Station.latitude, Station.longitude, Station.elevation).all()

    session.close()

    # Convert the list of stations retrieved with the quary into a dictionary

    all_stations = []
    for station, name, latitude, longitude, elevation in stations:
        station_dict = {}
        station_dict["station"] = station
        station_dict["name"] = name
        station_dict["latitude"] = latitude
        station_dict["longitude"] = longitude
        station_dict["elevation"] = elevation
        all_stations.append(station_dict)

    return jsonify(all_stations)


@app.route('/api/v1.0/<start>', defaults={'end': None})
@app.route("/api/v1.0/<start>/<end>")
def determine_temps_for_date_range(start, end):

    session = Session(engine)

    # Creating If statement to check if we have a start AND end date

    if end != None:
        temperature_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).filter(
            Measurement.date <= end).all()

    # If there is only a start date

    else:
        temperature_data = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)).\
            filter(Measurement.date >= start).all()

    session.close()

    # Appending quary results to a list

    temperature_list = []
    no_temperature_data = False
    for min_temp, avg_temp, max_temp in temperature_data:
        if min_temp == None or avg_temp == None or max_temp == None:
            no_temperature_data = True
        temperature_list.append(min_temp)
        temperature_list.append(avg_temp)
        temperature_list.append(max_temp)

    if no_temperature_data == True:
        return f"No temperature data for this date range."
    else:
        return jsonify(temperature_list)


if __name__ == '__main__':
    app.run(debug=True)
