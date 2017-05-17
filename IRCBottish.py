#!/usr/bin/env python
import socket
import os
import sys
import re
import random
from threading import Timer

dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)


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

#enable/disable toggle for modules
modules = {"FF4P": "enabled", "Responder": "enabled", "Chest": "enabled"}

#Message for non-privileged users trying to run privileged commands, picked at random
denial = ["Wash your face and try again, %s.", "You're not allowed to touch me, %s!"]

def unknownMsg(data):
    print(data)

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
    
    #Check if responder module is enabled
    if modules["Responder"] == "enabled":
        #Check if responder module is loaded
        try:
            from Responder import Reply
        except:
            print("Responder module not found.")
            return
        
        #Check for a responder message in the text and reply if found
        toRespond = Reply.findReply(text)
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
    if dataParts[0].find("!") > -1:
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

#A message started with the command character, check if it's actually a command
def cmdRequest(user, channel, text):
    global admin, allowedUsers, floodProtection, antiFlood, modules
    
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
    
    #List of admin commands to prevent running an if on cmd 100 times
    adminCmd = ["debug", "join", "part", "quit", "adduser", "deluser", "antiflood"]
    
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
                        floodProtection = float(30)
                        if int(args) == 0:
                            sendPrivMsg(channel, "Anti-Flood timer disabled.")
                        else:
                            sendPrivMsg(channel, "Anti-Flood timer set to %s seconds." % args)
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
        #Admin command but user is not admin
        else:
            rando = random.randint(0,len(denial)-1)
            sendMsg("PRIVMSG %s :" % (channel) + denial[rando] % (user))
        return

    #List of mod commands to avoid running an if on cmd 100 times
    modCmd = ["abilityreload", "reply", "module"]
    #List of mods in lowercase
    privLower = [name.lower() for name in allowedUsers]
    
    #privileged but not admin commands
    if cmd.lower() in modCmd:
        if user.lower() in privLower:
            #Reloads the list of abilities from the FF4P plugin
            #   CSV can be edited and reloaded so bot doesn't have to restart for minor changes
            if cmd.lower() == "abilityreload":
                if modules["FF4P"] == enabled:
                    try:
                        from FF4P import Abilities
                    except ModuleNotFoundError:
                        sendPrivMsg(channel,"FF4P Module not found")
                        return
                    
                    Abilities.reloadAbilities()
                    sendPrivMsg(channel, "FF4P abilities reloaded.")
                else:
                    sendPrivMsg(channel, "FF4P module is disabled.")
            
            #Enables or disables the responder, or reloads its response list
            #   from CSV so minor changes don't require restart
            if cmd.lower() == "reply":
                
                if args == "off":
                    modules["Responder"] = "disabled"
                    sendPrivMsg(channel, "Responder disabled.")
                
                elif args == "on":
                    modules["Responder"] = "enabled"
                    sendPrivMsg(channel, "Responder enabled.")
                
                elif args == "reload":
                    if modules["Responder"] == "enabled":
                        try:
                            from Responder import Reply
                        except:
                            sendPrivMsg(channel, "Responder Module not found")
                            return
                        
                        Reply.reloadReplies()
                        sendPrivMsg(channel, "Replies reloaded.")
                    else:
                        sendPrivMsg(channel, "Responder Module is disabled, must be enabled to reload.")
                
                else:
                    sendPrivMsg(channel, "Responder is currently %s. Valid input is 'on' or 'off'." %(modules["Responder"]))
            
            #Enable or disable modules
            if cmd.lower() == "module":
                if args == "":
                    moduleList = ' '.join(['%s: %s;' % (key, value) for (key, value) in modules.items()])
                    sendPrivMsg(channel, "Current modules - %s" % (moduleList[:-1]))
                    return
                args = args.split(" ")
                if len(args) > 2:
                    sendPrivMsg(channel, "Invalid command, format is 'module moduleName [enabled/disabled]'")
                elif len(args) == 1:
                    try:
                        status = modules[args[0]]
                    except KeyError:
                        sendPrivMsg(channel, "Module does not exist: %s" %(args[0]))
                        return
                    sendPrivMsg(channel, "%s module is %s" % (args[0], status))
                else:
                    args[1] = str(args[1]).lower()
                    if args[1] == "enabled" or args[1] == "disabled":
                        try:
                            status = modules[args[0]]
                        except KeyError:
                            sendPrivMsg(channel, "Module does not exist: %s" %(args[0]))
                            return
                        modules[args[0]] = args[1]
                        sendPrivMsg(channel, "%s module is now %s" % (args[0], args[1]))
                    else:
                        sendPrivMsg(channel, "Invalid argument: %s, must be 'enable' or 'disable'" % (args[1]))
            
        #privileged command but user is not privileged
        else:
            print("Mod Denial")
            rando = random.randint(0,len(denial)-1)
            sendMsg("PRIVMSG %s :" % (channel) + denial[rando] % (user))
        return

    #Public Commands
    if antiFlood == 1:
        return
    cmdRan = 0
    
    #Silly command to call someone or something a butt
    if cmd == "butt" and args != "":
        isAre = "is"
        if args.find("and") > -1:
            isAre = "are"
        sendPrivMsg(channel,"%s %s indeed a butt." % (args, isAre))
        cmdRan = 1
    
    #Gets an item at random from the chest module
    if cmd == "chest":
        if modules["Chest"] == enabled:
            try:
                from Chest import getItem
            except ModuleNotFoundError:
                sendPrivMsg(channel, "Chest Module not found")
                return
            
            floorNum, floorInfo, item = getItem.pickAnItem()
            formatted = "%s found '%s' on floor %s" % (user, item, floorNum)
            sendPrivMsg(channel, formatted)
        else:
            sendPrivMsg(channel, "Chest module is disabled.")
        cmdRan = 1
    
    #Gets an ability from the FF4P module
    if cmd == "ability" and args != "":
        if modules["FF4P"] == "enabled":
            try:
                from FF4P import Abilities
            except ModuleNotFoundError:
                sendPrivMsg(channel,"FF4P Module not found")
                return
            
            found = Abilities.getAbility(args)
            if len(found) > 1:
                name = found[0]
                desc = found[1]
                cost = found[3]
                loc  = found[4]
                slot = found[5]
                if len(found) > 6:
                    coin = found[6]
                    formatted = "%s: %s - %s AP - %s in %s (%s coins)" % (name, desc, cost, slot, loc, coin)
                else:
                    formatted = "%s: %s - %s AP - %s in %s" % (name, desc, cost, slot, loc)
                sendPrivMsg(channel, formatted)
            else:
                sendPrivMsg(channel, "Not found")
        else:
            sendPrivMsg(channel, "FF4P module is disabled.")
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
        funcToRun = messageType.get(dataParts[1], unknownMsg)
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

        if data.find("376 " + nick) > -1:
            sendMsg("JOIN %s" % (startChannel))