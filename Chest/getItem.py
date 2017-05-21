#!/usr/bin/env python
import os
import sys
import re
import random
import csv

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

#Load weapon CSV, split into weapon name and chance name, and
#   skip any weapons that start on floors after the chosen one
def loadWeaponList(floorNum):
    name = []
    chance = []
    type = "Weapon"
    
    fileName = getFileName(type)
    if type == -1:
        return
    
    with open(fileName, "r") as csvfile:
        fileReader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in fileReader:
            startFloor = int(row[1])
            if startFloor <= floorNum:
                name.append(row[0])
                tempChance = row[2]
                chance.append(float(tempChance[:-1]))
    
    return name, chance

#Load armor CSV, split into armor name and chance name, and
#   skip any armors that start on floors after the chosen one.
#   Extra difficulty added due to the floor 9 bug where most things
#   stop showing up.
def loadArmorList(floorNum):
    name = []
    chance = []
    type = "Armor"
    
    fileName = getFileName(type)
    if type == -1:
        return
    
    #Armor CSV: name, start1, end1, start2, end2, chance
    #   start1/end1 are for floors 1-9, start2-end2 are for floors 10-98;
    #   There's a bug where many armor types don't show up past floor 9.
    with open(fileName, "r") as csvfile:
        fileReader = csv.reader(csvfile, delimiter=",", quotechar="|")
        for row in fileReader:
            #Check for floor 9 or higher only equips
            if floorNum <= 9:
                startFloor = int(row[1])
                if startFloor != 0 and floorNum >= startFloor:
                    name.append(row[0])
                    tempChance = row[5]
                    chance.append(float(tempChance[:-1]))
            #Floors 10 or lower
            else:
                startFloor = int(row[3])
                if startFloor != 0 and floorNum >= startFloor:
                    name.append(row[0])
                    tempChance = row[5]
                    chance.append(float(tempChance[:-1]))
    
    return name, chance

#Load any of the other CSVs, split into weapon name and chance name.
#   These can be found on any floor.
def loadBasicList(type):
    name = []
    chance = []
    
    fileName = getFileName(type)
    if type == -1:
        return
    
    with open(fileName, "r") as csvfile:
        fileReader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in fileReader:
            name.append(row[0])
            tempChance = row[1]
            chance.append(float(tempChance[:-1]))
    
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
        pickedNames, pickedChances = loadArmorList(floorNum)
    elif pickedCat == "Weapon":
        pickedNames, pickedChances = loadWeaponList(floorNum)
    else:
        pickedNames, pickedChances = loadBasicList(pickedCat)
    
    #Use name and chance arrays to pick a weighted item
    chosenDrop = random.choices(pickedNames, pickedChances)[0]
    #Print drop's name
    return floorNum, floorInfo, chosenDrop

if __name__ == "__main__":
    forcedCat = "Armor"
    print(pickAnItem())
    print(pickAnItem())
    print(pickAnItem())
    print(pickAnItem())
    print(pickAnItem())