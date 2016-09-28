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

# Edit user@email.com and shows
users = [{'email': 'user1@gmail.com',
          'shows': ('show1', 'show2')
          },
         {'email': 'user2@gmail.com',
          'shows': ('show1', 'show2', 'show3')
          },
         {'email': 'user3@gmail.com',
          'shows': ('show1', 'show2', 'show3', 'show4')
          }]
          
to = ','.join([u['email'] for u in users if show_name in u['shows']])

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
if show_name.lower() == show_notify.lower() or show_type.lower() == 'show' or show_type.lower() == 'episode': # if tv show
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
