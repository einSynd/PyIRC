import json
replyList = {}

def reloadReplies(*args):
    global replyList
    replyList = {}
    loadReplies()
    return "Replies reloaded."

def loadReplies():
    global replyList
    with open("responder/responses.txt", "r") as respondFile:
        replyList = json.load(respondFile)

def findReply(text):
    if replyList == {}:
        loadReplies()
    
    for key in replyList:
        if text.lower().find(key) > -1:
            return replyList[key]
