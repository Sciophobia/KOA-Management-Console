import configparser
import hashlib
import logging
import os
import re
import shutil
import signal

import tweepy
from bson import ObjectId
from datetime import timedelta, datetime, date

import threading, time, signal

import PySimpleGUI as sgd
import boto3
import json

from pymongo.server_api import ServerApi

import bcrypt
import pymongo as pymongo
import pymongo_auth_aws as g
import us as us
import wtforms
from wtforms import form
from flask import Flask, render_template, request, flash, url_for, redirect, session
from flask_pymongo import PyMongo
from pymongo.server_api import ServerApi
from remi.server import StandaloneServer, Server

app = Flask(__name__)
app.secret_key = "super secret key"
configFile = ()

cfg = configparser.ConfigParser()
path = os.path.abspath(__file__)
sgd.theme("reddit")
port = 25566
# MongoDB connection
s = g
appWindowMain = ()
client = pymongo.MongoClient(
    "mongodb+srv://<AWS access key>:<AWS secret "
    "key>@cluster0.re3ie7p.mongodb.net/?authSource=%24external&authMechanism=MONGODB-AWS&retryWrites=true&w=majority",
    server_api=ServerApi('1'))


# print("Collections: ", db.list_collection_names())
# print("MongoDB info: ", client.server_info())
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('Login_UI.html')


def run():
    app.run(debug=True, port=port, host="0.0.0.0")


from pathlib import Path

ROOT_DIR = os.path.realpath(os.path.join(os.path.dirname(__file__)))
# Create and configure logger

logging.basicConfig(filename=os.path.join(ROOT_DIR, 'static', 'ConsoleApplication.txt'),
                    format='%(asctime)s %(message)s',
                    filemode='w')

# Creating an object
logger = logging.getLogger()

# Setting the threshold of logger to DEBUG
logger.setLevel(logging.DEBUG)


# Opens a configuration window via PySimpleGUI to select a configuration file.
def openConfigurationFileSelection():
    print("-openConfigurationFileSelection-")
    logger.info("Opening configuration file selection window.")
    file_list_column = [
        [sgd.Text("Configuration File"),
         sgd.In(size=(25, 1), enable_events=True, key="-FOLDER-"),
         sgd.FileBrowse(), ],

    ]

    layout = [
        [sgd.Text("A valid configuration file was not detected. Please select a configuration file.",
                  key='validation')],
        [sgd.Column(file_list_column)],
        # [sgd.Text('Username', size=(15, 1)), sgd.InputText('', key='Username')],
        [sgd.Button("Save", key='SaveButton')],
        [sgd.Button("Discard", key="discard")]
    ]
    # window = sg.Window(title="KOA Management Console Login", layout=layout2, margins=(500, 500)).read()

    window = sgd.Window(title="KOA Management Console Configuration", layout=layout)
    while True:
        event, values = window.read()
        if event == "Exit" or event == sgd.WIN_CLOSED:
            break
        # Folder name was filled in, make a list of files in the folder
        if event == "-FOLDER-":
            folder = values["-FOLDER-"]
            try:

                configFile = values["-FOLDER-"]

                shutil.copyfile(configFile, "KOAConsole.ini")
                logger.info("-openConfigurationFileSelection- Copied selected configuration file to root directory as "
                            "KOAConsole.ini")
                with open("KOAConsole.ini", "r") as f:
                    read_data = f.read()
                    line = read_data.replace('%', "%%")
                    f.close()

                with open("KOAConsole.ini", "w") as f:
                    f.write(line)
                    f.close()
            except Exception as e:
                print("Error occurred with the selected ini file.")
                logger.exception("-openConfigurationFileSelection- There was a critical error with the configuration "
                                 "file selected. Exception: " + str(e))
                print(e)

        if event == "SaveButton":
            cfg.read('KOAConsole.ini')
            configCheck = checkConfig()

            if configCheck:
                config = parseConfiguration('KOAConsole.ini')
                logger.critical("New configuration saved and will be used by the program.")
                window.close()
            elif not configCheck:
                window['validation'].update(
                    value='Invalid configuration detected. \nPlease make sure all necessary fields are entered. '
                          'Remember % signs have to be doubled.', )
                logger.error("Invalid configuration detected. There may be a missing parameter or typo in "
                             "KOAConsole.ini.")
        elif event == "discard":
            window.close()


clientPass = ""


