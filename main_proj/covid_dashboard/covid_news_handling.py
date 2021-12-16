"""COVID NEWS HANDLER"""
import sched
import time
import json
from datetime import datetime
import requests

#News scheduler
s_news = sched.scheduler(time.time, time.sleep)
#Scheduled updates
sched_updates = []

#API Key and URL
with open('config.json', 'r', encoding='utf-8') as jsonfile:
    config_data = json.load(jsonfile)

api = config_data['api']
url = "https://newsapi.org/v2/top-headlines"

#News Articles
news_list = []
removed_articles = config_data['removed_articles']

def enter_log(log_type, content):
    """Enter log into main log file"""

    now = datetime.now()
    with open('resources/main.log', 'a', encoding='utf-8') as file:
        file.write(f'[{now.strftime("%m/%d/%Y %H:%M:%S")}]{log_type}: {content}\n')

def news_API_request(covid_terms='covid coronavirus COVID-19'):
    """Get Covid News"""
    #Split covid terms to keywords
    new_covid_terms = []
    for item in covid_terms.split(' '):
        new_covid_terms.append(item)
    #Send API request with needed parameters
    payload = {'q': new_covid_terms, 'country': 'gb', 'apiKey': api}
    news = requests.get(url, params=payload)
    news_json = news.json()

    return (news_json)

def schedule_news_updates(update_interval, update_name, u_type=None, repeat=None):
    """Schedule Updates"""
    #If update news schedule s_news
    if u_type == 'news':
        #Event item template
        update_event = {
        'title': update_name,
        'type': u_type,
        'repeat': repeat,
        'event': None
        }
        #If update repeats pass arguments
        if repeat:
            update_event['event'] = s_news.enter(update_interval,
            1,
            update_news,
            argument=(update_name, u_type, repeat))
        else:
            update_event['event'] = s_news.enter(update_interval, 1, update_news)

        sched_updates.append(update_event)

def update_news(name=None, u_type=None, repeat=None, data=news_API_request()['articles']):
    """Update News Articles"""
    #Find number of articles
    index = len(data)
    #Clear list 
    news_list.clear()
    count = 0
    i = 0
    #Loop through articles
    while i < 4:
        if count < index:
            #Check if in removed_articles
            if (data[count]['title'] not in removed_articles) and (data[count]['description'] != ''):
                #Add article to news_list
                news_list.append({
                    'title': data[count]['title'],
                    'content': data[count]['description']})

                count += 1
                i += 1
            elif count > index:
                i = 4
            else:
                count += 1
        else:
            break

    if repeat:
        if u_type == 'news':
            schedule_news_updates(10, name, u_type, repeat)

    #Log News Update
    enter_log('[INFO]', 'ARTICLES UPDATED')
