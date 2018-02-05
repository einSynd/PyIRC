#!/usr/bin/env python
import socket
import os
import sys
import re
import random
from threading import Timer

dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

#Import the mandatory module ModLoader
from ModLoader import modLoader

#Run modLoader to get the modules as a dict from Modules.json
modules, modList = modLoader.loadModules()

server = "irc.rizon.net"
port = 6667
nick = "einElectro"
client = "Electro-Choc"
startChannel = "#einTest"
commandChar = "+"
#Number of seconds to trigger flood protection
floodProtection = float(5)
#1 after command runs, 0 after floodProtection seconds
antiFlood = 0

#Hard-coded admin command and privileged command lists
#Allowed users can be added on the fly while running, but currently does not save
#Admins can only be hard-coded for now for safety
admin = ["einSynd", "einSyndication", "Jitterskull"]
allowedUsers = ["chirico", "Chocolate", "BROVIETTO", "DynamicDonut", "Albs"]
allowedUsers += admin

#Message for non-privileged users trying to run privileged commands, picked at random
denial = ["Wash your face and try again, %s.", "You're not allowed to touch me, %s!"]

#All messages come here, be it PMs or channel messages
def privMsg(data):
    user = data[1:].split("!")[0]
    
    text = data.split("PRIVMSG ")[1]
    channel = text.split(" ")[0]
    text = text[len(channel) + 2:]
    
    #Check for /me and print it nicely
    if text[:7] == "/ACTION":
        print("* " + user + "@" + channel + " " + text[8:-1])
    else:
        print(user + "@" + channel + ": " + text)
    #Check for the command character as first letter
    if text[:1] == commandChar:
        cmdRequest(user, channel, text[1:])
    
    #Check if responder.reply exists
    if "Reply" in modules:
        #Check if responder module is enabled
        if modList["Responder"]["enabled"]:
            
            #Check for a responder message in the text and reply if found
            toRespond = getattr(modules["Reply"], "findReply")(text)
            if toRespond:
                toRespond = toRespond.replace("%user%", user)
                sendPrivMsg(channel, toRespond)

#Notice was sent, print nicer
def notice(data):
    user = data[1:].split("!")[0]
    text = data.split("NOTICE")[1]
    print("(NOTICE) " + user + ": " + text)

#User changed name, print nicely
def nickChange(data):
    user = data[1:].split("!")[0]
    change = data.split("NICK :")[1]
    print(user + " is now " + change)

#User joined, print nicely
def userJoin(data):
    user = data[1:].split("!")[0]
    channel = data.split("JOIN :")[1]
    print(user + " has joined " + channel)

#User left, print nicely with their message
def userQuit(data):
    user = data[1:].split("!")[0]
    message = data.split("QUIT :")[1]
    print(user + " has left " + server + ": " + message)

#Gets the mode string and prints it nicely
def userMode(data):
    dataParts = data[1:].split(" ")
    #Check if it's a user by looking for the ! sent with username
    if "!" in dataParts[0]:
        user = dataParts[0].split("!")[0]
    else:
        user = dataParts[0]
    channel = dataParts[2]
    mode = dataParts[3]

    target = ""
    #On empty channel join, the string has fewer parts.
    #On channel mode, the string ends with a space so there's an extra empty part.
    if len(dataParts) > 4:
        target = dataParts[4]
    if target == "":
        target = "the channel"
    print(user + "@" + channel  + " has given " + mode + " to " + target)

#Resets anti-flood variable via timer
def resetAntiFlood():
    global antiFlood
    #print("Resetting anti flood")
    antiFlood = 0

