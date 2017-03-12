import requests
import os
import json
import time

APP_ID = "Vj8pQggXLhLy0WHahglCD4N1nAkkXQtGYpq2HrHD7H1nvmbT55KqtN6RSF4ILB/i"
LOCALE = "en"

HOST_URI = "myqexternal.myqdevice.com"
LOGIN_ENDPOINT = "api/v4/User/Validate"
DEVICE_LIST_ENDPOINT = "api/v4/UserDeviceDetails/Get"
DEVICE_SET_ENDPOINT = "api/v4/DeviceAttribute/PutDeviceAttribute"

INVONAME  = os.environ['inv_name']
USERNAME  = os.environ['username']
PASSWORD  = os.environ['password']
SKILL_ID  = os.environ['skill_id']
NO_OPEN   = os.environ['no_open']

myq_userid                  = ""
myq_security_token          = ""
myq_device_id               = []

def lambda_handler(event, context):

    failFunc = "N"

    if (INVONAME == ""):
        print("inv_name environment variable cannot be blank and needs to be set to your Alexa Skill's Invocation Name")
        failFunc = "Y"
        
    if (USERNAME == ""):
        print("username environment variable cannot be blank and needs to be set to your MyQ username")
        failFunc = "Y"
        
    if (PASSWORD == ""):
        print("password environment variable cannot be blank and needs to be set to your MyQ password")
        failFunc = "Y"

    if (SKILL_ID == ""):
        print("skill_id environment variable cannot be blank and needs to be set to your Alexa Skill's Application ID")
        failFunc = "Y"
        
    if (failFunc == "Y"):
        raise

    if event['session']['application']['applicationId'] != SKILL_ID:
        print "Invalid Application ID"
        raise
    else:
        # Not using sessions for now
        sessionAttributes = {}

        login()
        get_device_id()

        if event['session']['new']:
            onSessionStarted(event['request']['requestId'], event['session'])
        if event['request']['type'] == "LaunchRequest":
            speechlet = onLaunch(event['request'], event['session'])
            response = buildResponse(sessionAttributes, speechlet)
        elif event['request']['type'] == "IntentRequest":
            speechlet = onIntent(event['request'], event['session'])
            response = buildResponse(sessionAttributes, speechlet)
        elif event['request']['type'] == "SessionEndedRequest":
            speechlet = onSessionEnded(event['request'], event['session'])
            response = buildResponse(sessionAttributes, speechlet)

        # Return a response for speech output
        return(response)


def open(device):
    change_door_state(device, "open")

def close(device):
    change_door_state(device, "close")

def status(device):
    state = check_door_state(device)

    if state == "1":
        state_desc = "open"
    elif state == "2":
        state_desc = "closed"
    elif state == "3":
        state_desc = "stopped"
    elif state == "4":
        state_desc = "opening"
    elif state == "5":
        state_desc = "closing"
    elif state == "8":
        state_desc = "moving"
    elif state == "9":
        state_desc = "open"
    else:
        state_desc = "unknown"
        
    print("Check Door State: " + str(myq_device_id[device]) + " is " + state_desc)
    
    return state_desc
    

def login():

    global myq_userid
    global myq_security_token

    params = {
        'username': USERNAME,
        'password': PASSWORD
    }

    login = requests.post(
            'https://{host_uri}/{login_endpoint}'.format(
                host_uri=HOST_URI,
                login_endpoint=LOGIN_ENDPOINT),
                json=params,
                headers={
                    'MyQApplicationId': APP_ID
                }
        )

    myq_security_token = login.json()['SecurityToken']

def change_door_state(device, command):
    open_close_state = 1 if command.lower() == "open" else 0

    payload = {
        'attributeName': 'desireddoorstate',
        'myQDeviceId': myq_device_id[device],
        'AttributeValue': open_close_state,
    }
    
    device_action = requests.put(
        'https://{host_uri}/{device_set_endpoint}'.format(
            host_uri=HOST_URI,
            device_set_endpoint=DEVICE_SET_ENDPOINT),
            data=payload,
            headers={
                'MyQApplicationId': APP_ID,
                'SecurityToken': myq_security_token
            }
    )

    print("Change Door State: " + str(myq_device_id[device]) + " to " + command)
    
    return device_action.status_code == 200
    
    
def get_devices():

    device_list = requests.get(
        'https://{host_uri}/{device_list_endpoint}'.format(
            host_uri=HOST_URI,
            device_list_endpoint=DEVICE_LIST_ENDPOINT),
            headers={
                'MyQApplicationId': APP_ID,
                'SecurityToken': myq_security_token
            }
    )
    
    return device_list.json()['Devices']