# Checks the configuration file for any missing entries and notifies the user if an invalid configuration file is
# present.
def checkConfig():
    try:
        print("-checkConfig-")
        # print("Configuration being checked:", config, type(config))
        print("Sections:", (cfg.sections()))
        portIn = (cfg.get('WebUI Configuration', "web_ui_port"))
        client_connection = (cfg.get("MongoDB Configuration", "client_connection"))
        m5_aws_access = cfg.get("M5Stack Configuration", "m5_aws_access"),
        m5_aws_secret = cfg.get("M5Stack Configuration", "m5_aws_secret"),
        bucket_name = cfg.get("M5Stack Configuration", "bucket_name"),
        refreshInterval = cfg.get("M5Stack Configuration", "refreshInterval"),
        consumer_key = cfg.get("Twitter Configuration", "consumer_key"),
        consumer_secret = cfg.get("Twitter Configuration", "consumer_secret"),
        access_key = cfg.get("Twitter Configuration", "access_key"),
        access_secret = cfg.get("Twitter Configuration", "access_secret"),
        print(client_connection, portIn)
        if not portIn:
            print("Port connection not found in configuration file.")
            logger.error("-checkConfig- There was an issue with the configuration file: no port found for web_ui_port.")
            return False
        if not client_connection:
            print("Client connection not found in configuration file.")
            logger.error(
                "-checkConfig- There was an issue with the configuration file: Mongo URI for ""client_connection"" not found or is invalid.")
            return False
        if not m5_aws_access:
            print("M5 access key not found in configuration file.")
            logger.error(
                "-checkConfig- There was an issue with the configuration file: Entry for ""m5_aws_access"" not found or is invalid.")
            return False
        if not m5_aws_secret:
            print("M5 secret key not found in configuration file.")
            logger.error(
                "-checkConfig- There was an issue with the configuration file: Entry for ""m5_aws_secret"" not found or is invalid.")
            return False
        if not bucket_name:
            print("M5 AWS bucket name not found in configuration file.")
            logger.error(
                "-checkConfig- There was an issue with the configuration file: Entry for ""bucket_name"" not found or is invalid.")
            return False
        if not refreshInterval:
            print("Job refresh interval not found in configuration file.")
            logger.error(
                "-checkConfig- There was an issue with the configuration file: Entry for ""refreshInterval"" not found or is invalid.")
            return False
        if not consumer_key:
            print("Twitter API consumer key not found in configuration file.")
            logger.error(
                "-checkConfig- There was an issue with the configuration file: Entry for ""consumer_key"" not found or is invalid.")
            return False
        if not consumer_secret:
            print("Twitter API consumer secret not found in configuration file.")
            logger.error(
                "-checkConfig- There was an issue with the configuration file: Entry for ""consumer_secret"" not found or is invalid.")
            return False
        if not access_key:
            print("Twitter access key not found in configuration file.")
            logger.error(
                "-checkConfig- There was an issue with the configuration file: Entry for ""access_key"" not found or is invalid.")
            return False
        if not access_secret:
            print("Twitter access secret not found in configuration file.")
            logger.error(
                "-checkConfig- There was an issue with the configuration file: Entry for ""access_secret"" not found or is invalid.")
            return False
    except Exception as e:
        print("There is an issue with the configuration file:", e)
        logger.exception(
            "-checkConfig- There is a critical issue with the configuration file. Response received: " + str(e))
        sgd.Popup(("There is an issue with the configuration file:\n" + "Error: " + str(
            e) + "\nPlease make sure all of the necessary settings are configured!"), keep_on_top=True)
        return False, str(e)
    clientPass = client_connection
    print("Client connected:", client)
    return True


# Generates a valid configuration file based upon the entered parameters.
def genConfigFile(db_url, in_port, m5_aws_access, m5_aws_secret, bucketName, refreshInterval, consumer_key,
                  consumer_secret, access_key, access_secret, callbackuri):
    print("-genConfigFile-")
    try:

        cfg.add_section('MongoDB Configuration')
        db_url = db_url.replace('%', '%%')
        cfg.add_section('WebUI Configuration')
        port = (int(in_port))
        cfg.add_section('M5Stack Configuration')
        # client = pymongo.MongoClient(db_url, server_api=ServerApi('1'))

    except Exception as e:
        print("There was an issue generating configuration file. Message:")
        print(e)
        logger.exception("Configuration file generation error. " + str(e))
        return False, e

    cfg.set('MongoDB Configuration', 'client_connection', db_url)
    cfg.set('WebUI Configuration', 'web_ui_port', str(port))
    cfg.set('M5Stack Configuration', 'm5_aws_access', m5_aws_access)
    cfg.set('M5Stack Configuration', 'm5_aws_secret', m5_aws_secret)
    cfg.set('M5Stack Configuration', 'bucket_name', bucketName)
    cfg.set('Twitter Configuration', 'consumer_key', consumer_key)
    cfg.set('Twitter Configuration', 'consumer_secret', consumer_secret)
    cfg.set('Twitter Configuration', 'access_key', access_key)
    cfg.set('Twitter Configuration', 'access_secret', access_secret)
    cfg.set('Twitter Configuration', 'callback uri', callbackuri)
    with open('KOAConsole.ini', 'w') as configfile:
        print(cfg.write(configfile))
        logger.info("Wrote configuration to KOAConsole.ini")
    return True