def handleModuleCommands(cmd, args, user, channel):
    global admin, allowedusers, modules, modList, antiFlood
    adminLower = [name.lower() for name in admin]
    privLower = [name.lower() for name in allowedUsers]
    
    if user.lower() in adminLower:
        userLevel = 2
    elif user.lower() in privLower:
        userLevel = 1
    else:
        userLevel = 0
    
    #Loop through mods in modList
    for mod, modVals in modList.items():
        #Check that it even has commands
        if "cmds" in modVals:
            
            #Don't bother checking if the module is disabled
            if not modVals["enabled"]:
                print("Module disabled")
                continue
            
            exists = [val for val in modVals["cmds"] if cmd in val.lower()]
            
            #Check if the command sent was in the current mod's command list
            if exists:
            
                #Get the command's name from the module list for proper capitalizaton
                cmd = exists[0]
                
                #Get the mod's name to use in "modules" dict and user level required to run
                modName = modVals["modName"]
                privLevel = modVals["cmds"][cmd]
                
                #Check that the user is high enough level to run the command
                if userLevel < privLevel:
                    sendPrivMsg(channel,"{} is not high enough level for this command.".format(user))
                    return
                
                #Check if we're in the anti-flood window if it's a public command
                if antiFlood == 1 and privLevel == 0:
                    return
                cmdRan = 0
                
                #Check that the module has the proper function
                #If so, get the function to run as a variable
                if hasattr(modules[modName], cmd):
                    func = getattr(modules[modName], cmd)
                    
                    #Run the function, returning what the function returns
                    #Send both extra input and the user, in case the function needs either one.
                    sendPrivMsg(channel, func(input, user))
                    if privLevel == 0:
                        cmdRan = 1
                    
                    #Set the flood protection if a public command ran
                    if cmdRan == 1 and floodProtection > 0 and antiFlood == 0:
                        #print("Setting flood protection")
                        antiFlood = 1
                        t = Timer(floodProtection, resetAntiFlood)
                        t.start()
                else:
                    sendPrivMsg(channel, "Module '{}' does not have '{}' defined as a function.".format(mod, cmd))
                    print("Module '{}' does not have '{}' defined as a function.".format(mod, cmd))
    
    
    

