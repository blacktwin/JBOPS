'''
https://gist.github.com/blacktwin/4ccb79c7d01a95176b8e88bf4890cd2b
'''

from plexapi.server import PlexServer
import ConfigParser
import io
import os.path
import random
import re

## EDIT THESE SETTINGS IF NOT USING THE CONFIG ##
baseurl = 'http://localhost:32400'
token = 'xxxxxx'

## DO NOT EDIT
config_exists = os.path.exists("../config.ini")
if config_exists:
    # Load the configuration file
    with open("../config.ini") as f:
        real_config = f.read()
        config = ConfigParser.RawConfigParser(allow_no_value=False)
        config.readfp(io.BytesIO(real_config))

        token=config.get('plex-data', 'PLEX_TOKEN')
        baseurl=config.get('plex-data', 'PLEX_URL')
##/DO NOT EDIT

##/EDIT THESE SETTINGS

plex = PlexServer(baseurl, token)


sections_lst = []
LIBRARIES_LST = ['Movies', 'TV Shows'] # Whatever you name your libraries


for x in LIBRARIES_LST:
    sections = plex.library.section(x).all()
    sections_lst += [section.title for section in sections]

word_site = [line.split() for line in sections_lst]
WORDS = [item for sublist in word_site for item in sublist]
count = len(WORDS)
r = range(0,count)


def ran_words(cnt,):
    word_site = [line.split() for line in sections_lst]
    WORDS = [item for sublist in word_site for item in sublist]

    ran_word = random.choice(WORDS)
    ran_word = ''.join(e for e in ran_word if e.isalnum())
    sy_cnt = sylco(ran_word)
    word_cnt = {ran_word: sy_cnt}
    return word_cnt


def sylco(word):
    # pulled from https://github.com/eaydin/sylco/blob/master/sylco.py
    word = word.lower()

    # exception_add are words that need extra syllables
    # exception_del are words that need less syllables

    exception_add = ['serious', 'crucial']
    exception_del = ['fortunately', 'unfortunately']

    co_one = ['cool', 'coach', 'coat', 'coal', 'count', 'coin', 'coarse', 'coup', 'coif', 'cook', 'coign', 'coiffe',
              'coof', 'court']
    co_two = ['coapt', 'coed', 'coinci']

    pre_one = ['preach']

    syls = 0  # added syllable number
    disc = 0  # discarded syllable number

    # 1) if letters < 3 : return 1
    if len(word) <= 3:
        syls = 1
        return syls

    # 2) if doesn't end with "ted" or "tes" or "ses" or "ied" or "ies", discard "es" and "ed" at the end.
    # if it has only 1 vowel or 1 set of consecutive vowels, discard. (like "speed", "fled" etc.)

    if word[-2:] == "es" or word[-2:] == "ed":
        doubleAndtripple_1 = len(re.findall(r'[eaoui][eaoui]', word))
        if doubleAndtripple_1 > 1 or len(re.findall(r'[eaoui][^eaoui]', word)) > 1:
            if word[-3:] == "ted" or word[-3:] == "tes" or word[-3:] == "ses" or word[-3:] == "ied" or word[
                                                                                                       -3:] == "ies":
                pass
            else:
                disc += 1

    # 3) discard trailing "e", except where ending is "le"

    le_except = ['whole', 'mobile', 'pole', 'male', 'female', 'hale', 'pale', 'tale', 'sale', 'aisle', 'whale', 'while']

    if word[-1:] == "e":
        if word[-2:] == "le" and word not in le_except:
            pass

        else:
            disc += 1

    # 4) check if consecutive vowels exists, triplets or pairs, count them as one.

    doubleAndtripple = len(re.findall(r'[eaoui][eaoui]', word))
    tripple = len(re.findall(r'[eaoui][eaoui][eaoui]', word))
    disc += doubleAndtripple + tripple

    # 5) count remaining vowels in word.
    numVowels = len(re.findall(r'[eaoui]', word))

    # 6) add one if starts with "mc"
    if word[:2] == "mc":
        syls += 1

    # 7) add one if ends with "y" but is not surrouned by vowel
    if word[-1:] == "y" and word[-2] not in "aeoui":
        syls += 1

    # 8) add one if "y" is surrounded by non-vowels and is not in the last word.

    for i, j in enumerate(word):
        if j == "y":
            if (i != 0) and (i != len(word) - 1):
                if word[i - 1] not in "aeoui" and word[i + 1] not in "aeoui":
                    syls += 1

    # 9) if starts with "tri-" or "bi-" and is followed by a vowel, add one.

    if word[:3] == "tri" and word[3] in "aeoui":
        syls += 1

    if word[:2] == "bi" and word[2] in "aeoui":
        syls += 1

    # 10) if ends with "-ian", should be counted as two syllables, except for "-tian" and "-cian"

    if word[-3:] == "ian":
        # and (word[-4:] != "cian" or word[-4:] != "tian") :
        if word[-4:] == "cian" or word[-4:] == "tian":
            pass
        else:
            syls += 1

    # 11) if starts with "co-" and is followed by a vowel, check if exists in the double syllable dictionary, if not, check if in single dictionary and act accordingly.

    if word[:2] == "co" and word[2] in 'eaoui':

        if word[:4] in co_two or word[:5] in co_two or word[:6] in co_two:
            syls += 1
        elif word[:4] in co_one or word[:5] in co_one or word[:6] in co_one:
            pass
        else:
            syls += 1

    # 12) if starts with "pre-" and is followed by a vowel, check if exists in the double syllable dictionary, if not, check if in single dictionary and act accordingly.

    if word[:3] == "pre" and word[3] in 'eaoui':
        if word[:6] in pre_one:
            pass
        else:
            syls += 1

    # 13) check for "-n't" and cross match with dictionary to add syllable.

    negative = ["doesn't", "isn't", "shouldn't", "couldn't", "wouldn't"]

    if word[-3:] == "n't":
        if word in negative:
            syls += 1
        else:
            pass

            # 14) Handling the exceptional words.

    if word in exception_del:
        disc += 1

    if word in exception_add:
        syls += 1


        # calculate the output
    return numVowels - disc + syls

def hi_build(d, cnt):
    dd = d
    while sum(dd.values()) < cnt:
        try:
            up = ran_words(1)
            dd.update(up)
            if sum(dd.values()) == cnt:
                return [dd]
            else:
                if sum(dd.values()) > cnt:
                    dd = {}
        except Exception:
            pass
    return [dd]


m_lst = hi_build(ran_words(1), 5) + hi_build(ran_words(1), 7) + hi_build(ran_words(1), 5)

stanz1 = ' '.join(m_lst[0].keys())
stanz2 = ' '.join(m_lst[1].keys())
stanz3 = ' '.join(m_lst[2].keys())

lines = stanz1,stanz2,stanz3
lines = '\n'.join(lines)
print('')
print(lines.lower())
print('')
