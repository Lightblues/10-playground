from sys import exit as sys_exit
from sys import argv as sys_argv
from json import loads as json_loads

from requests import session
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


class Checkin:
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:76.0) Gecko/20100101 Firefox/76.0"
    
    def __init__(self) -> None:
        self.session = session()
        self.session.headers['User-Agent'] = self.UA
        
    def checkinSuwa(self, authorizationmweb):
        headers = {
            # "Host": "cloud.faster.buzz",
            # "Origin": "https://cloud.faster.buzz/m/home",
            'authorizationmweb': authorizationmweb,
        }
        logging.debug("Checking in Suwa")
        r = self.session.put(
            "https://cloud.faster.buzz/api_mweb/user/checkin",
            headers = headers, allow_redirects=False
        )
        j = json_loads(r.text)
        logging.debug(j['message'])
    def getSuwaInfo(self, authorizationmweb):
        # https://cloud.faster.buzz/api_mweb/user/info
        pass

if __name__ == '__main__':
    authorizationmweb = sys_argv[1].strip()
    # authorizationmweb = 
    
    checkin = Checkin()
    checkin.checkinSuwa(authorizationmweb)
    
