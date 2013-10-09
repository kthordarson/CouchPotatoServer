# coding=utf-8
from couchpotato import get_session
from couchpotato.api import addApiView
from couchpotato.core.event import addEvent
from couchpotato.core.helpers.encoding import toUnicode, ss
from couchpotato.core.helpers.variable import mergeDicts, md5, getExt
from couchpotato.core.logger import CPLog
from couchpotato.core.plugins.base import Plugin
from couchpotato.core.settings.model import Quality, Profile, ProfileType
from sqlalchemy.sql.expression import or_
import re
import time

log = CPLog(__name__)


class QualityPlugin(Plugin):

    qualities = [
        {'identifier': 'bd50', 'hd': True, 'size': (15000, 60000), 'label': 'BR-Disk', 'alternative': ['bd25'], 'allow': ['1080p'], 'ext':[], 'tags': ['bdmv', 'certificate', ('complete', 'bluray')]},
        {'identifier': '1080p', 'hd': True, 'size': (4000, 20000), 'label': '1080p', 'width': 1920, 'height': 1080, 'alternative': [], 'allow': [], 'ext':['mkv', 'm2ts'], 'tags': ['m2ts']},
        {'identifier': '720p', 'hd': True, 'size': (3000, 10000), 'label': '720p', 'width': 1280, 'height': 720, 'alternative': [], 'allow': [], 'ext':['mkv', 'ts']},
        {'identifier': 'deildu', 'hd': True, 'size': (600, 6000), 'label': 'deildu', 'alternative': ['txt', 'texti', 'texta', 'isl', '0xEDsl', '0xEDslenskum', 'islenskum', 'islenskur', '0xEDslenskur'], 'allow': [], 'ext':['mkv', 'avi'], 'tags': ['texti', 'texta', 'Texta', 'isl', '0xEDsl', '0xCDsl', '0xEDslenskum', '0xCDslenskum', 'Texti', 'eskil']},
        {'identifier': 'brrip', 'hd': True, 'size': (700, 7000), 'label': 'BR-Rip', 'alternative': ['bdrip'], 'allow': ['720p', '1080p'], 'ext':['avi'], 'tags': ['hdtv', 'hdrip', 'webdl', ('web', 'dl')]},
        {'identifier': 'dvdr', 'size': (3000, 10000), 'label': 'DVD-R', 'alternative': [], 'allow': [], 'ext':['iso', 'img'], 'tags': ['pal', 'ntsc', 'video_ts', 'audio_ts']},
        {'identifier': 'dvdrip', 'size': (600, 2400), 'label': 'DVD-Rip', 'width': 720, 'alternative': [], 'allow': [], 'ext':['avi', 'mpg', 'mpeg'], 'tags': [('dvd', 'rip'), ('dvd', 'xvid'), ('dvd', 'divx')]},
        {'identifier': 'scr', 'size': (600, 1600), 'label': 'Screener', 'alternative': ['screener', 'dvdscr', 'ppvrip', 'dvdscreener', 'hdscr'], 'allow': ['dvdr', 'dvd'], 'ext':['avi', 'mpg', 'mpeg'], 'tags': ['webrip', ('web', 'rip')]},
        {'identifier': 'r5', 'size': (600, 1000), 'label': 'R5', 'alternative': ['r6'], 'allow': ['dvdr'], 'ext':['avi', 'mpg', 'mpeg']},
        {'identifier': 'tc', 'size': (600, 1000), 'label': 'TeleCine', 'alternative': ['telecine'], 'allow': [], 'ext':['avi', 'mpg', 'mpeg']},
        {'identifier': 'ts', 'size': (600, 1000), 'label': 'TeleSync', 'alternative': ['telesync', 'hdts'], 'allow': [], 'ext':['avi', 'mpg', 'mpeg']},
        {'identifier': 'cam', 'size': (600, 1000), 'label': 'Cam', 'alternative': ['camrip', 'hdcam'], 'allow': [], 'ext':['avi', 'mpg', 'mpeg']}
    ]
    pre_releases = ['cam', 'ts', 'tc', 'r5', 'scr']

    def __init__(self):
        addEvent('quality.all', self.all)
        addEvent('quality.single', self.single)
        addEvent('quality.guess', self.guess)
        addEvent('quality.pre_releases', self.preReleases)

        addApiView('quality.size.save', self.saveSize)
        addApiView('quality.list', self.allView, docs = {
            'desc': 'List all available qualities',
            'return': {'type': 'object', 'example': """{
            'success': True,
            'list': array, qualities
}"""}
        })

        addEvent('app.initialize', self.fill, priority = 10)

    def preReleases(self):
        return self.pre_releases

    def allView(self, **kwargs):

        return {
            'success': True,
            'list': self.all()
        }

    def all(self):

        db = get_session()

        qualities = db.query(Quality).all()

        temp = []
        for quality in qualities:
            q = mergeDicts(self.getQuality(quality.identifier), quality.to_dict())
            temp.append(q)

        return temp

    def single(self, identifier = ''):

        db = get_session()
        quality_dict = {}

        quality = db.query(Quality).filter(or_(Quality.identifier == identifier, Quality.id == identifier)).first()
        if quality:
            quality_dict = dict(self.getQuality(quality.identifier), **quality.to_dict())

        return quality_dict

    def getQuality(self, identifier):

        for q in self.qualities:
            if identifier == q.get('identifier'):
                return q

    def saveSize(self, **kwargs):

        db = get_session()
        quality = db.query(Quality).filter_by(identifier = kwargs.get('identifier')).first()

        if quality:
            setattr(quality, kwargs.get('value_type'), kwargs.get('value'))
            db.commit()

        return {
            'success': True
        }

    def fill(self):

        db = get_session()

        order = 0
        for q in self.qualities:

            # Create quality
            qual = db.query(Quality).filter_by(identifier = q.get('identifier')).first()

            if not qual:
                log.info('Creating quality: %s', q.get('label'))
                qual = Quality()
                qual.order = order
                qual.identifier = q.get('identifier')
                qual.label = toUnicode(q.get('label'))
                qual.size_min, qual.size_max = q.get('size')

                db.add(qual)

            # Create single quality profile
            prof = db.query(Profile).filter(
                    Profile.core == True
                ).filter(
                    Profile.types.any(quality = qual)
                ).all()

            if not prof:
                log.info('Creating profile: %s', q.get('label'))
                prof = Profile(
                    core = True,
                    label = toUnicode(qual.label),
                    order = order
                )
                db.add(prof)

                profile_type = ProfileType(
                    quality = qual,
                    profile = prof,
                    finish = True,
                    order = 0
                )
                prof.types.append(profile_type)

            order += 1

        db.commit()

        time.sleep(0.3) # Wait a moment

        return True

    def guess(self, files, extra = None):
        if not extra: extra = {}

        # Create hash for cache
        cache_key = md5(str([f.replace('.' + getExt(f), '') for f in files]))
        cached = self.getCache(cache_key)
        if cached and len(extra) == 0: return cached

        qualities = self.all()
        for cur_file in files:
            words = re.split('[\W\s\-]+', cur_file.lower())

            found = {}
            for quality in qualities:
                contains = self.containsTag(quality, words, cur_file)
                if contains:
                    found[quality['identifier']] = True

            for quality in qualities:

                # Check identifier
                if quality['identifier'] in words:
                    if len(found) == 0 or len(found) == 1 and found.get(quality['identifier']):
                        log.debug('Found via identifier "%s" in %s', (quality['identifier'], cur_file))
                        return self.setCache(cache_key, quality)

                # Check alt and tags
                contains = self.containsTag(quality, words, cur_file)
                if contains:
                    return self.setCache(cache_key, quality)

        # Try again with loose testing
        quality = self.guessLoose(cache_key, files = files, extra = extra)
        if quality:
            return self.setCache(cache_key, quality)

        log.debug('Could not identify quality for: %s', files)
        return None

    def containsTag(self, quality, words, cur_file = ''):
        cur_file = ss(cur_file)

        # Check alt and tags
        for tag_type in ['alternative', 'tags', 'label']:
            qualities = quality.get(tag_type, [])
            qualities = [qualities] if isinstance(qualities, (str, unicode)) else qualities

            for alt in qualities:
                if (isinstance(alt, tuple) and '.'.join(alt) in '.'.join(words)) or (isinstance(alt, (str, unicode)) and ss(alt.lower()) in cur_file.lower()):
                    log.debug('Found %s via %s %s in %s', (quality['identifier'], tag_type, quality.get(tag_type), cur_file))
                    return True

            if list(set(qualities) & set(words)):
                log.debug('Found %s via %s %s in %s', (quality['identifier'], tag_type, quality.get(tag_type), cur_file))
                return True

        return

    def guessLoose(self, cache_key, files = None, extra = None):

        if extra:
            for quality in self.all():

                # Check width resolution, range 20
                if quality.get('width') and (quality.get('width') - 20) <= extra.get('resolution_width', 0) <= (quality.get('width') + 20):
                    log.debug('Found %s via resolution_width: %s == %s', (quality['identifier'], quality.get('width'), extra.get('resolution_width', 0)))
                    return self.setCache(cache_key, quality)

                # Check height resolution, range 20
                if quality.get('height') and (quality.get('height') - 20) <= extra.get('resolution_height', 0) <= (quality.get('height') + 20):
                    log.debug('Found %s via resolution_height: %s == %s', (quality['identifier'], quality.get('height'), extra.get('resolution_height', 0)))
                    return self.setCache(cache_key, quality)

            if 480 <= extra.get('resolution_width', 0) <= 720:
                log.debug('Found as dvdrip')
                return self.setCache(cache_key, self.single('dvdrip'))

        return None
