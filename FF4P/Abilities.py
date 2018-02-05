import os
import csv
abilityList = {}

#Function for the chat command "abilityreload"
#No arguments
def abilityreload(*arg):
    reloadAbilities()

#Function for the chat command "ability"
#One argument, an ability to search for
def ability(input, user):
    if input:
        return getAbility(input)
    else:
        return "No ability to search for was given."

def loadAbilities():
    global abilityList
    fileName = "FF4P/FF4P_Abil.csv"
    if not os.path.exists(fileName):
        fileName = "FF4P_Abil.csv"
    
    with open(fileName, 'r') as csvFile:
        abilityReader = csv.reader(csvFile, delimiter=',', quotechar='|')
        i = 0
        for row in abilityReader:
            abilityList[i] = row
            i += 1

def reloadAbilities():
    loadAbilities()
    print("Abilities reloaded.")

def getAbility(name):
    if abilityList == {}:
        loadAbilities()
    
    none = ["none"]
    for _,ability in abilityList.items():
        if ability[0].lower() == name.lower():
            return ability
    
    return none