# Parses through the configuration file and initiates configuration check to validate configuration file.
def parseConfiguration(cfgFile):
    print("-parseConfiguration-")
    try:

        config = cfg.read(cfgFile)

        configInput = [cfg.get("MongoDB Configuration", "client_connection"),
                       cfg.get("WebUI Configuration", "web_ui_port"),
                       cfg.get("M5Stack Configuration", "m5_aws_access"),
                       cfg.get("M5Stack Configuration", "m5_aws_secret"),
                       cfg.get("M5Stack Configuration", "bucket_name"),
                       cfg.get("M5Stack Configuration", "refreshInterval"),
                       cfg.get("Twitter Configuration", "consumer_key"),
                       cfg.get("Twitter Configuration", "consumer_secret"),
                       cfg.get("Twitter Configuration", "access_key"),
                       cfg.get("Twitter Configuration", "access_secret"),
                       ]
        print("Configuration Read:", configInput)

        if not config:
            print("1")
            logger.error(
                "-parseConfiguration- There is an issue with the configuration file or none is present in root "
                "directory. "
                "Opening configuration prompt.")
            configurator(False)
        elif config and checkConfig():
            print("2")
        #  configurator(True)
        else:
            config = cfg.read('KOAConsole.ini')
            logger.info("-parseConfiguration- Configuration file read.")
            # cfg.get("client_connection", "web_ui_port")
        return configInput
    except Exception as e:
        configurator(False)
        print("There was an issue reading the configuration file. Error message:")
        print(e)
        logger.exception(
            "-parseConfiguration- + Configuration parsing exception. Launching configurator. Exception: " + str(e))
        # configurator(False)
        return False, str(e)


# Starts a MongoDB connection with the specified MongoDB URI parameter.
def startMongo(client_connection):
    print("-startMongo-")
    try:
        print("Client information:", client_connection)
        clientAppMain = pymongo.MongoClient(
            client_connection,
            server_api=ServerApi('1'))
        return clientAppMain
    except Exception as e:
        return False, str(e)


# Opens the configuration file selection screen if the file is not present or did not pass checks.
def configurator(fileLocated):
    print("-configurator-")

    if not fileLocated:
        print("Opening configuration file selection.")
        openConfigurationFileSelection()
    if fileLocated and checkConfig():
        print("Launching main application.")
        clientPass = cfg.get("MongoDB Configuration", "client_connection")
        startMongo(clientPass)


# Starts the MongoDB by utilizing startMongo whilst passing the MongoDB uri present in the configuration file.
def startMongoNoCheck():
    print("-startMongoNoCheck-")
    logger.info("-startMongoNoCheck- Contacting MongoDB database.")
    cfg.read('KOAConsole.ini')
    try:
        clientPass = cfg.get("MongoDB Configuration", "client_connection")

    except Exception as e:
        logger.exception("-startMongoNoCheck- There was an issue connecting to MongoDB. " + str(e))
        parseConfiguration('KOAConsole.ini')
        return False, str(e)

    return startMongo(clientPass)


@app.route('/ConsoleApplication.txt', methods=["GET"])
def logTXT(address=None):
    return app.send_static_file('ConsoleApplication.txt')


@app.route('/static/KOAWeather.gif', methods=["GET"])
def logoGIF(address=None):
    return app.send_static_file('KOAWeather.gif')


@app.route('/getlogs/', methods=["GET"])
# Redirects the user to the log's html page.
def openLogScreen():
    return render_template("consoleLog_UI.html")


# Calculates the hash of the directory the python file is in.
def calcHash():
    fname = os.path.abspath(__file__)
    print("My path: " + fname)
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(2 ** 20), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


# Management Console main class.


_userName = ''
menu = ['',
        ['Show Window', 'Hide Window', '---', '!Disabled Item', 'Change Icon', ['Happy', 'Sad', 'Plain'], 'Exit']]
tooltip = 'KOA Management Console'

tray = sgd.SystemTray(menu, tooltip=tooltip)

state_names = [state.name for state in us.states.STATES_AND_TERRITORIES]