#A message started with the command character, check if it's actually a command
def cmdRequest(user, channel, text):
    global admin, allowedUsers, floodProtection, antiFlood, modules, modList
    
    #Get the first word as a command, everything else as one string of arguments
    dataParts = text.split(" ")
    if len(dataParts) > 1:
        cmd = dataParts[0]
        args = " ".join(dataParts[1:])
    else:
        cmd = text
        args = ""
    
    #Lowercase for easier checking
    cmd = cmd.lower()
    
    #List of built-in admin commands to prevent running an if on cmd 100 times
    adminCmd = ["debug", "join", "part", "quit", "adduser", "deluser", "antiflood", "reloadmods"]
    
    #List of admins in lowercase
    adminLower = [name.lower() for name in admin]
    
    #Admin commands
    if cmd in adminCmd:
        if user.lower() in adminLower:
            #Quick debug statement, showing allowed users
            if cmd == "debug":
                sendPrivMsg(user, "%s" % (allowedUsers))
                return
            
            #Gets or sets antiflood timer in seconds, 0 to disable
            if cmd == "antiflood":
                if args != "":
                    try:
                        floodProtection = float(args)
                        if int(args) == 0:
                            sendPrivMsg(channel, "Anti-Flood timer disabled.")
                            antiFlood = 0
                        else:
                            sendPrivMsg(channel, "Anti-Flood timer set to %s seconds." % args)
                            antiFlood = 0
                    except ValueError:
                        sendPrivMsg(channel, "%s is not a valid number of seconds." % args)
                else:
                    sendPrivMsg(channel, "Flood protection is currently %s seconds." % floodProtection)
            
            #Tells bot to join another channel
            if cmd == "join" and args != "":
                sendMsg("JOIN %s" % (args))
            
            #Tells bot to leave current channel
            if cmd == "part" and args != "":
                    sendMsg("PART %s :Requested by %s " % (args, user))
            
            #Shut down the bot
            if cmd == "quit":
                sendPrivMsg(channel, "Bye.")
                sendMsg("QUIT :Exiting")
                sock.close()
                print("Quit by request of " + user)
                sys.exit()
                return
            
            #Adds users for the privileged but non-mod commands
            if cmd == "adduser" and args != "":
                newUser = args
                if newUser in allowedUsers:
                    sendPrivMsg(channel, "%s is already an allowed user." % (newUser))
                else:
                    allowedUsers += [newUser]
                    sendPrivMsg(channel, "%s is now an allowed user." % (newUser))
                    print(allowedUsers)
            
            #Removes users for the privileged but non-mod commands
            if cmd == "deluser" and args != "":
                newUser = args
                if newUser in allowedUsers:
                    if newUser in admin:
                        sendPrivMsg(channel, "%s is an admin and cannot be removed." & (newUser))
                    else:
                        allowedUsers.remove(newUser)
                        sendPrivMsg(channel, "%s is no longer an allowed user." % (newUser))
                        print(allowedUsers)
                else:
                    sendPrivMsg(channel, "%s is not an allowed user anyway." % (newUser))
            
            #Calls the loadModules function again to reload the mods
            if cmd == "reloadmods":
                print("{} has reloaded the mods".format(user))
                sendPrivMsg(channel, "Reloading mods!")
                modules, modList = modLoader.reloadModules()
        #Admin command but user is not admin
        else:
            rando = random.randint(0,len(denial)-1)
            sendMsg("PRIVMSG %s :" % (channel) + denial[rando] % (user))
        return

    #List of mod commands to avoid running an if on cmd 100 times
    modCmd = ["reply", "module"]
    #List of mods in lowercase
    privLower = [name.lower() for name in allowedUsers]
    
    #privileged but not admin commands
    if cmd.lower() in modCmd:
        if user.lower() in privLower:

            #Enables or disables the responder, or reloads its response list
            #   Left in after mod loader just because it's a bit special
            #   but can also be done from "modules" command below or just "reloadModules" command
            if cmd.lower() == "reply":
                if "Responder" in modList:
                    if args == "off":
                        modList["Responder"]["enabled"] = False
                        sendPrivMsg(channel, "Responder disabled.")
                    
                    elif args == "on":
                        modList["Responder"]["enabled"] = True
                        sendPrivMsg(channel, "Responder enabled.")
                    
                    elif args == "reload":
                        if modList["Responder"]["enabled"]:
                            handleModuleCommands("reloadreplies", "", user, channel)
                        else:
                            sendPrivMsg(channel, "Responder Module is disabled, must be enabled to reload.")
                    else:
                        toReply = "disabled"
                        if modList["Responder"]["enabled"]:
                            toReply = "enabled"
                            
                        sendPrivMsg(channel, "Responder is currently %s. Valid input is 'on' or 'off'." %(toReply))
                else:
                    sendPrivMsg(channel, "Responder module not found.")
            
            #Enable or disable modules
            if cmd.lower() == "module":
                if args == "":
                    toPrint = ""
                    for mod, modVals in modList.items():
                        #If modVals is a string, not a dict, then modules failed to load
                        if isinstance(modVals, str):
                            sendPrivMsg(channel, "Modules not loaded. {}".format(modVals))
                            return
                        
                        status = "disabled"
                        if modVals["enabled"]:
                            status = "enabled"
                        toPrint = toPrint + "{}: {}; ".format(mod, status)
                        
                    sendPrivMsg(channel, "Current modules - %s" % (toPrint[:-2]))
                    return
                
                #Check that either one or two arguments were sent
                args = args.split(" ")
                
                #Check if the module exists, case-insensitive
                exists = [mod for mod in modList if args[0].lower() in mod.lower()]
                if not exists:
                    sendPrivMsg(channel, "Module {} does not exist.".format(args[0]))
                    return
                
                args[0] = exists[0]
                
                if len(args) > 2:
                    sendPrivMsg(channel, "Invalid command, format is 'module moduleName [enable/disable]'")
                
                elif len(args) == 1:
                #Only one argument, check if enabled or disabled
                    status = "disabled"
                    if modList[args[0]]["enabled"]:
                        status = "enabled"
                        
                    sendPrivMsg(channel, "%s module is %s" % (args[0], status))
                else:
                #Two arguments, enable or disable it
                    args[1] = str(args[1]).lower()
                    if args[1] == "enable" or args[1] == "on":
                        isEnabled = True
                    elif args[1] == "disable" or args[1] == "off":
                        isEnabled = False
                    else:
                        sendPrivMsg(channel, "Invalid argument: %s, must be 'enable' or 'disable'" % (args[1]))
                        return
                    
                    modList[args[0]]["enabled"] = isEnabled
                    sendPrivMsg(channel, "%s module is now %s" % (args[0], args[1]))
            
        #privileged command but user is not privileged
        else:
            print("Mod Denial")
            rando = random.randint(0,len(denial)-1)
            sendMsg("PRIVMSG %s :" % (channel) + denial[rando] % (user))
        return
    
    handleModuleCommands(cmd, args, user, channel)
    
    #Public Commands
    if antiFlood == 1:
        return
    cmdRan = 0
    
    #Silly command to call someone or something a butt
    if cmd == "butt" and args != "":
        isAre = "is"
        if "and" in args:
            isAre = "are"
        sendPrivMsg(channel,"%s %s indeed a butt." % (args, isAre))
        cmdRan = 1
    
    #Set the flood protection since a public command ran
    if cmdRan == 1 and floodProtection > 0 and antiFlood == 0:
            #print("Setting flood protection")
            antiFlood = 1
            t = Timer(floodProtection, resetAntiFlood)
            t.start()

