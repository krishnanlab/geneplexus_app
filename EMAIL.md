# Sending Email from the application

Azure documentation recommends using a 3rd party service to send email from applications, although for those with an Enterprise account we _can_ send email but this is easier to implement.  

Azure specifically recommends https://sendgrid.com and that's what's implemented.   To use email with this application : 


1. Create a sendgrid account using any email address.    
   I don't know if you should or should not use your MSU email address for this.  The terms of use are between you (the app owner) and sendgrid, not with MSU. 
   Save the account and password somewhere, but they are not needed for the actualy app to work, you need only the 'sender identity' and the api key. 
2. Create a  "sender identity"
   The account email you use to sign up for sendgrid does not have to be the email account use to send the emails.  You create multiple 'sender identities' 
   but for us we may only need one.  However you have to set one up.  
    2a.  If using a domain, create a new email address for this. This could an MSU shared mailbox address (geneplexus@msu.edu ) or a new address 
         using the hosting company of the domain.  e.g. app@geneplexus.net  , or the gmail domain.  You must have a working email box you can access
    2b.  set the sender identity to this new email address.   

The following are based on the instructions for setting up Python to use the sendgrid api  https://app.sendgrid.com/guide/integrate/langs/python

3. get an API key 
   https://app.sendgrid.com/guide/integrate/langs/python#settings/api_keys
4. configure the app
   - add the key to .env AND/OR make sure there is a app service config setting 
    `SENDGRID_API_KEY='YOUR_API_KEY'` 
    - add the sender identity email 
    `NOTIFIER_EMAIL_ADDRESS='sender identity email address from above'`
     I used app@geneplexus.net for example  
    - test email
      During development we used a test email account to send emails to.  I used a personal account for that

     `TEST_EMAIL_RECIPIENT='your email address'`

5. Configure Azure
if you have an existing Azure setup, you can add these to azure using the CLI

az webapp config appsettings set --resource-group $AZRG --name $AZAPPNAME --settings SENDGRID_API_KEY='your key' TEST_EMAIL_RECIPIENT='your email here' NOTIFIER_EMAIL_ADDRESS='the sendgrid sender identity email here'