def get_device_id():
      
    global myq_device_id
    
    myq_device_id = []
   
    devices = get_devices()    
    for dev in devices:
        if dev["MyQDeviceTypeName"] in ["VGDO", "GarageDoorOpener", "Garage Door Opener WGDO"]:
            myq_device_id.append(str(dev["MyQDeviceId"]))
            print("MyQDeviceTypeName:" + str(dev["MyQDeviceTypeName"]))
            print("MyQDeviceId:" + str(dev["MyQDeviceId"]))
            print("Number of Devices:" + str(len(myq_device_id)))

def check_door_state(device):

    devices = get_devices()    
    for dev in devices:
        if str(dev["MyQDeviceId"]) == str(myq_device_id[device]):
            for attribute in dev["Attributes"]:
                if attribute["AttributeDisplayName"] == "doorstate":
                    door_state = attribute['Value']
    
    return door_state    

# Called when the session starts
def onSessionStarted(requestId, session):
    print("onSessionStarted requestId=" + requestId + ", sessionId=" + session['sessionId'])

# Called when the user launches the skill without specifying what they want.
def onLaunch(launchRequest, session):
    # Dispatch to your skill's launch.
    getWelcomeResponse()

# Called when the user specifies an intent for this skill.
def onIntent(intentRequest, session):
    intent = intentRequest['intent']
    intentName = intentRequest['intent']['name']

    # Dispatch to your skill's intent handlers
    if intentName == "StateIntent":
        return stateResponse(intent)
    elif intentName == "MoveIntent":
        return moveIntent(intent)
    elif intentName == "HelpIntent":
        return getWelcomeResponse()
    else:
        print "Invalid Intent (" + intentName + ")"
        raise

# Called when the user ends the session.
# Is not called when the skill returns shouldEndSession=true.
def onSessionEnded(sessionEndedRequest, session):
    # Add cleanup logic here
    print "Session ended"

def getWelcomeResponse():
    cardTitle = "Welcome"
    
    if (NO_OPEN.upper() == "Y") or (NO_OPEN.upper() == "YES"):
        speechOutput = "You can close your garage door by saying, ask " + INVONAME + " door one to close.  You can also check the state of your garage door by saying, ask " + INVONAME + " if door one is open"

        # If the user either does not reply to the welcome message or says something that is not
        # understood, they will be prompted again with this text.
        repromptText = "Ask me to close your garage door by saying, ask " + INVONAME + " door one to close, or ask me to check the state of your garage door by saying, ask " + INVONAME + " if door one is open"   
    else:
        speechOutput = "You can open your garage door by saying, ask " + INVONAME + " door one to open, or you can close your garage door by saying, ask " + INVONAME + " door one to close.  You can also check the state of your garage door by saying, ask " + INVONAME + " if door one is open"
        repromptText = "Ask me to open your garage door by saying, ask " + INVONAME + " door one to open, or ask me to close your garage door by saying, ask " + INVONAME + " door one to close.  You can also ask me to check the state of your garage door by saying, ask " + INVONAME + " if door one is open"
        
    shouldEndSession = True

    return (buildSpeechletResponse(cardTitle, speechOutput, repromptText, shouldEndSession))

def moveIntent(intent):
    # Ask garage {door|door 1|door 2} to {open|close|shut|go up|go down}
    #     "intent": {
    #       "name": "StateIntent",
    #       "slots": {
    #         "doornum": {
    #           "name": "doornum",
    #           "value": "1"
    #         }    
    #         "doorstate": {
    #           "name": "doorstate",
    #           "value": "close"
    #         }
    #       }
    #     }
    
    if (NO_OPEN.upper() == "Y") or \
       (NO_OPEN.upper() == "YES"):
       
        failureMsg  = "I didn't understand that. You can close your garage door by saying, ask " + INVONAME + " door one to close"
        repromptMsg = "Ask me to close your garage door by saying, ask " + INVONAME + " door one to close"
        
    else:
        failureMsg  = "I didn't understand that. You can open your garage door by saying, ask " + INVONAME + " door one to open, or you can close your garage door by saying, ask " + INVONAME + " door one to close"
        repromptMsg = "Ask me to open your garage door by saying, ask " + INVONAME + " door one to open, or ask me to close your garage door by saying, ask " + INVONAME + " door one to close"
    
    try:  
        doornum = intent['slots']['doornum']['value']
        
        if (doornum == "door") or \
           (doornum == "door 1") or \
           (doornum == "1"):
           
            device = 0
            
        elif (doornum == "door 2") or \
             (doornum == "door to") or \
             (doornum == "2") or \
             (doornum == "to"):
             
            device = 1
            
        else:
            speechOutput = failureMsg
            cardTitle = "Try again" 
            repromptText = repromptMsg
            shouldEndSession = False
            return(buildSpeechletResponse(cardTitle, speechOutput, repromptText, shouldEndSession))        
                
        if (intent['slots']['doorstate']['value'] == "close") or \
           (intent['slots']['doorstate']['value'] == "shut") or \
           (intent['slots']['doorstate']['value'] == "down"):
           
            close(device)
            print("Closing...")
            speechOutput = "Ok, closing garage " + doornum + " now"
            cardTitle = "Closing your garage door"
            
        elif (intent['slots']['doorstate']['value'] == "open") or \
             (intent['slots']['doorstate']['value'] == "up"):
             
            if (NO_OPEN.upper() == "Y") or \
               (NO_OPEN.upper() == "YES"):
               
                speechOutput = failureMsg
                cardTitle = "Try again"
                
            else:
                open(device)
                print("Opening...")
                speechOutput = "Ok, opening garage " + doornum + " now"
                cardTitle = speechOutput
        else:
            speechOutput = failureMsg
            cardTitle = "Try again"
            
        repromptText = repromptMsg
        shouldEndSession = True

        return(buildSpeechletResponse(cardTitle, speechOutput, repromptText, shouldEndSession))
    
    except:
        speechOutput = failureMsg
        cardTitle = "Try again" 
        repromptText = repromptMsg
        shouldEndSession = False
        return(buildSpeechletResponse(cardTitle, speechOutput, repromptText, shouldEndSession))        
    

