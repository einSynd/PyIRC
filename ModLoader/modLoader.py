from importlib import import_module, reload
import json

#Load the modules
def loadModules():
    imported = {}
    modList = {}
    #File is "Modules.json" in the parent directory
    fileName = "Modules.json"
    with open(fileName, 'r') as modFile:
        modList = json.load(modFile)[0]
    
    for pkg, modVals in modList.items():
        modName = modVals["modName"]
        toImport = pkg + "." + modName
        #Try to import the library
        try:
            __temp = import_module(toImport)
            #Save the module to the 'imported' dict to return
            imported[modName] = __temp
            
        except:
            print("Module '{}.{}' not found.".format(pkg, modName))
    
    #Return both the imported modules and the parsed list to check for and run commands
    return imported, modList

#Reload the modules, then run through another load to catch any newly-added modules
def reloadModules():
    #Load the modules again to pick up new additions
    modules, modList = loadModules()
    
    #Reload all the mods
    for mod,pkg in modules.items():
        modules[mod] = reload(pkg)
    
    return modules, modList
    