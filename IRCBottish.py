#!/usr/bin/env python
import socket
import os
import sys
import re
from random import randint

dir_path = os.path.dirname(os.path.realpath(__file__))
os.chdir(dir_path)

admin = ["einSynd", "einSyndication", "Jitterskull"]
denial = ["Wash your face and try again, %s.", "You're not allowed to touch me, %s!"]
allowedUsers = ["chirico", "Chocolate", "BROVIETTO", "DynamicDonut", "Albs"]
allowedUsers += admin

server = "irc.rizon.net"
port = 6667
nick = "einElectro"
client = "Electro-Choc"
startChannel = "#einTest"
commandChar = "+"
responderStatus = "on"

def unknownMsg(data):
    print(data)

def privMsg(data):
    user = data[1:].split("!")[0]
    
    text = data.split("PRIVMSG ")[1]
    channel = text.split(" ")[0]
    text = text[len(channel) + 2:]
    
    if text[:7] == "/ACTION":
        print("* " + user + "@" + channel + " " + text[8:-1])
    else:
        print(user + "@" + channel + ": " + text)
    if text[:1] == commandChar:
        cmdRequest(user, channel, text[1:])
    
    try:
        from Responder import Reply
    except:
        print("Responder module not found.")
        return
    
    if responderStatus == "on":
        toRespond = Reply.findReply(text)
        if toRespond:
            toRespond = toRespond.replace("%user%", user)
            sendPrivMsg(channel, toRespond)

def notice(data):
    user = data[1:].split("!")[0]
    text = data.split("NOTICE")[1]
    print("(NOTICE) " + user + ": " + text)

def nickChange(data):
    user = data[1:].split("!")[0]
    change = data.split("NICK :")[1]
    print(user + " is now " + change)

def userJoin(data):
    user = data[1:].split("!")[0]
    channel = data.split("JOIN :")[1]
    print(user + " has joined " + channel)

def userQuit(data):
    user = data[1:].split("!")[0]
    message = data.split("QUIT :")[1]
    print(user + " has left " + server + ": " + message)

def userMode(data):
    user = data[1:].split("!")[0]
    dataParts = data.split(" ")
    channel = dataParts[2]
    mode = dataParts[3]
    target = dataParts[4]
    print(user + "@" + channel  + " has given " + mode + " to " + target)

def cmdRequest(user, channel, text):
    global admin, allowedUsers
    
    dataParts = text.split(" ")
    if len(dataParts) > 1:
        cmd = dataParts[0]
        args = " ".join(dataParts[1:])
    else:
        cmd = text
        args = ""
    
    cmd = cmd.lower()
    
    #List of admin commands to prevent running an if on cmd 100 times
    adminCmd = ["debug", "join", "part", "quit", "adduser", "deluser"]
    
    #List of admins in lowercase
    adminLower = [name.lower() for name in admin]
    
    #Admin commands
    if cmd in adminCmd:
        if user.lower() in adminLower:
            if cmd == "debug":
                sendPrivMsg(user, "%s" % (allowedUsers))
                return
            
            if cmd == "join" and args != "":
                sendMsg("JOIN %s" % (args))
            
            if cmd == "part" and args != "":
                    sendMsg("PART %s :Requested by %s " % (args, user))
            
            if cmd == "quit":
                sendMsg("QUIT :Exiting")
                sock.close()
                print("Quit by request of " + user)
                sys.exit()
                return
            
            if cmd == "adduser" and args != "":
                newUser = args
                if newUser in allowedUsers:
                    sendPrivMsg(channel, "%s is already an allowed user." % (newUser))
                else:
                    allowedUsers += [newUser]
                    sendPrivMsg(channel, "%s is now an allowed user." % (newUser))
                    print(allowedUsers)
                
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
        #Admin command but user not admin
        else:
            rando = randint(0,len(denial)-1)
            sendMsg("PRIVMSG %s :" % (channel) + denial[rando] % (user))

    #List of mod commands to avoid running an if on cmd 100 times
    modCmd = ["abilityreload", "reply"]
    #List of mods in lowercase
    privLower = [name.lower() for name in allowedUsers]
    
    #Priveleged but not admin commands
    if cmd.lower() in modCmd:
        if user.lower() in privLower:
            if cmd.lower() == "abilityreload":
                try:
                    from FF4P import Abilities
                except ModuleNotFoundError:
                    sendPrivMsg(channel,"FF4P Module not found")
                    return
                
                Abilities.reloadAbilities()
                sendPrivMsg(channel, "FF4P abilities reloaded.")
            
            if cmd.lower() == "reply":
                global responderStatus
                if args == "off":
                    responderStatus = "off"
                    sendPrivMsg(channel, "Responder disabled.")
                
                elif args == "on":
                    responderStatus = "on"
                    sendPrivMsg(channel, "Responder enabled.")
                
                elif args == "reload":
                    try:
                        from Responder import Reply
                    except:
                        sendPrivMsg(channel, "Responder Module not found")
                        return
                    
                    Reply.reloadReplies()
                    sendPrivMsg(channel, "Replies reloaded.")
                
                else:
                    sendPrivMsg(channel, "Responder is currently " + responderStatus + ". Valid input is 'on' or 'off'.")
            
        #Priveleged command but not priveleged
        else:
            print("Mod Denial")
            rando = randint(0,len(denial)-1)
            sendMsg("PRIVMSG %s :" % (channel) + denial[rando] % (user))

    #Public Commands
    if cmd == "butt" and args != "":
        isAre = "is"
        if args.find("and") > -1:
            isAre = "are"
        sendPrivMsg(channel,"%s %s indeed a butt." % (args, isAre))
    
    if cmd == "ability" and args != "":
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

messageType = {
    "NOTICE": notice, 
    "PRIVMSG": privMsg,
    "NICK": nickChange,
    "QUIT": userQuit,
    "JOIN": userJoin,
    "MODE": userMode,
}

def processLog(data):
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

def sendPrivMsg(destination, message):
    sendMsg("PRIVMSG %s :%s" % (destination, message))

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