@app.route('/login/', methods=['POST'])
# Verifies the user credentials with MongoDB.
# Returns a boolean of True if verified, otherwise False.
def verifyCredentials():
    print("-verifyCredentials-")
    try:
        if request.method == "POST":
            print(request.form['username'])

            _userName = request.form['username']

            clientAppMain = startMongoNoCheck()
            print("User I am searching for: ", _userName)
            print("Users", clientAppMain.KOADB.ManagementUsers.find({}))
            userEquate = clientAppMain.KOADB.ManagementUsers.find({'Username': _userName})
            print("User Cursor: ", userEquate)
            print("Entered pass:", request.form['password'])
            userAuthenticate = check_password_mongoDB(request.form['password'], userEquate)
            print("Verified? ", userAuthenticate)
            if userAuthenticate:
                print("Authentication Successful.")
                logger.info("-verifyCredentials- User authentication successful. User: " + _userName)
                session["name"] = request.form.get("username")
                return openWelcomeScreen()
            # thread = Thread(target=openWelcomeScreen(getSensors()))
            # thread.start()

            else:
                logger.error("-verifyCredentials- Invalid credentials were entered for user " +
                             request.form['username'])
                print("Invalid credentials entered.")
                flash("Invalid credentials were entered. Please check your username and password.")
                return redirect(url_for("index"))
    except Exception as e:
        print("Error verifying credentials. Error:\n", e)
        logger.exception("-verifyCredentials- There was an exception while verifying credentials. " + str(e))
        return redirect(url_for("index"))

        #     window['title'].update(value='Invalid credentials were entered!', text_color='red')
        #     tray.show_message("Warning!", "You entered invalid credentials!")


@app.route("/logout")
# Redirects user to the login page and clears out any current sessions.
def logout():
    logger.info("-logout- User sign-out: " + session["name"])
    session["name"] = None
    return redirect("/")


@app.route("/login/", methods=['GET'])
# Redirects user to the login page.
def openLoginScreen():
    session["name"] = None
    return redirect(url_for("index"))


@app.route("/consoleAction/", methods=['POST'])
# Processes any requests made from the console welcome screen.
def proccessWelcomeAction():
    print("-proccessWelcomeAction-")
    # stationSelected = request.form[""]
    try:
        stationSelected = request.form['stationlist']
        actionSelected = request.form['actionSelection']
        station = startMongoNoCheck().KOADB.WeatherStations.find_one({'name': stationSelected})
        print("Station selected:", stationSelected, "Action selected:", actionSelected)
        if actionSelected == "add":
            print("-Add Station-")
            logger.info("-proccessWelcomeAction- User " + session[
                "name"] + "is performing the following action: " + actionSelected + " on station " + stationSelected)
            return render_template('addStation_UI.html', stationStateList=us_state_to_abbrev)
        elif actionSelected == "modify":
            print("-Modify Station-")
            logger.info("-proccessWelcomeAction- User " + session[
                "name"] + "is performing the following action: " + actionSelected + " on station " + stationSelected)
            return render_template('modify_UI.html', stationSelected=stationSelected,
                                   stationStateList=us_state_to_abbrev,
                                   stationStreet=station['street'], stationMunicipality=station['municipality'],
                                   stationState=station['state'], stationZipcode=station['zip code'])
        elif actionSelected == "remove":
            mongo_id = getDocumentID("WeatherStations", "name", stationSelected)
            print("-Remove Station-")
            print("Removing", mongo_id)
            logger.info("-proccessWelcomeAction- User " + session[
                "name"] + "is performing the following action: " + actionSelected + " on station " + stationSelected)
            print(startMongoNoCheck().KOADB.WeatherStations.delete_one({"_id": ObjectId(mongo_id)}))
            return render_template('welcome_UI.html', dropdown_list=getSensors())
        elif actionSelected == "getlogs":
            logger.info("-proccessWelcomeAction- User " + session[
                "name"] + " is performing the following action: " + actionSelected + ".")
            return openLogScreen()
        elif actionSelected == "allreadings":
            logger.info("-proccessWelcomeAction- User " + session[
                "name"] + "is performing the following action: " + actionSelected)
            return openAllSensorsScreen()
        elif actionSelected == "sensorReadings":
            logger.info("-proccessWelcomeAction- User " + session[
                "name"] + "is performing the following action: " + actionSelected + " on sensor " + stationSelected)
            return openSensorReadingScreen(stationSelected)
        elif actionSelected == "tweet":
            tweetConsolePush(stationSelected)
            return render_template('welcome_UI.html', dropdown_list=getSensors())
    except Exception as e:
        print("Exception occurred performing the requesting action.", str(e))
        flash("Your requested action could not be performed at this time. Please see logs for details.")
        logger.exception("-processWelcomeAction- There was a critical error while processing user " + session[
            'name'] + "'s requested action. " + str(e))


