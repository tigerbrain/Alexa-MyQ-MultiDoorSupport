# Recent Updates
* 09-FEB-2017: Updated to support a simpler command set for units connected to a single garage.  Thereby,
               eliminating the need to mention the exact door number if it doesn't apply.
* 05-FEB-2017: Updated lambda-upload.zip file to fix a bug that caused the code to stop working on 04-FEB-2017
               due to a change in endpoint targets.
* 03-FEB-2017: Forked jbnunn's repository to release an enhanced and fully working version of a modified code
               that supports activating a second garage door under a single MyQ gateway along with some feature
               enhancements that help simplify installation and introduce an ability to configure Alexa to only
               close garages if so desired for security reasons.
               
--------------------------------------

# Enable Alexa to Control Your MyQ Garage Opener
Use Alexa to activate your Chamberlain/LiftMaster MyQ garage gateway that is connected to one or two doors.

## Summary
By using the Alexa Skills Kit and AWS Lambda, you can control your Chamberlain or LiftMaster MyQ garage
door through your Amazon Echo device.  This code adapts [David Pfeffer's](https://github.com/pfeffed) unofficial
[Chamberlain Liftmaster API](http://docs.unofficialliftmastermyq.apiary.io/) to a Python-based app you can 
use inside of AWS Lambda.

## Instructions
1.  Create a free Amazon developer account via url "developer.amazon.com"
2.  On the Amazon developer main page, click on the "Alexa" tab and select "Alexa Skills Kit"
3.  Add a new skill using the following settings:

        NOTE:  Settings not mentioned below can be left as is
        
        ----------------------------------------------------------------------------
        Skill Information
        ----------------------------------------------------------------------------
        Skill Type       :  Custom Interaction Model
        Name             :  <Your Own Custom Skill Name>
        Invocation Name  :  <A Custom Device Name For Alexa to Recognize>  
                          
                            Example:  Garage
        
                            NOTE:  
                            In my experience, it is better to give the skill a single 
                            word invocation name because it will shorten your command
                            instruction.
                          
                            It is easier to say "Alexa, ask GARAGE door one to close"
                            than to say "Alexa, ask MY GARAGE door one to close"
                      
        ----------------------------------------------------------------------------
        Interaction Model
        ----------------------------------------------------------------------------
        Intent Schema    :  <Paste the contents of the intent_schema.txt file here>
        Custom Slot Types:  <Add TWO slot types using the info below>
                            
                            <1st Slot Type>                        
                            Enter Type   :  DOOR_NUMBERS
                            Enter Values :  <Paste the ENTIRE contents of the DOOR_NUMBERS.txt file here>

                            <2nd Slot Type>
                            Enter Type   :  DOOR_STATES
                            Enter Values :  <Paste the ENTIRE contents of the DOOR_STATES.txt file here>

        Sample Utterances:  <Paste the ENTIRE contents of the sample_utterances.txt file here>
    
        ----------------------------------------------------------------------------
        Configuration
        ----------------------------------------------------------------------------
    
        You will need an ARN to get pass this step so you will come back to this 
        step only after you have created your lambda function which will provide
        the ARN information that you need.  For now, proceed to step 4
    
4.  Click on the "Skill Information" navigation link on the left side to navigate back to
    the "Skill Information" section of the skill you are trying to create and copy the
    "Application ID" of the skill onto a notepad as you will be needing it in step 8c.
    
        Sample Application ID:  amzn1.ask.skill.2dc3256e-f143-41a6-ab8f-194c3df2d789
    
    
5.  Create a free/Basic Amazon webservice (AWS) account via url "aws.amazon.com"
6.  On the upper right corner of the AWS main page, just beside your AWS account name,
    shows a location that you need click on and select "US East (N. Virginia)"
7.  Still on the AWS main page, search for AWS Services called "lambda"
8.  Click the "Create a Lambda Function" button and follow the steps below:

    a.  On the "Select Blueprint" page, choose "Blank Function"
       
    b.  On the "Configure Triggers" page, click on the dotted square box and choose
        "Alexa Skills Kit", then click the "Next" button
        
        NOTE:  If "Alexa Skills Kit" is not available, it is because your location
               is not set correctly (Please refer back to step 5 for more info)
               
    c.  On the "Configure function" page, enter the following information:
    
        NOTE:  Settings not mentioned below can be left as is

        Name             :  <Your Custom Function Name Without Spaces>  
                            Example:  OperateGarage
                   
        Runtime          :  Python 2.7
        
        ----------------------------------------------------------------
        Lambda function code
        ----------------------------------------------------------------
        Code Entry Type  :  Upload a .ZIP file
        Function Package :  <Click the "Upload" button and select the 
                            "lambda-upload.zip" file located in the directory
                            were you extracted the files I provided
                            
        Environment Variables:
        
           Key             Value
           -------------   ---------------------------------------
           username        <Enter your MyQ account username here>
           password        <Enter your MyQ account password here>
           skill_id        <Paste the Application ID of your Alexa Skill here (The one from step 4)>
           inv_name        <Enter the exact same Invocation Name you used to create the Skill in step 3>
           no_open         <Enter a "Y", if you only want Alexa to close but never open doors for 
                            security reasons>
                    
        
        ----------------------------------------------------------------        
        Lambda function handler and role
        ----------------------------------------------------------------
        Handler          :  main.lambda_handler
        Role             :  Create new role from template(s)
        Role name        :  <Your Custom Role Name>
                            Example:  GarageOperator
        
        Policy templates :  Simple Microservice permissions  

        ----------------------------------------------------------------        
        Advanced Settings
        ----------------------------------------------------------------     
        Timeout          :  15 seconds        
        
    d.  Click the "Next" button
    e.  Click the "Create function" button
    f.  On the page that comes up immediately after clicking the "Create function"
        button, notice that you now have the ARN information provided to you located
        at the upper right section of the screen, just below your AWS account name.
        This will look something like the sample below and you will need to copy this
        information in order to proceed to the next step.
        
        Example:  arn:aws:lambda:us-east-1:563954059256:function:OperateGarage
        
9.  Return to your Amazon developer account >> Alexa >> Alexa Skills Kit project and
    edit the custom skill that you have already started creating back in step 5 and
    navigate to the "Configuration" section of the skill and enter the information
    below:
    
        NOTE:  Settings not mentioned below can be left as is
        
        ----------------------------------------------------------------------------
        Configuration
        ----------------------------------------------------------------------------
        Service Endpoint Type:  AWS Lambda ARN (Amazon Resource Name)
        
                                For Geographical Region, choose "North America" and
                                on the text box that popped up immediately underneath,
                                enter the ARN information similar to the one shown 
                                below and then click on the "Next" button.
                                
                                arn:aws:lambda:us-east-1:563954059256:function:OperateGarage
                                
        ----------------------------------------------------------------------------
        Test
        ----------------------------------------------------------------------------
        On the "Test" section, just make sure that the skill is ENABLED and that's it!
        You may proceed to the next step and try out the commands directly with Alexa
        or you may opt to do a simulation test to verify that you did everything
        correctly by scrolling down to the "Text" tab of the "Service Simulator"
        section and typing in command "if door 1 is open" in the "Enter Utterance" text
        box and clicking on the "Ask <YourFunctionName>" button.
    
10. Congratulations!  You are now ready to test your skill by giving Alexa the
    command below:
    
        Assuming that your skill invocation name is "Garage"

        ----------------------------------------------------------------------------
        If your MyQ unit is only linked to a single garage door, you would say
        ----------------------------------------------------------------------------

        "Alexa, ask GARAGE if DOOR is open"

        OR

        "Alexa, ask GARAGE DOOR to close"


        ----------------------------------------------------------------------------
        If your MyQ unit is linked to two garage doors, you would say
        ----------------------------------------------------------------------------

        "Alexa, ask GARAGE if DOOR ONE is open"

        OR

        "Alexa, ask GARAGE if DOOR TWO is closed"

        OR

        "Alexa, ask GARAGE DOOR ONE to close"

        OR

        "Alexa, ask GARAGE DOOR TWO to open"


        ----------------------------------------------------------------------------
        In addition, for units linked to two garage doors, you may also drop the 
        DOOR keyword and just say
        ----------------------------------------------------------------------------

        "Alexa, ask GARAGE ONE to close"

        OR

        "Alexa, ask GARAGE if TWO is open"

## Troubleshooting Tips
Troubleshooting Alexa to Lambda interactions can be done via AWS Lambda.  You need to navigate into the specific Lambda function that you just created, click on the "Monitoring" tab and then you will be presented a link in the upper right corner of the tab called "View logs in CloudWatch".  Clicking on the link will allow you to view the logs generated by the function you created with the most recent one presented at the top of the list.  Use the logs to gain a better understanding on why the function is not working as expected.

### Alexa Skills Kit Documentation
The documentation for the Alexa Skills Kit is available on the [Amazon Apps and Services Developer Portal](https://developer.amazon.com/appsandservices/solutions/alexa/alexa-skills-kit/).

### Resources
Here are a few direct links to Alexa and Lambda documentation:

- [Using the Alexa Skills Kit Samples (Node.js)](https://github.com/amzn/alexa-skills-kit-js)
- [Getting Started](https://developer.amazon.com/appsandservices/solutions/alexa/alexa-skills-kit/getting-started-guide)
- [Invocation Name Guidelines](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/choosing-the-invocation-name-for-an-alexa-skill)
- [Developing an Alexa Skill as an AWS Lambda Function](https://developer.amazon.com/appsandservices/solutions/alexa/alexa-skills-kit/docs/developing-an-alexa-skill-as-a-lambda-function)

### Disclaimer

The code here is based off of an unsupported API from [Chamberlain](http://www.chamberlain.com/) and is subject to change without notice. The authors claim no responsibility for damages to your garage door or property by use of the code within.
