#!/usr/bin/env python
import os
import sys
import re
import random
import csv

#Function for the chat command 'chest'
#One argument, user
def chest(input, user):
    floorNum, floorInfo, item = pickAnItem()
    formatted = "{} found '{}' on floor {}".format(user, item, floorNum)
    return formatted

itemDicts = {"Armor": {}, "Blue": {}, "Other": {}, "Healing": {},
                "Spells": {}, "Weapon": {}, "Iris": {} }

#List all of the CSV files by category, minus .csv
fileDict = {"Armor": "Armor", "Blue": "Blue Treasure", "Other": "Other Usables",
            "Healing": "Restorative Usables", "Spells": "Spells", "Weapon": "Weapons",
            "Iris": "Iris Treasure"}

#Set up friendly names to print to string per category
friendlyName = {"Armor": "a piece of armor", "Blue": "a blue treasure",
                "Iris": "an Iris treasure", "Other": "a miscellaneous item",
                "Healing": "a healing item", "Spells": "a spell", "Weapon": "a weapon"}

#List of categories and their relative weights
categories = ["Armor", "Blue", "Iris", "Other", "Healing", "Spells", "Weapon"]
catWeights = [17.57, 1.95, 1.95, 14.06, 22.66, 11.72, 32.03]

def getFileName(type):
    fileName = "Chest/" + fileDict[type] + ".csv"
    if not os.path.exists(fileName):
        fileName = fileDict[type] + ".csv"
    if not os.path.exists(fileName):
        print(type + "CSV not found")
        return -1
    return fileName

#Receives weapon information and returns a list of weapons and chances based on floor number
def pickFloorItem(floorNum, name, chance, floors):
    availableNames = []
    availableChances = []
    excluded = 0
    
    for index in range(len(floors)):
        if floors[index] != 0 and floors[index] <= floorNum:
            availableNames.append(name[index])
            availableChances.append(chance[index])
        else:
            excluded += 1
    
    return availableNames, availableChances

#Load weapon CSV if not already loaded and split into weapon name, chance name, and floor number
def getWeaponList():
    name = []
    chance = []
    floors = []
    
    type = "Weapon"
    
    if "chance" in itemDicts[type]:
        name = itemDicts[type]["name"]
        chance = itemDicts[type]["chance"]
        floors = itemDicts[type]["floors"]
    else:
        fileName = getFileName(type)
        if type == -1:
            return ["File not found"], [1]
        
        with open(fileName, "r") as csvfile:
            fileReader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in fileReader:
                name.append(row[0])
                floors.append(int(row[1]))
                
                tempChance = row[2]
                chance.append(float(tempChance[:-1]))
                
        itemDicts[type]["name"] = name
        itemDicts[type]["chance"] = chance
        itemDicts[type]["floors"] = floors
    
    return name, chance, floors

#Load armor CSV, split into armor name and chance name, and
#   skip any armors that start on floors after the chosen one.
#   Extra difficulty added due to the floor 9 bug where most things
#   stop showing up.
def getArmorList(floorNum):
    name = []
    chance = []
    floors = []
    
    type = "Armor"
    
    #Checked for arrays already loaded
    if floorNum < 10 and "1-9" in itemDicts[type]:
        #print("Armor on floors 1-9 is cached.")
        name = itemDicts[type]["1-9"]["name"]
        chance = itemDicts[type]["1-9"]["chance"]
        floors = itemDicts[type]["1-9"]["floors"]
        
    elif floorNum > 9 and "10+" in itemDicts[type]:
        #print("Armor on floors 10-98 is cached.")
        name = itemDicts[type]["10+"]["name"]
        chance = itemDicts[type]["10+"]["chance"]
        floors = itemDicts[type]["10+"]["floors"]
        
    else:
        #Armor for the proper floor isn't cached, load it.
        fileName = getFileName(type)
        if type == -1:
            return ["File not found"], [1]
        
        #Armor CSV: name, start1, start2, chance
        #   start1 is for floors 1-9, start2 is for floors 10-98; 
        #   There's a bug where many armor types don't show up past floor 9.
        #   start of 0 means not available
        
        with open(fileName, "r") as csvfile:
            fileReader = csv.reader(csvfile, delimiter=",", quotechar="|")
            for row in fileReader:
                #Floors 1-9
                if floorNum < 10:
                    startFloor = int(row[1])
                    #If it doesn't start on floor 0, then it's in this range
                    if startFloor != 0:
                        name.append(row[0])
                        floors.append(startFloor)
                        tempChance = row[3]
                        chance.append(float(tempChance[:-1]))
                #Floors 10 or lower
                else:
                    startFloor = int(row[2])
                    #If it doesn't start on floor 0, then it's in this range
                    if startFloor != 0 :
                        name.append(row[0])
                        floors.append(startFloor)
                        tempChance = row[3]
                        chance.append(float(tempChance[:-1]))
        
        if floorNum < 10:
            itemDicts[type]["1-9"] = {}
            itemDicts[type]["1-9"]["name"] = name
            itemDicts[type]["1-9"]["chance"] = chance
            itemDicts[type]["1-9"]["floors"] = floors
        else:
            itemDicts[type]["10+"] = {}
            itemDicts[type]["10+"]["name"] = name
            itemDicts[type]["10+"]["chance"] = chance
            itemDicts[type]["10+"]["floors"] = floors
    
    return name, chance, floors

#Load any of the other CSVs, split into weapon name and chance name.
#   These can be found on any floor.
def getBasicList(type):
    name = []
    chance = []
    
    #Check if the dict for that item type has stats already loaded
    if "chance" in itemDicts[type]:
        #print("Item type %s is cached." % (type))
        name = itemDicts[type]["name"]
        chance = itemDicts[type]["chance"]
    else:
        #No stats, so load the CSV
        fileName = getFileName(type)
        
        if type == -1:
            return ["File not found"], [1]
            
        with open(fileName, "r") as csvfile:
            fileReader = csv.reader(csvfile, delimiter=',', quotechar='|')
            for row in fileReader:
                name.append(row[0])
                tempChance = row[1]
                chance.append(float(tempChance[:-1]))
        
        itemDicts[type]["chance"] = chance
        itemDicts[type]["name"] = name
    
    return name, chance

#Main function, with an optional parameter to force a category
def pickAnItem(forcedCat = "None"):
    #Pick a weighted category
    if forcedCat == "None":
        pickedCat = random.choices(categories,catWeights)[0]
    else:
        pickedCat = forcedCat
    #Pick a floor at random
    #TODO: Maybe weight more towards early floors?
    floorNum = random.randint(1,98)
    #Print floor and category using friendly names
    floorInfo = "You're on floor %s and found %s!" % (str(floorNum), friendlyName[pickedCat])
    
    #Load the arrays from file
    if pickedCat == "Armor":
        name, chance, floors = getArmorList(floorNum)
        pickedNames, pickedChances = pickFloorItem(floorNum, name, chance, floors)
    elif pickedCat == "Weapon":
        name, chance, floors = getWeaponList()
        pickedNames, pickedChances = pickFloorItem(floorNum, name, chance, floors)
    else:
        pickedNames, pickedChances = getBasicList(pickedCat)
    
    #Use name and chance arrays to pick a weighted item
    chosenDrop = random.choices(pickedNames, pickedChances)[0]
    
    #Return drop's information
    return floorNum, floorInfo, chosenDrop

if __name__ == "__main__":
    forcedCat = "Armor"
    print(pickAnItem(forcedCat))
    print(pickAnItem(forcedCat))
    print(pickAnItem(forcedCat))
    print(pickAnItem(forcedCat))
    print(pickAnItem(forcedCat))