@app.route("/modifyAction/", methods=['POST'])
# Processes the user's request to modify a station with the specified parameters in the HTML fields.
def processModifyAction():
    print("-processModifyAction-")
    try:

        stationName = request.form['name']
        stationStreet = request.form['street']
        stationMunicipality = request.form['municipality']
        stationState = request.form['stationstate']
        stationZip = request.form['zipcode']
        mongo_id = (getDocumentID("WeatherStations", "name", stationName))
        weatherDict = {"name": stationName, "street": stationStreet,
                       "municipality": stationMunicipality,
                       "state": stationState,
                       "zip code": stationZip}
        print("Mongo Object ID:", mongo_id, "Station Updated:", weatherDict)
        logger.info((
                "-processModifyAction- User has updated station with Mongo Object ID: " + mongo_id + " Station Updated:" + str(
            weatherDict)))
        startMongoNoCheck().KOADB.WeatherStations.update_one({'_id': ObjectId(mongo_id)}, {"$set": weatherDict},
                                                             upsert=False)
        return render_template('welcome_UI.html', dropdown_list=getSensors())
    except Exception as e:
        print(
            "-processModifyAction- There was an issue with the user's modification request. Exception caught: " + str(
                e))
        logger.exception(
            "-processModifyAction- There was an issue with the user's modification request. Exception caught: " + str(
                e))
        flash("There was an issue processing your request. Please try again or return to the home screen.")
        return render_template('welcome_UI.html', dropdown_list=getSensors())


@app.route("/addAction/", methods=['POST'])
# Processes the user's request to add a station with the specified parameters in the HTML fields.
def processAddAction():
    try:
        stationName = request.form['name']
        stationStreet = request.form['street']
        stationMunicipality = request.form['municipality']
        stationState = request.form['stationstate']
        stationZip = request.form['zipcode']
        weatherDict = {"name": stationName, "street": stationStreet,
                       "municipality": stationMunicipality,
                       "state": stationState,
                       "zip code": stationZip}
        print("Station Added:", weatherDict)
        startMongoNoCheck().KOADB.WeatherStations.insert_one(weatherDict)
        logger.info("-processAddAction- User " + session['name'] + " has added a new weather station to the database. "
                                                                   "Station info: " + str(weatherDict))
        return render_template('welcome_UI.html', dropdown_list=getSensors())
    except Exception as e:
        print(
            "-processAddAction- There was an issue with the user's post request. Exception caught: " + str(e))
        flash("There was an issue processing your request. Please try again or return to the home screen.")
        logger.exception(
            "-processAddAction- There was an issue with the user's post request. Exception caught: " + str(e))


@app.route("/register/", methods=['POST', 'GET'])
# Registers a user with the MongoDB database.
def registerUser():
    print("-registerUser-")
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if request.method == "GET":
        return render_template('Register_UI.html')
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        confpassword = request.form['password2']
        email = request.form["email"]
        firstname = request.form["firstname"]
        lastname = request.form["lastname"]

        if username == "":
            flash("Enter a valid username.")
            return redirect(url_for("registerUser"))
        elif email == "" or not (re.fullmatch(regex, email)):
            flash("Enter valid e-mail address.")
            return redirect(url_for("registerUser"))
        elif password != confpassword:
            flash('Your passwords must match.')
            return redirect(url_for("registerUser"))
        elif password == "":
            flash("You must enter a password.")
            return redirect(url_for("registerUser"))
        elif (firstname == "") & (lastname == ""):
            flash("You must enter a valid name.")
            return redirect(url_for("registerUser"))
        elif confpassword == password:
            userDict = {"Username": username,
                        "Password": get_hashed_password(password.encode('utf-8')),
                        "Firstname": firstname,
                        "Lastname": lastname,
                        "E-mail address": lastname}
            print("Inserting a new user into the database.")
            startMongoNoCheck().KOADB.ManagementUsers.insert_one(userDict)
            return render_template('Login_UI.html')
    return "There was an issue with entered credentials."


@app.route("/forward/", methods=['GET'])
# Opens the main dashboard that the user first sees after login, presenting to them a menu of options.
def openWelcomeScreen():
    print("-openWelcomeScreen-")
    if not session.get("name"):
        return redirect("/")
    return render_template('welcome_UI.html', dropdown_list=getSensors())


@app.route("/getAllSensorReadings/", methods=['GET'])
# Opens the sensor reading screens for all sensors.
def openAllSensorsScreen():
    print("-openAllSensorsScreen-")
    return render_template('allSensorReadings_UI.html', stationReadings=getAllSensorReadings())


@app.route("/getSensorReadings/", methods=['GET'])
# Opens the sensor readings screen.
def openSensorReadingScreen(station):
    print("-openAllSensorsScreen-")
    return render_template('sensorReadings_UI.html', stationReadings=getSensorReading(station))


# Returns all the weather stations.
def getSensors():
    print("-getSensors-")
    try:
        sensors = []
        for x in startMongoNoCheck().KOADB.WeatherStations.find({}, {"_id": 0, "name": 1}):
            sensors.append(x["name"])
        return sensors
    except Exception as e:
        return False, str(e)


