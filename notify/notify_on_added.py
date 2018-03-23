"""
Tautulli > Settings > Notification Agents > Scripts > Bell icon:
        [X] Notify on Recently Added
Tautulli > Settings > Notification Agents > Scripts > Gear icon:
        Recently Added: notify_on_added.py
        
Tautulli > Settings > Notifications > Script > Script Arguments: 
-sn {show_name} -ena {episode_name} -ssn {season_num00} -enu {episode_num00} -srv {server_name} -med {media_type} -pos {poster_url} -tt {title} -sum {summary} -lbn {library_name}

You can add more arguments if you want more details in the email body
"""

from email.mime.text import MIMEText
import email.utils
import smtplib
import sys
import argparse


parser = argparse.ArgumentParser()
parser.add_argument('-sn', '--show_name', action='store', default='',
                    help='The name of the TV show')
parser.add_argument('-ena', '--episode_name', action='store', default='',
                    help='The name of the episode')
parser.add_argument('-ssn', '--season_num', action='store', default='',
                    help='The season number of the TV show')
parser.add_argument('-enu', '--episode_num', action='store', default='',
                    help='The episode number of the TV show')
parser.add_argument('-srv', '--plex_server', action='store', default='',
                    help='The name of the Plex server')
parser.add_argument('-med', '--show_type', action='store', default='',
                    help='The type of media')
parser.add_argument('-pos', '--poster', action='store', default='',
                    help='The poster url')
parser.add_argument('-tt', '--title', action='store', default='',
                    help='The title of the TV show')
parser.add_argument('-sum', '--summary', action='store', default='',
                    help='The summary of the TV show')
parser.add_argument('-lbn', '--library_name', action='store', default='',
                    help='The name of the TV show')
p = parser.parse_args()

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
          
# Kill script now if show_name is not in lists
too = list('Match' for u in users if p.show_name in u['shows'])
if not too:
	print 'Kill script now show_name is not in lists'
	exit()

# Join email addresses
to = list([u['email'] for u in users if p.show_name in u['shows']])

# Email settings
name = 'Tautulli' # Your name
sender = 'sender' # From email address
email_server = 'smtp.gmail.com' # Email server (Gmail: smtp.gmail.com)
email_port = 587  # Email port (Gmail: 587)
email_username = 'email' # Your email username
email_password = 'password' # Your email password
email_subject = 'New episode for ' + p.show_name + ' is available on ' +  p.plex_server # The email subject

# Detailed body for tv shows
show_html = """\
<html>
  <head></head>
  <body>
    <p>Hi!<br>
        {p.show_name}  S{p.season_num} - E{p.episode_num} -- {p.episode_name} -- was recently added to {p.library_name} on PLEX
        <br><br>
        <br> {p.summary} <br>
       <br><img src="{p.poster}" alt="Poster unavailable" height="150" width="102"><br>
    </p>
  </body>
</html>
""".format(p=p)

### Do not edit below ###
# Check to see whether it is a tv show
if p.show_type.lower() == 'show' or p.show_type.lower() == 'episode':
    message = MIMEText(show_html, 'html')
    message['Subject'] = email_subject
    message['From'] = email.utils.formataddr((name, sender))
    
    
    mailserver = smtplib.SMTP(email_server, email_port)
    mailserver.starttls()
    mailserver.ehlo()
    mailserver.login(email_username, email_password)
    mailserver.sendmail(sender, to, message.as_string())
    mailserver.quit()
else:
	exit()
