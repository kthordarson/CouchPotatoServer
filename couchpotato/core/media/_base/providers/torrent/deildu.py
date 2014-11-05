# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from couchpotato.core.helpers.encoding import simplifyString, tryUrlencode
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.logger import CPLog
#from couchpotato.core.providers.torrent.base import TorrentProvider

#import traceback
import re
import json
import traceback

from couchpotato.core.helpers.variable import tryInt, getIdentifier
from couchpotato.core.logger import CPLog
from couchpotato.core.media._base.providers.torrent.base import TorrentProvider


log = CPLog(__name__)


class Base(TorrentProvider):

    urls = {
        'test': 'http://icetracker.org/',
        'login': 'http://icetracker.org/takelogin.php',
        'detail': 'http://icetracker.org/details.php?id=%s',
        'search': 'http://icetracker.org/browse.php?sort=seeders&type=desc&cat=0',
        'base': 'http://icetracker.org/',
    }

    http_time_between_calls = 5  # seconds
    last_login_check = None

    def _searchOnTitle(self, title, movie, quality, results):

        #q = '%s %s' % (simplifyString(title), movie['library']['year'])
        q = '%s' % (simplifyString(title))

        arguments = tryUrlencode({
            'search': q,
        })
        url = "%s&%s" % (self.urls['search'], arguments)
        data = self.getHTMLData(url)
        if data:
            html = BeautifulSoup(data)
#            print(html)
#            log.info("Deildu.net got some data")
#            log.info("Deildu.net datadump %s", data)
#            log.info("Deildu.net htmldump %s", html)
#            log.info("Deildu.net got some data2")
            try:
                resultsTable = html.find('table', {'class': 'torrentlist'})
                log.info("Deildu.net looking for resultsTable")
                if resultsTable:
                    entries = resultsTable.find_all('tr')
                    for result in entries[1:]:

                        all_cells = result.find_all('td')
                        log.info("Deildu.net got some restults table: ")

                        detail_link = all_cells[1].find('a')
                        details = detail_link['href']
                        torrent_id = details.replace('details.php?id=', '')
                        torrent_id = details.replace('&hit=1', '')

                        results.append({
                            'id': torrent_id,
                            'name': detail_link.get_text().strip(),
                            'size': self.parseSize(all_cells[6].get_text()),
                            'seeders': tryInt(all_cells[8].get_text()),
                            'leechers': tryInt(all_cells[9].get_text()),
                            'url': self.urls['base'] + all_cells[2].find('a')['href'],
                            'download': self.loginDownload,
                            'description': self.urls['base'] + all_cells[1].find('a')['href'],
                        })
                else:
                    log.info("Deildu.net got no resultsTable")

            except:
                log.error('Failed getting results from %s: %s', (self.getName(), traceback.format_exc()))
        else:
            log.info("Deildu.net got no data!")

    def getLoginParams(self):
        return {
            'username': self.conf('username'),
            'password': self.conf('password'),
        }

    def loginSuccess(self, output):
        return 'Login failed!' not in output
    loginCheckSuccess = loginSuccess

config = [{
    'name': 'deildu',
    'groups': [
        {
            'tab': 'searcher',
#            'subtab': 'providers',
            'list': 'torrent_providers',
            'name': 'deildu',
            'description': 'See <a href="http://icetracker.org">Deildu.net</a>',
            'icon': 'iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAIAAACQkWg2AAABi0lEQVR4AZWSzUsbQRjGdyabTcvSNPTSHlpQQeMHJApC8CJRvHgQQU969+LJP8G7f4N3DwpeFRQvRr0EKaUl0ATSpkigUNFsMl/r9NmZLCEHA/nNO5PfvMPDm0DI6fV3ZxiolEICe1oZCBVCCmBPKwOh2ErKBHGE4KYEXBpSLkUlqO4LcM7f+6nVhRnOhSkOz/hexk+tL+YL0yPF2YmN4tynD++4gTLGkNNac9YFLoREBR1+cnF3dFY6v/m6PD+FaXiNJtgA4xYbABxiGrz6+6HWaI5/+Qh37YS0/3Znc8UxwNGBIIBX22z+/ZdJ+4wzyjpR4PEpODg8tgUXBv2iWUzSpa12B0IR6n6lvt8Aek2lZHb084+fdRNgrwY8z81PjhVy2d2ttUrtV/lbBa+JXGEpDMPnoF2tN1QYRqVUtf6nFbThb7wk7le395elcqhASLb39okDiHY00VCtCTEHwSiH4AI0lkOiT1dwMeSfT3SRxiQWNO7Zwj1egkoVIQFMKvSiC3bcjXq9Jf8DcDIRT3hh10kAAAAASUVORK5CYII=',
            'wizard': True,
            'options': [
                {
                    'name': 'enabled',
                    'type': 'enabler',
                    'default': False
                },
                {
                    'name': 'username',
                    'default': '',
                },
                {
                    'name': 'password',
                    'default': '',
                    'type': 'password',
                }
            ],
        }
    ]
}]
