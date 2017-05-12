import json
replyList = {}

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


def reloadReplies():
    global replyList
    replyList = {}
    loadReplies()