# Fetches all the readings of all M5 sensors from within the database.
# Returns a list of the readings.
def getAllSensorReadings():
    print("-getAllSensorReadings-")
    sensors = []
    sensors2 = []
    for x in startMongoNoCheck().KOADB.WeatherStationData.find({}, {"_id": 0, "station": 1, "tempF": 1, "tempC": 1,
                                                                    "humidity": 1, "pressure": 1, "time": 1,
                                                                    "date": 1}):
        print(x)
        sensors.append((x["station"], "Temperature:", str(x["tempF"]), "℉", str(x["tempC"]), "℃", "Humidity:",
                        str(x["humidity"]) + "%", "Pressure:", str(x["pressure"]) + " in", "Time:",
                        str(x["time"]), "Date:",
                        str(x["date"]) + ""))
    for s in sensors:
        s = str(s).replace(',', '')
        s = s.replace("'", "")
        sensors2.append(s)
    return sensors2[::-1]


# Fetches the readings for a specific M5 sensor from the MongoDB.
# Returns a list with the parameters.
def getSensorReading(sensor):
    print("-getSensorReading-")

    sensorData = []
    try:
        for x in startMongoNoCheck().KOADB.WeatherStationData.find(({"station": sensor}),
                                                                   {"_id": 0, "station": 1, "tempF": 1, "tempC": 1,
                                                                    "humidity": 1, "pressure": 1, "time": 1,
                                                                    "date": 1}):
            sensorData.append({
                "Temperature℉": str(x["tempF"]),
                "Temperature℃": str(x["tempC"]),
                "Humidity": str(x["humidity"]),
                "Pressure": str(x["pressure"]),
                "Time": str(x["time"]),
                "Date": str(x["date"])})

        return sensorData[::-1]
    except Exception as e:
        print("An error occurred while getting a sensor reading for", sensor, " Error:\n", e)
        return False


# Gets the amount of seconds from a time string.
def get_sec(time_str):
    """Get seconds from time."""
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)


# Fetches all the readings of the M5 sensors within the past 30 minutes from MongoDB and returns them as an array.
def getAllSensorReadingLastThirtyMinutes():
    print("-getAllSensorReadingLastThirtyMinutes-")
    todayDate = date.today()
    print("Today's date is", todayDate)
    sensorData = []
    try:
        for x in startMongoNoCheck().KOADB.WeatherStationData.find({"date": str(todayDate)},
                                                                   {"_id": 0, "station": 1, "tempF": 1, "tempC": 1,
                                                                    "humidity": 1, "pressure": 1, "time": 1,
                                                                    "date": 1}):
            readingTimeString = x["time"]
            readingTime = get_sec(readingTimeString)
            now = datetime.now()
            seconds_since_midnight = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
            now = seconds_since_midnight
            duration = (now - readingTime)

            if duration <= 1800:
                sensorData.append({
                    "Station": str(x["station"]),
                    "Temperature℉": str(x["tempF"]),
                    "Temperature℃": str(x["tempC"]),
                    "Humidity": str(x["humidity"]),
                    "Pressure": str(x["pressure"]),
                    "Time": str(x["time"]),
                    "Date": str(x["date"])})
        return sensorData[::-1]
    except Exception as e:
        print("-getAllSensorReadingLastThirtyMinutes- An error occurred while getting a sensor readings within last "
              "thirty minutes Error:\n", e)
        logger.exception(
            "-getAllSensorReadingLastThirtyMinutes- An error occurred while getting a sensor readings within last "
            "thirty minutes. Exception: " + str(e))
        return False, str(e)


# Iterates through all the readings returned from getAllSensorReadingLastThirtyMinutes
# Interacts with the tweet method to post notable sensor readings.
def iterateRecentStations():
    print("-iterateRecentStations-")
    try:
        recentReadings = getAllSensorReadingLastThirtyMinutes()
        highTempLimit = 100
        lowTempLimit = 40
        lowPressure = 29.80
        highPressure = 30.20
        logger.info(
            "-iterateRecentStations- Beginning check for abnormal weather conditions in the last 30 minutes of readings.")
        for x in recentReadings:
            if int(x["Temperature℉"]) >= highTempLimit:
                tweet("Station " + x["Station"] + " is reporting an abnormally high temperature of " + x[
                    "Temperature℉"] + ".")
            if int(x["Temperature℉"]) <= lowTempLimit:
                tweet(
                    "Station " + x[
                        "Station"] + " is reporting temperatures that may create icy conditions. Temperature: " +
                    x["Temperature℉"] + ".")
            if float(x["Pressure"]) <= lowPressure:
                tweet("Station " + x["Station"] + " is reporting a lower air pressure reading of " + x[
                    "Pressure"] + "inHg. Indicating clear skies and calm weather is probable.")
            if float(x["Pressure"]) >= highPressure:
                tweet("Station " + x["Station"] + " is reporting a higher air pressure reading of " + x[
                    "Pressure"] + "inHg. Indicating inclement weather is probable.")

        logger.info("-iterateRecentStations- Successfully iterated through all recent readings and generated alerts.")
    except Exception as e:
        logger.exception(
            "-iterateRecentStations- There was a critical error while checking recent readings. Exception: " + str(e))


