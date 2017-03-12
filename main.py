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
LEFT	  = os.environ['left']

myq_userid                  = ""
myq_security_token          = ""
myq_device_id               = []

only_close = (NO_OPEN.upper() == "Y") or (NO_OPEN.upper() == "YES")

open_msg = " open your garage door by saying, ask " + INVONAME + " to open the left or right door."
close_msg =  " close your garage door by saying, ask " + INVONAME + " to close the left or right door."
check_msg = " check the state of your garage door by saying, ask " + INVONAME + " if the doors are open."
check1_msg = " check the state of your garage door by saying, ask " + INVONAME + " if the left or right door is open."

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

    global left_door, right_door
    if (LEFT == "") or (LEFT == "0"):
        left_door = 0
        right_door = 1
    elif (LEFT == "1"):
        left_door = 1
        right_door = 0
    else:
        print("left environment variable must be blank, 0, or, 1")
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

        if len(myq_device_id) == 1:
            global open_msg, close_msg, check_msg, check1_msg
            open_msg = open_msg.replace(" left or right", "")
            close_msg = close_msg.replace(" left or right", "")
            check_msg = check1_msg = check1_msg.replace(" left or right", "")

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
    if device_action.status_code != 200:
        print("Status code: " + str(device_action.status_code))
    
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
            # break # enable to test a single device

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
    elif intentName == "AllStatesIntent":
        if len(myq_device_id) == 1:
            return allState1Response(intent)
        else:
            return allStatesResponse(intent)
    elif intentName == "MoveIntent":
        return moveIntent(intent)
    elif intentName == "AllCloseIntent":
        if len(myq_device_id) == 1:
            return allClose1Intent(intent)
        else:
            return allCloseIntent(intent)
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

def getDevice(doornum):
    if (doornum == "door") or \
       (doornum == "the door") or \
       (doornum == "door 1") or \
       (doornum == "1"):

        return 0

    elif (doornum == "door 2") or \
         (doornum == "door to") or \
         (doornum == "2") or \
         (doornum == "to"):

        return 1

    elif ("left" in doornum):

        return left_door

    elif ("right" in doornum):

        return right_door

    else:
        return -1


def getWelcomeResponse():
    cardTitle = "Welcome"
    
    if only_close:
        speechOutput = "You can" + close_msg + " You can also" + check_msg

        # If the user either does not reply to the welcome message or says something that is not
        # understood, they will be prompted again with this text.
        repromptText = "Ask me to" + close_msg + " Or, ask me to " + check_msg
    else:
        speechOutput = "You can" + open_msg + " You can" + close_msg + " You can also" + check_msg
        repromptText = "Ask me to" + open_msg + " Ask me to" + close_msg + " You can also ask me to" + check_msg
        
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
    
    if only_close:       
        failureMsg  = "I didn't understand that. You can" + close_msg
        repromptMsg = "Ask me to" + close_msg
        
    else:
        failureMsg  = "I didn't understand that. You can" + open_msg + " Or, you can" + close_msg
        repromptMsg = "Ask me to" + open_msg + " Or, ask me to" + close_msg
    
    try:  
        doornum = intent['slots']['doornum']['value']
        device = getDevice(doornum)
            
        if device == -1:
            speechOutput = failureMsg
            cardTitle = "Try again" 
            repromptText = repromptMsg
            shouldEndSession = False
            return(buildSpeechletResponse(cardTitle, speechOutput, repromptText, shouldEndSession)) 
                
        if (intent['slots']['doorstate']['value'] == "close") or \
           (intent['slots']['doorstate']['value'] == "shut") or \
           (intent['slots']['doorstate']['value'] == "down"):
           
            close(device)
            print("Closing " + str(device) + "...")
            speechOutput = "Ok, closing " + doornum + " now"
            cardTitle = "Closing your garage door"
            
        elif (intent['slots']['doorstate']['value'] == "open") or \
             (intent['slots']['doorstate']['value'] == "up"):
             
            if only_close:               
                speechOutput = failureMsg
                cardTitle = "Try again"
                
            else:
                open(device)
                print("Opening " + str(device) + "...")
                speechOutput = "Ok, opening " + doornum + " now"
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


