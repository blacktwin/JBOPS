import argparse
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from plexapi.server import CONFIG
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import RequestException

# Using CONFIG file
PLEX_URL = ''
PLEX_TOKEN = ''
TAUTULLI_URL = ''
TAUTULLI_APIKEY = ''

if not PLEX_URL:
    PLEX_URL = CONFIG.data['auth'].get('server_baseurl')
if not PLEX_TOKEN:
    PLEX_TOKEN = CONFIG.data['auth'].get('server_token')
if not TAUTULLI_URL:
    TAUTULLI_URL = CONFIG.data['auth'].get('tautulli_baseurl')
if not TAUTULLI_APIKEY:
    TAUTULLI_APIKEY = CONFIG.data['auth'].get('tautulli_apikey')

VERIFY_SSL = False


class Connection:
    def __init__(self, url=None, apikey=None, verify_ssl=False):
        self.url = url
        self.apikey = apikey
        self.session = Session()
        self.adapters = HTTPAdapter(max_retries=3,
                                    pool_connections=1,
                                    pool_maxsize=1,
                                    pool_block=True)
        self.session.mount('http://', self.adapters)
        self.session.mount('https://', self.adapters)
        
        # Ignore verifying the SSL certificate
        if verify_ssl is False:
            self.session.verify = False
            # Disable the warning that the request is insecure, we know that...
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Tautulli:
    def __init__(self, connection):
        self.connection = connection
    
    def _call_api(self, cmd, payload, method='GET'):
        payload['cmd'] = cmd
        payload['apikey'] = self.connection.apikey
        
        try:
            response = self.connection.session.request(method, self.connection.url + '/api/v2', params=payload)
        except RequestException as e:
            print("Tautulli request failed for cmd '{}'. Invalid Tautulli URL? Error: {}".format(cmd, e))
            return
        
        try:
            response_json = response.json()
        except ValueError:
            print("Failed to parse json response for Tautulli API cmd '{}'".format(cmd))
            return
        
        if response_json['response']['result'] == 'success':
            return response_json['response']['data']
        else:
            error_msg = response_json['response']['message']
            print("Tautulli API cmd '{}' failed: {}".format(cmd, error_msg))
            return
    
    def get_watched_history(self, user=None, section_id=None, rating_key=None, start=None, length=None):
        """Call Tautulli's get_history api endpoint"""
        payload = {"order_column": "full_title",
                   "order_dir": "asc"}
        if user:
            payload["user"] = user
        if section_id:
            payload["section_id"] = section_id
        if rating_key:
            payload["rating_key"] = rating_key
        if start:
            payload["start"] = start
        if length:
            payload["lengh"] = length
        
        history = self._call_api('get_history', payload)
        
        return [d for d in history['data'] if d['watched_status'] == 1]


class Plex:
    def __init__(self, token, url=None):
        if token and not url:
            self.account = MyPlexAccount(token)
        if token and url:
            session = Connection().session
            self.server = PlexServer(baseurl=url, token=token, session=session)
    
    def all_users(self):
        """All users
        Returns
        -------
        data: dict
        """
        users = {self.account.title: self.account}
        for user in self.account.users():
            users[user.title] = user
        
        return users
    
    def all_sections(self):
        """All sections from server
        Returns
        -------
        sections: dict
            {section title: section object}
        """
        sections = {section.title: section for section in self.server.library.sections()}
        
        return sections

    def all_sections_totals(self, library=None):
        """All sections total items
        Returns
        -------
        section_totals: dict or int
            {section title: section object} or int
        """
        section_totals = {}
        if library:
            sections = [self.all_sections()[library]]
        else:
            sections = self.all_sections()
        for section in sections:
            if section.type == 'movie':
                section_total = len(section.all())
            elif section.type == 'show':
                section_total = len(section.search(libtype='episode'))
            else:
                continue
                
            if library:
                return section_total
            
            section_totals[section.title] = section_total

        return section_totals


if __name__ == '__main__':
    admin_account = Plex(PLEX_TOKEN)
    plex_server = Plex(PLEX_TOKEN, PLEX_URL)
    parser = argparse.ArgumentParser(description="Sync watch status from one user to others.",
                                     formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--libraries', nargs='*', metavar='library', choices=plex_server.all_sections().keys(),
                        help='Libraries to scan for watched content.\n'
                             'Choices: %(choices)s')
    parser.add_argument('--users', nargs='*', metavar='users', choices=admin_account.all_users().keys(),
                        help='Users to scan for watched content.\n'
                             'Choices: %(choices)s')
    
    opts = parser.parse_args()
    

    for library in opts.libraries:
        section_total = plex_server.all_sections_totals(library)
        print("Section: {}, has {} items.".format(library, section_total))
        for user in opts.users:
            user_account = admin_account.account.user(user)
            token = user_account.get_token(plex_server.server.machineIdentifier)
            user_server = Plex(url=PLEX_URL, token=token)
            section = user_server.server.library.section(library)
            section_watched_lst = []
            if section.type == 'movie':
                section_watched_lst += section.search(unwatched=False)
            elif section.type == 'show':
                section_watched_lst += section.search(libtype='episode', unwatched=False)
            else:
                continue
            section_watched_total = len(section_watched_lst)
            percent_watched = 100 * (float(section_watched_total) / float(section_total))
            print("    {} has watched {} items ({}%).".format(user, section_watched_total, int(percent_watched)))