# Returns the current registered user utilizing the console.
def getCurrentUser():
    print("-getCurrentUser-")
    return session["name"]


# Returns the current registered user utilizing the console.
def getCurrentUser():
    print("-getCurrentUser-")
    return session["name"]


# Salt hashes a plaint text password (str) using bcrypt's hashpw method.
# Returns a Python "bytes" object.
def get_hashed_password(plain_text_password):
    # Hash a password for the first time
    #   (Using bcrypt, the salt is saved into the hash itself)
    return bcrypt.hashpw(plain_text_password, bcrypt.gensalt())


# Validates a salt hashed password with a plaintext string.
# Returns a boolean.
def check_password(plain_text_password, hashed_password):
    # Check hashed password. Using bcrypt, the salt is saved into the hash itself
    return bcrypt.checkpw(plain_text_password, hashed_password)


# Verifies a plaintext password with a salt hashed password (PyMongo cursor).
# Returns a boolean.
def check_password_mongoDB(entry, userEquate):
    print("-check_password_mongoDB-")
    try:

        if userEquate != [""]:

            userEquateListStr = []
            records = dict((record['Password'], record) for record in userEquate)

            print("Records:", records)

            for i in records:
                userEquateListStr.append(i)
                print("Value in list: ", userEquateListStr)
            print("Checking password...")
            print("userEquateListStr:", userEquateListStr)
            PWs = ('{} {}'.format(userEquateListStr, ''))

            PWs = repr(PWs)[4:-1]
            PWs = PWs[:-3]
            print("PW: ", PWs, " Entry: ", entry.encode('utf-8'))
            verifyPW = check_password(entry.encode('utf-8'), PWs.encode('utf-8'))
            return verifyPW
        else:
            return False
    except Exception as e:
        print("Exception caught when trying to verify credentials with MongoDB.")
        print("Exception message:", e)
        return False


# Finds the document id within a collection in the MongoDB client "db".
def getDocumentID(collectionName, fieldName, fieldEntry):
    collection = startMongoNoCheck().KOADB[collectionName]
    cursor = collection.find_one({fieldName: fieldEntry})
    return str(cursor["_id"])


# Retrieves MongoDB document with the specified parameters within the database.
def retrieveMongoDocument(collectionName, searchFieldName, searchFieldValue):
    print("Searching for", searchFieldName, "with a value of", searchFieldValue, "in collection",
          collectionName + ".")
    cursor = [i for i in startMongoNoCheck().KOADB[collectionName].find({searchFieldName: (searchFieldValue)})]
    return cursor


# Pushes tweet if manually requested through the management console.
def tweetConsolePush(station):
    stationReading = getSensorReading(station)[0]
    print(stationReading)
    message = "Station " + station + " is reporting a weather conditions of " + str(stationReading)

    tweet(message)


# Tweets a message using the specified keys.
def tweet(message):
    print("-Tweet-")
    try:
        # Replace these with your own consumer and access keys
        consumer_key = cfg.get("Twitter Configuration", "consumer_key")
        consumer_secret = cfg.get("Twitter Configuration", "consumer_secret")
        access_key = cfg.get("Twitter Configuration", "access_key")
        access_secret = cfg.get("Twitter Configuration", "access_secret")
        callbackuri = cfg.get("Twitter Configuration", "callback URI")
        print("Consumer Key", consumer_key, "\n Consumer Secret", consumer_secret, "Access Key", access_key,
              "\n Access Secret", access_secret)
        print(consumer_secret)
        # Set up the authentication
        auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token=access_key,
                                        access_token_secret=access_secret, callback=callbackuri)
        # auth.set_access_token(access_key, access_secret)

        # Connect to the API
        api = tweepy.API(auth)
        print("Twitter Message:", message)
        # Post the message to Twitter
        logger.info("-Tweet- Pushed status message update to Twitter.")
        api.update_status(message)
    except Exception as e:
        pass


# Source: https://gist.github.com/rogerallen/1583593
us_state_to_abbrev = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "District of Columbia": "DC",
    "American Samoa": "AS",
    "Guam": "GU",
    "Northern Mariana Islands": "MP",
    "Puerto Rico": "PR",
    "United States Minor Outlying Islands": "UM",
    "U.S. Virgin Islands": "VI",
}


def get_db():
    """
    Configuration method to return db instance
    """
    db = getattr(g, "_database", None)

    if db is None:
        db = g._database = PyMongo(app).db

    return db


