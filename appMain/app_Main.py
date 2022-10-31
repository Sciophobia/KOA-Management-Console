import hashlib
import PySimpleGUI as sg
import os

import bcrypt

import pymongo as pymongo
from pymongo.server_api import ServerApi

path = os.path.abspath(__file__)
sg.theme("reddit")

client = pymongo.MongoClient("mongodb+srv://<AWS access key>:<AWS secret key>@cluster0.re3ie7p.mongodb.net/?authSource=%24external&authMechanism=MONGODB-AWS&retryWrites=true&w=majority", server_api=ServerApi('1'))

db = client.KOADB

print("Collections: ", db.list_collection_names())
print(client.server_info())
# testing inserting collections into mongodb.
print(db.test_collection.insert_one({"my_test field": "my test value oct 30 2022"}))


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
class appWindowMain:
    _userName = ''
    stations = ["Station 1", "Station 2", "Station 3"]

    def genTestStations(self):
        db.WeatherStations.insert_one({"Station 1": "Privet Road, Surrey"})

    # Opens the login screen that requests user's credentials.
    def openLoginScreen(self):
        print("My hash - " + calcHash())
        layout = [
            [sg.Text("Please login to continue.")],
            [sg.Text('Username', size=(15, 1)), sg.InputText('', key='Username')],
            [sg.Text('Password', size=(15, 1)), sg.InputText('', key='Password', password_char='*')],
            [sg.Button("OK")],
            [sg.Button("No Account?")]
        ]
        # window = sg.Window(title="KOA Management Console Login", layout=layout2, margins=(500, 500)).read()
        window = sg.Window(title="KOA Management Console Login", layout=layout)

        # label = tk.Label(text="KOA Management Console", fg="white", bg="black")
        # label.pack()
        # window.mainloop()
        while True:
            event, values = window.read()
            # End program if user closes window or
            # presses the OK button
            if event == "OK" or event == sg.WIN_CLOSED:
                self._userName = values['Username']
                break

        window.close()
        # print('Username: ' + values['Username'])
        print('Username: ' + self._userName)
        print('Password: ' + values['Password'])

    def openAddStation(self):
        layout = [
            [sg.Text("Enter weather station info to add it to the database.")],
            [sg.Text('Station Name', size=(15, 1)), sg.InputText('', key='Station Name')],
            [sg.Text('Station Street', size=(15, 1)), sg.InputText('', key='Station Street')],
            [sg.Text('Station Municipality', size=(15, 1)), sg.InputText('', key='Station Municipality')],
            [sg.Text('Station State', size=(15, 1)), sg.InputText('', key='Station State')],
            [sg.Text('Station Zip Code', size=(15, 1)), sg.InputText('', key='Station Zip Code')],
            [sg.Button("OK")],
            [sg.Button("Cancel")],

        ]
        # window = sg.Window(title="KOA Management Console Login", layout=layout2, margins=(500, 500)).read()
        window = sg.Window(title="KOA Management Console Add Station", layout=layout)

        # label = tk.Label(text="KOA Management Console", fg="white", bg="black")
        # label.pack()
        # window.mainloop()
        while True:
            event, values = window.read()
            # End program if user closes window or
            # presses the OK button
            if event == "OK":
                # df = [values["Station Name"],values["Station Street"], values["Station Municipality"], values["Station State"], values["Station Zip Code"]]
                # convert_dict = df.to_dict(orient="records")
                weatherDict = {"name": values["Station Name"], "street": values["Station Street"],
                               "municipality": values["Station "
                                                      "Municipality"],
                               "state": us_state_to_abbrev[values["Station State"]],
                               "zip code": values["Station Zip Code"]}
                db.WeatherStations.insert_one(weatherDict)
                break
            if event == "Cancel":
                window.close()
        window.close()

    # Opens the main dashboard that the user first sees after login, presenting to them a menu of options.
    def openWelcomeScreen(self, stations):
        username = (self.getCurrentUser())
        layout = [
            [sg.Text("Welcome to the Management Dashboard, " + username.capitalize() + '.')],
            [sg.Text("Select Weather Station:")],
            [sg.Listbox(values=stations, select_mode='SINGLE', key='fac', size=(30, 6),
                        tooltip='Select a weather station to modify.')],
            [sg.Text("Select a menu option:")],
            [sg.Radio('Add Station', "RADIO1", default=False, key="-ADD-")],
            [sg.Radio('Modify Station', "RADIO1", default=False, key="-MODIFY-")],
            [sg.Button("OK")],
        ]
        # margins=(500, 500)
        window = sg.Window(title="KOA Management Console", layout=layout, )

        print('Username: ' + self.getCurrentUser())
        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED or event == "Exit":
                break
            elif values["-ADD-"]:
                print("Add is selected.")
                self.openAddStation()

    # Returns all the weather stations.
    def getSensors(self):
        return appWindowMain.stations

    # Returns the current registered user utilizing the console.
    def getCurrentUser(self):
        return self._userName

    def genSalt(self):

        # Open in "wb" mode to
        # write a new file, or
        # "ab" mode to append
        if not os.path.isfile("saltFile.txt"):
            with open("saltFile.txt", "wb") as binary_file:
                # Write bytes to file
                salt = bcrypt.gensalt()
                print("Salt: ", salt)

                binary_file.write(salt)
                print("Wrote salt file in ", os.getcwd())
        else:
            print("Salt file found.")

    # Retrieves the salt hash and returns the object.
    def getSalt(self):
        saltFile = open("saltFile.txt", "rb")
        salt = saltFile.read()
        saltFile.close()
        # listSaltByte = list(salt)
        # print("Retrieved salt from file. Salt: ", listSaltByte)
        return salt


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

windowMain = appWindowMain()
windowMain.genSalt()
windowMain.getSalt()
# windowMain.genTestStations()
windowMain.openLoginScreen()
# TODO: needs user verification prior to launching.
windowMain.openWelcomeScreen(windowMain.getSensors())
