from email.mime.text import MIMEText
import email.utils
import smtplib
import sys

# Arguments passed from PlexPy
# {show_name} {episode_name} {season_num00} {episode_num00} {server_name} {media_type} {poster_url} {title} {summary} {library_name}
show_name = sys.argv[1]
# You can add more arguments if you want more details in the email body
episode_name = sys.argv[2]
season_num = sys.argv[3]
episode_num = sys.argv[4]
plex_server = sys.argv[5]
show_type = sys.argv[6]
poster = sys.argv[7]
title = sys.argv[8]
summary = sys.argv[9]
library_name = sys.argv[10]

show_notify = ''
to = ''

# setting user's shows they want notifications for		
list_user1 = ["show1", "show2"]
list_user2 = ["show1", "show3"] 
list_user3 = ["show1", "show4"] 
list_user4 = ["show1", "show2", "show3", "show4"] 

# Email list
user_1 = ["user1@gmail.com", list_user1]
user_2 = ["user2@gmail.com", list_user2]
user_3 = ["user3@gmail.com", list_user3]
user_4 = ["user4@gmail.com", list_user4]

# If show matches user's list then the user's email is added
for n in user_1[1]:
	if n == show_name:
	 show_notify = n
	 to += user_1[0] + ", "
	 
for n in user_2[1]:
	if n == show_name:
	 show_notify = n
	 to += user_2[0] + ", "
	 
for n in user_3[1]:
	if n == show_name:
	 show_notify = n
	 to += user_3[0] + ", "
	 
for n in user_4[1]:
	if n == show_name:
	 show_notify = n
	 to += user_4[0] + ", "

# Email settings
name = 'PlexPy' # Your name
sender = 'sender' # From email address
email_server = 'smtp.gmail.com' # Email server (Gmail: smtp.gmail.com)
email_port = 587  # Email port (Gmail: 587)
email_username = 'email' # Your email username
email_password = 'password' # Your email password
email_subject = 'New episode for ' + show_name + ' is available on ' +  plex_server # The email subject

 # More detailed email body
show_html = """\
<html>
  <head></head>
  <body>
    <p>Hi!<br>
        %s  S%s - E%s -- %s -- was recently added to %s on PLEX
        <br><br>
        <br> %s <br>
       <br><img src="%s" alt="Poster unavailable" height="150" width="102"><br>
    </p>
  </body>
</html>
""" %(show_name, season_num, episode_num, episode_name, library_name, summary, poster) #these are the passed parameters for tvshows
### Do not edit below ###
# Check to se whether it is a tv show or a movie
if show_name.lower() == show_notify.lower() or show_type.lower() == 'show': # if tv show
    message = MIMEText(show_html, 'html')
    message['Subject'] = email_subject
    message['From'] = email.utils.formataddr((name, sender))
    message['To'] = to
    
    mailserver = smtplib.SMTP(email_server, email_port)
    mailserver.starttls()
    mailserver.ehlo()
    mailserver.login(email_username, email_password)
    mailserver.sendmail(sender, to, message.as_string())
    mailserver.quit()
else:
	exit