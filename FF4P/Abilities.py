import csv
abilityList = {}

def loadAbilities():
    global abilityList
    with open('FF4/FF4Abil.csv', 'r') as csvFile:
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