#List of message types and the function to run when found
messageType = {
    "NOTICE": notice, 
    "PRIVMSG": privMsg,
    "NICK": nickChange,
    "QUIT": userQuit,
    "JOIN": userJoin,
    "MODE": userMode,
}

def processLog(data):
    #Strip trailing newlines
    data = data.rstrip("\r\n")
    #Version / Action / etc
    data = data.replace("\x01","/")
    #Bold
    data = data.replace("\x02","*")
    #Color code
    colorCodes = re.compile("\x03(?:\d{1,2}(?:,\d{1,2})?)?", re.UNICODE)
    data = colorCodes.sub("", data)
    #Underline
    data = data.replace("\x1F","_")
    #Reset to normal
    data = data.replace("\x0F","|")
    #Reverse?
    data = data.replace("\x16","[16]")
    
    #Split data by both space and \r\n; login ping request was being sent wrong
    dataParts = re.split('[ \r\n]', data)
    if dataParts[-2] == "PING":
        sendMsg("PONG " + dataParts[-1])
    elif len(dataParts) > 1:
        #Use the second word to find out what type of message it is and do its specific
        #   function, or basic print function if it's something else.
        funcToRun = messageType.get(dataParts[1], print)
        funcToRun(data)
    else:
        print(data)

#Sends a privmsg to given destination
def sendPrivMsg(destination, message):
    sendMsg("PRIVMSG %s :%s" % (destination, message))

#Sends a general message to the server
def sendMsg(message):
    sock.sendall((message + "\r\n").encode('utf-8'))
    if message[:4] != "PONG":
        print("Sending " + message)

if __name__ == "__main__":
    loginStr = "PASS NOPASS\r\nNICK %s\r\nUSER %s * * :%s\r\n" % (nick, nick, client)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(None)
    sock.connect((server, port))
    sock.sendall(loginStr.encode('utf-8'))
    
    while 1:
        data = ""
        data = sock.recv(4096)
        data = data.decode()
        processLog(data)

        if ("376 " + nick) in data:
            sendMsg("JOIN %s" % (startChannel))