def stateResponse(intent):
    # Ask garage if {door|door 1|door 2} is {open|up|close|closed|shut|down}
    #     "intent": {
    #       "name": "StateIntent",
    #       "slots": {
    #         "doornum": {
    #           "name": "doornum",
    #           "value": "1"
    #         }
    #         "doorstate": {
    #           "name": "doorstate",
    #           "value": "closed"
    #         }
    #       }
    #     }
    
    failureMsg  = "I didn't understand that. You can check the state of your garage door by saying ask " + INVONAME + " if door one is open"
    repromptMsg = "Ask me to check the state of your garage door by saying, ask " + INVONAME + " if door one is open"
    
    try:
        doornum = intent['slots']['doornum']['value']
        
        if (doornum == "door") or \
           (doornum == "door 1") or \
           (doornum == "1"):
           
            device = 0
            
        elif (doornum == "door 2") or \
             (doornum == "door to") or \
             (doornum == "2") or \
             (doornum == "to"):
             
            device = 1
            
        else:
            speechOutput = failureMsg
            cardTitle = "Try again"
            repromptText = repromptMsg
            shouldEndSession = False
            return(buildSpeechletResponse(cardTitle, speechOutput, repromptText, shouldEndSession))    
            
        doorstate = status(device)    

        if (intent['slots']['doorstate']['value'] == "open") or \
           (intent['slots']['doorstate']['value'] == "up"):
           
            if doorstate == "open":
                speechOutput = "Yes, garage " + doornum + " is open"
                cardTitle = speechOutput
            elif doorstate == "closed":
                speechOutput = "No, garage " + doornum + " is closed"
                cardTitle = speechOutput
            else:
                speechOutput = "Garage " + doornum + " is " + doorstate
                cardTitle = speechOutput

        elif (intent['slots']['doorstate']['value'] == "close") or \
             (intent['slots']['doorstate']['value'] == "closed") or \
             (intent['slots']['doorstate']['value'] == "shut") or \
             (intent['slots']['doorstate']['value'] == "down"):
             
            if doorstate == "closed":
                speechOutput = "Yes, garage " + doornum + " is closed"
                cardTitle = speechOutput
            elif doorstate == "open":
                speechOutput = "No, garage " + doornum + " is open"
                cardTitle = speechOutput
            else:
                speechOutput = "Garage " + doornum + " is " + doorstate
                cardTitle = speechOutput

        else:
            speechOutput = failureMsg
            cardTitle = "Try again"

        repromptText = repromptMsg
        shouldEndSession = True

        return(buildSpeechletResponse(cardTitle, speechOutput, repromptText, shouldEndSession))
        
    except:
        speechOutput = failureMsg
        cardTitle = "Try again"
        repromptText = repromptMsg
        shouldEndSession = False
        return(buildSpeechletResponse(cardTitle, speechOutput, repromptText, shouldEndSession))


# --------------- Helpers that build all of the responses -----------------------
def buildSpeechletResponse(title, output, repromptText, shouldEndSession):
    return ({
        "outputSpeech": {
            "type": "PlainText",
            "text": output
        },
        "card": {
            "type": "Simple",
            "title": "MyQ - " + title,
            "content": "MyQ - " + output
        },
        "reprompt": {
            "outputSpeech": {
                "type": "PlainText",
                "text": repromptText
            }
        },
        "shouldEndSession": shouldEndSession
    })

def buildResponse(sessionAttributes, speechletResponse):
    return ({
        "version": "1.0",
        "sessionAttributes": sessionAttributes,
        "response": speechletResponse
    })
