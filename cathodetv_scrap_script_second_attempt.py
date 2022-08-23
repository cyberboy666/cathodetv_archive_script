"""
first i scrap all the metadata from their instagram using https://github.com/arc298/instagram-scraper
with the command: instagram-scraper cathodecinema --media-types none --media-metadata -u cyberboy666 -p <password>
this outputs in json format

then i will parse this json data trying to seperate into 'themes' and 'films', which will then be converted into letterboxd csv format for uploading....

"""

import json
import re
import datetime
from time import tzname
import pytz
import csv
from collections import OrderedDict


# open json file and only take the items we care about into a python list
f = open('cathodecinema.json')
data = json.load(f)
posts = data["GraphImages"]

trimmed_list = []
for i in posts:
     trimmed_list.append({'id':i['shortcode'], 'date':datetime.datetime.fromtimestamp(i['taken_at_timestamp'],tz=pytz.timezone('US/Pacific')).date(), 'text':i['edge_media_to_caption']['edges'][0]['node']['text'], 'image':i['display_url']})


# trying to remove non-film night/non scheduled posts
    # first filter: if 'PST\n' is not in the text its prob not a film night post, otherwise it probably is...
    # if 'PST' not in i['text'].upper()  and 'PT\n' not in i['text'].upper() and 'PM\n' not in i['text'].upper():
filter_list = []
for i in trimmed_list:
    if 'PST' not in i['text'].upper()  and 'PT\n' not in i['text'].upper() and 'PM\n' not in i['text'].upper():
        pass
    else:
        filter_list.append(i)


# extracting list of titles from text
# check for a year in brackets - replace '’' with '19' in year and remove director from brackets if in there
# merge with previous line if it seems like year is on new line to title
# remove other space chars

for i in filter_list:
    text_list = i['text'].split('\n')
    title_list = []
    for count, j in enumerate(text_list):
        if re.match('^.*\(.*(19|20)\d{2}\)', j):
            j = re.sub('’(?=\d{2}\))', '19', j)
            j = ')'.join(j.split(')')[:-1]) + ')' # remove everything after last close bracket
            year_brackets = re.search(r'\([^\(]*(19|20)\d{2}\)', j).group(0) # select just the year bracket
            just_year = year_brackets[-5:-1]
            j = j.replace(year_brackets, '(' + just_year + ')')
            j = j.strip()
            if len(j) < 7:
                j = text_list[count - 1] + j
            j = j.replace(u'\xa0', u' ')
            title_list.append(j)
    i['title_list']=title_list

s_filter_list = []
for item in filter_list:
    if len(item['title_list']) > 3:
        s_filter_list.append(item)

# tryextract the theme from line 0 of the text:
# try to remove as much common info language from first line
# if first line is too short take next line as theme
# if theme is too long try to break it around a '.' after 150 char

def filter_common_info(theme_line):
    theme_line = re.sub('tonight!?( &)?( and)?( tomorrow)?!?( sunday)?( night)?', '', theme_line, flags=re.IGNORECASE)
    theme_line = re.sub('all weekend(!)? (long)?(!)?', '', theme_line, flags=re.IGNORECASE)
    theme_line = re.sub('this weekend!?', '', theme_line, flags=re.IGNORECASE)
    theme_line = re.sub('on cathode tv!?', '', theme_line, flags=re.IGNORECASE)
    theme_line = re.sub('today!?', '', theme_line, flags=re.IGNORECASE)
    theme_line = re.sub('early( show)?!?', '', theme_line, flags=re.IGNORECASE)
    theme_line = re.sub('\d{1,2}/\d{1,2}/\d{2,4}', '', theme_line, flags=re.IGNORECASE)
    theme_line = re.sub('(\d:\d)?\d[AP]M *(PST)?(!)?', '', theme_line, flags=re.IGNORECASE)
    theme_line = re.sub('(?:Tue(?:sday)?|Wed(?:nesday)?|Thu(?:rsday)?|Sat(?:urday)?|(Mon|Fri|Sun)(?:day)?)?,? ?(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|(Nov|Dec)(?:ember)) ?\d{1,2},?( \d\d\d\d)?', '', theme_line, flags=re.IGNORECASE)
    theme_line = theme_line.strip()
    theme_line = theme_line.strip('-')
    theme_line = theme_line.strip(':')
    theme_line = theme_line.strip()
    return theme_line

for i in s_filter_list:
    i['text'] = i['text'].replace(u'\xa0', u' ')
    text_list = i['text'].split('\n')
    text_list = [l for l in text_list if len(l) > 3]
    i['theme'] = text_list[0]
    i['theme'] = filter_common_info(i['theme'])
    if len(i['theme']) < 7:
        i['theme'] = text_list[1]
        i['theme'] = filter_common_info(i['theme'])
    if len(i['theme']) < 7:
        i['theme'] = text_list[2]
        i['theme'] = filter_common_info(i['theme'])
    if len(i['theme']) > 150:
        i['theme'] = i['theme'][:150] + i['theme'][150:].split('.')[0]



#### generate html

# with open("cathode.html", "a") as file:
#     file.write('<h1>cathodetv stream archive</h1>')
#     for item in s_filter_list:
#         file.write(f'<details><summary>{item["date"]}</summary>\n')
#         file.write(f'<h2>{item["theme"]}</h2>\n')
#         file.write('<ul>\n')
#         for film in item['title_list']:
#             file.write(f'<li>{film}</li>\n')
#         file.write('</ul></details>\n')


## seperate into title and year

for screening in s_filter_list:
    dict_data = []
    for film in screening['title_list']:
        year = ''
        if re.search(r'(?<=\()(19|20)\d{2}(?=\))', film):
            year = re.search(r'(?<=\()(19|20)\d{2}(?=\))', film).group(0)
        else:
            print(film)
        film_data = {}
        film_data['year'] = year
        film_data['title'] = re.sub(r'\((19|20)\d{2}\)', '', film).strip()
        film_data['date'] = screening['date']
        film_data['theme'] = screening['theme']
        dict_data.append(film_data)
    screening['dict_data'] = dict_data


# writing to a csv file for letterboxd

with open('cathodetv_letterboxd.csv', 'w') as file:
    csv_write = csv.writer(file,delimiter=',')
    csv_write.writerow(['Title', 'Year', 'Note'])
    for count, entry in enumerate(s_filter_list[0]['dict_data']):
        film_count = len(s_filter_list[0]['dict_data'])
        csv_write.writerow([entry['title'], entry['year'], f"{count + 1}/{film_count} CTV_{entry['date']} - {entry['theme']}"])


title_dict = OrderedDict()
for screening in s_filter_list:
    for count, film in enumerate(screening['dict_data']):
        film_count = len(screening['dict_data'])
        if film['title'] in title_dict:
            title_dict[film['title']]['notes'] = title_dict[film['title']]['notes'] + f"\n& {count + 1}/{film_count} CTV_{film['date']} - {film['theme']}"
        else:
            title_dict[film['title']] = {'year': film['year'], 'notes': f"{count + 1}/{film_count} CTV_{film['date']} - {film['theme']}"}