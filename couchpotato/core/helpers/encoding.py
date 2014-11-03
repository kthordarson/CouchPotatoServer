<<<<<<< HEAD
# -*- coding: utf-8 -*-
from couchpotato.core.logger import CPLog
=======
>>>>>>> a12f049d14cfc34965a7a3b9523d76dc7279182d
from string import ascii_letters, digits
from urllib import quote_plus
import os
import re
import traceback
import unicodedata

from chardet import detect
from couchpotato.core.logger import CPLog
import six


log = CPLog(__name__)


def toSafeString(original):
    valid_chars = "-_.() %s%s" % (ascii_letters, digits)
    cleaned_filename = unicodedata.normalize('NFKD', toUnicode(original)).encode('ASCII', 'ignore')
    valid_string = ''.join(c for c in cleaned_filename if c in valid_chars)
    return ' '.join(valid_string.split())


def simplifyString(original):
    string = original.replace("'", " ")
    string = stripAccents(original.lower())
    string = toSafeString(' '.join(re.split('[\W\-]+', string, flags=re.U)))
    split = re.split('[\W\-]+|_', string.lower(), flags=re.U)
    return toUnicode(' '.join(split))


def toUnicode(original, *args):
    try:
        if isinstance(original, unicode):
            return original
        else:
            try:
                return six.text_type(original, *args)
            except:
                try:
                    detected = detect(original)
                    if detected.get('encoding') == 'utf-8':
                        return original.decode('utf-8')
                    return ek(original, *args)
                except:
                    log.error('encoding.py: tryunicode vesen')
                    raise
    except:
        log.error('Unable to decode value "%s..." : %s ', (repr(original)[:20], traceback.format_exc()))
        ascii_text = str(original).encode('string_escape')
        return toUnicode(ascii_text)


def ss(original, *args):

    u_original = toUnicode(original, *args)
    try:
        from couchpotato.environment import Env
        return u_original.encode(Env.get('encoding'))
    except Exception as e:
<<<<<<< HEAD
            log.debug('Failed ss encoding char, force UTF8: %s', e)
            return u_original.encode('utf8')
=======
        log.debug('Failed ss encoding char, force UTF8: %s', e)
        try:
            return u_original.encode(Env.get('encoding'), 'replace')
        except:
            return u_original.encode('utf-8', 'replace')
>>>>>>> a12f049d14cfc34965a7a3b9523d76dc7279182d


def sp(path, *args):

    # Standardise encoding, normalise case, path and strip trailing '/' or '\'
    if not path or len(path) == 0:
        return path

    # convert windows path (from remote box) to *nix path
    if os.path.sep == '/' and '\\' in path:
        path = '/' + path.replace(':', '').replace('\\', '/')

    path = os.path.normpath(ss(path, *args))

    # Remove any trailing path separators
    if path != os.path.sep:
        path = path.rstrip(os.path.sep)

    # Add a trailing separator in case it is a root folder on windows (crashes guessit)
    if len(path) == 2 and path[1] == ':':
        path = path + os.path.sep

    # Replace *NIX ambiguous '//' at the beginning of a path with '/' (crashes guessit)
    path = re.sub('^//', '/', path)

    return path


def ek(original, *args):
    if isinstance(original, (str, unicode)):
        try:
            from couchpotato.environment import Env
            return original.decode(Env.get('encoding'))
        except UnicodeDecodeError:
            return unicode(original,'utf8')
        except:
            log.error('encoding.py: ek vesen')
            return original
#            raise
    return original


def isInt(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


def stripAccents(s):
    return ''.join((c for c in unicodedata.normalize('NFD', toUnicode(s)) if unicodedata.category(c) != 'Mn'))


def tryUrlencode(s):
    new = six.u('')
    if isinstance(s, dict):
        for key, value in s.items():
            new += six.u('&%s=%s') % (key, tryUrlencode(value))

        return new[1:]
    else:
        for letter in ss(s):
            try:
                new += quote_plus(letter)
            except:
                new += letter

    return new