def allCloseIntent(intent):
    # Close all doors

    doorstate_left = status(left_door) 
    doorstate_right = status(right_door) 

    speechOutput = "Both doors are closed"
    cardTitle = speechOutput

    if doorstate_left != "closed" and doorstate_left != "closing":
        close(left_door)
        print("Closing left...")
        cardTitle = "Closing your garage door"
    if doorstate_right != "closed" and doorstate_right != "closing":
        close(right_door)
        print("Closing right...")
        cardTitle = "Closing your garage door"

    if doorstate_left != "closed" and doorstate_right != "closed":
        speechOutput = "Ok, closing both garage doors now"
    elif doorstate_left != "closed":
        speechOutput = "Ok, closing the left garage door now"
    elif doorstate_right != "closed":
        speechOutput = "Ok, closing the right garage door now"

    repromptText = "Ask me to" + close_msg + " Or, ask me to" + check_msg
    shouldEndSession = True

    return(buildSpeechletResponse(cardTitle, speechOutput, repromptText, shouldEndSession))


def allClose1Intent(intent):
    # Close all doors where there's just 1

    doorstate = status(0) 

    speechOutput = "The door is closed"
    cardTitle = speechOutput

    if doorstate != "closed" and doorstate != "closing":
        close(0)
        print("Closing...")
        cardTitle = "Closing your garage door"
        speechOutput = "Ok, closing the garage door now"

    repromptText = "Ask me to" + close_msg + " Or, ask me to" + check_msg
    shouldEndSession = True

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
    
    failureMsg  = "I didn't understand that. You can" + check1_msg
    repromptMsg = "Ask me to" + check1_msg
    
    try:
        doornum = intent['slots']['doornum']['value']
        device = getDevice(doornum)
            
        if device == -1:
            speechOutput = failureMsg
            cardTitle = "Try again"
            repromptText = repromptMsg
            shouldEndSession = False
            return(buildSpeechletResponse(cardTitle, speechOutput, repromptText, shouldEndSession))    
            
        doorstate = status(device)    

        if (intent['slots']['doorstate']['value'] == "open") or \
           (intent['slots']['doorstate']['value'] == "up"):
           
            if doorstate == "open":
                speechOutput = "Yes, " + doornum + " is open"
            elif doorstate == "closed":
                speechOutput = "No, " + doornum + " is closed"
            else:
                speechOutput = doornum + " is " + doorstate
            cardTitle = speechOutput

        elif (intent['slots']['doorstate']['value'] == "close") or \
             (intent['slots']['doorstate']['value'] == "closed") or \
             (intent['slots']['doorstate']['value'] == "shut") or \
             (intent['slots']['doorstate']['value'] == "down"):
             
            if doorstate == "closed":
                speechOutput = "Yes, " + doornum + " is closed"
            elif doorstate == "open":
                speechOutput = "No, " + doornum + " is open"
            else:
                speechOutput = doornum + " is " + doorstate
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


def allStatesResponse(intent):
    # Ask garage what's up
            
    doorstate_left = status(left_door) 
    doorstate_right = status(right_door) 

    if doorstate_left == doorstate_right:
        speechOutput = "Both doors are " + doorstate_left
    else:
        speechOutput = "The left door is " + doorstate_left + \
          ", and the right door is " + doorstate_right
    cardTitle = speechOutput

    repromptText = "Ask me to" + check_msg
    shouldEndSession = True

    return(buildSpeechletResponse(cardTitle, speechOutput, repromptText, shouldEndSession))


def allState1Response(intent):
    # Ask garage what's up when there's one door
            
    doorstate = status(0) 

    speechOutput = "The door is " + doorstate
    cardTitle = speechOutput

    repromptText = "Ask me to" + check_msg
    shouldEndSession = True

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