def create_app():
    app.config['DEBUG'] = True
    app.config['MONGO_URI'] = cfg.get("MongoDB Configuration", "client_connection")
    app.config["SESSION_PERMANENT"] = False
    # db.init_app(app)

    # from yourapplication.views.admin import admin
    # from yourapplication.views.frontend import frontend
    # app.register_blueprint(admin)
    # app.register_blueprint(frontend)

    return app


class ProgramKilled(Exception):
    pass


def signal_handler(signum, frame):
    raise ProgramKilled


class Job(threading.Thread):
    def __init__(self, interval, execute, *args, **kwargs):
        threading.Thread.__init__(self)
        self.daemon = False
        self.stopped = threading.Event()
        self.interval = interval
        self.execute = execute
        self.args = args
        self.kwargs = kwargs

    def stop(self):
        self.stopped.set()
        self.join()

    def run(self):
        while not self.stopped.wait(self.interval.total_seconds()):
            self.execute(*self.args, **self.kwargs)


# establishes connection to AWS IAM role and contains permissions needed to access and read files within bucket
def startAWSConnection():
    print("-startAWSConnection-")
    try:
        s3 = boto3.resource(
            's3',
            region_name='us-east-1',
            aws_access_key_id=cfg.get("M5Stack Configuration", "access_key"),
            aws_secret_access_key=cfg.get("M5Stack Configuration", "secret_key")
        )
        logger.info("-startAWSConnection- Started AWS connection.")
        return s3
    except Exception as e:
        print("There was a critical error establishing AWS client connection. Exception: " + str(e))
        logger.exception(
            "-startAWSConnection- There was a critical error establishing AWS client connection. Exception: " + str(e))
        return False, str(e)


# variable used to keep track of how many items (stored sensor readings) are in bucket
item_count = 0


# iterates over all files present in bucket, reads files, converts data to json, and then returns parsed data.
def getSensorReadingsFromAWS():
    print("-getSensorReadingsFromAWS-")
    try:
        awsBucket = cfg.get("M5Stack Configuration", "bucket_name")
        bucket = startAWSConnection().Bucket(awsBucket)
        logger.info("-getSensorReadingsFromAWS- Fetched info from AWS bucket", awsBucket)
        return bucket
    except Exception as e:
        print("There was a critical error fetching sensor readings from AWS bucket. Exception: " + str(e))
        logger.exception("-getSensorReadingsFromAWS- There was a critical error fetching sensor readings from AWS "
                         "bucket. Exception: " + str(e))
        return False, str(e)


# Inserts sensor data retrieve from getSensorReadingsFromAWS function into MongoDB collection.
def depositSensorData():
    print("-depositSensorData-")
    try:
        item_count = 0
        for obj in getSensorReadingsFromAWS().objects.all():
            item_count = item_count + 1
            key = obj.key  # reads file and acquires key_id used by AWS (basically primary keys) for each file
            body = obj.get()['Body'].read().decode('utf-8')  # reads file and acquires the actual contents of each file
            parsed_data = json.loads(body)
            startMongoNoCheck().KOADB['WeatherStationData'].insert_one(parsed_data)
        print("There are", item_count, "items in the bucket.")
        logger.info(
            "-depositSensorData- Successfully inserted sensor data into MongoDB. " + item_count + " items were parsed.")
        return True
    #   print(parsed_data)
    #   print(parsed_data['date'])              #just had this here to test
    except Exception as e:
        print("There was a critical issue depositing sensor data from AWS bucket. Exception: " + str(e))
        logger.exception("-depositSensorData- There was a critical issue depositing sensor data from AWS bucket. "
                         "Exception: " + str(e))
        return False, str(e)


if __name__ == "__main__":
    #    test = getAllSensorReadings()
    #   for x in test:
    #        print(x)

    parseConfiguration('KOAConsole.ini')
    app1 = create_app()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    job = Job(interval=timedelta(seconds=int(cfg.get("M5Stack Configuration", "refreshInterval"))),
              execute=depositSensorData)
    job2 = Job(interval=timedelta(seconds=int(cfg.get("M5Stack Configuration", "refreshInterval"))),
               execute=iterateRecentStations)
    iterateRecentStations()
    # tweetConsolePush("Dewie")
    logger.info("-__main__- Starting periodic sensor refresh service. ")
    print("!!! -__main__- Starting periodic sensor refresh service. !!!")

    job.start()
    job2.start()
    logger.info("-__main__- Starting Flask service. ")
    Thread = threading.Thread(target=app.run(port=port))
    Thread.start()
    while True:
        try:
            time.sleep(1)
        except ProgramKilled:
            logger.exception("-__main__- Console program ended.")
            print("Program killed: running cleanup code")

            job.stop()
            break
