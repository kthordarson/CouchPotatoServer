# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from couchpotato.core.helpers.encoding import simplifyString, tryUrlencode
from couchpotato.core.helpers.variable import tryInt
from couchpotato.core.logger import CPLog
from couchpotato.core.providers.torrent.base import TorrentProvider
import traceback

log = CPLog(__name__)


class Deildu(TorrentProvider):

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
