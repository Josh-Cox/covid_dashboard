"""COVID DATA HANDLER"""
import sched
import time
from uk_covid19 import Cov19API
from .covid_news_handling import update_news, s_news, config_data, enter_log, sched_updates

#News scheduler
s_data = sched.scheduler(time.time, time.sleep)

def parse_csv_data(csv_filename):
    """Return csv file as list"""
    #Return list of lines as strings
    main_list = []
    with open(csv_filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        for item in lines:
            main_list.append(item.strip())
    return(main_list)

def process_covid_csv_data(covid_csv_data):
    """Process List"""
    #Define values
    hospital_cases = 0
    death_cases = 0
    case_index = 1
    cases_7_days = 0
    #Find Hospital and Death Cases
    for i in range(4, 6):
        index = 1
        while index < len(covid_csv_data) and covid_csv_data[index].split(',')[i] == '':
            index += 1
        if i == 4:
            death_cases = covid_csv_data[index].split(',')[i]
        else:
            hospital_cases = covid_csv_data[index].split(',')[i]
    #Find Cases in last 7 days
    while case_index < len(covid_csv_data) and covid_csv_data[case_index].split(',')[6] == '':
        case_index += 1
    for i in range(case_index+1, case_index+8):
        cases_7_days += int(covid_csv_data[i].split(',')[6])
    return(int(cases_7_days), int(hospital_cases), int(death_cases))

def covid_API_request(location=config_data['location'], location_type=config_data['location_type']):
    """Get Covid Data"""

    #API Structure
    cases_and_deaths = {'area_code': 'areaCode',
     'area_name': 'areaName',
      'area_type': 'areaType',
       'date': 'date',
        'cum_deaths': 'cumDailyNsoDeathsByDeathDate',
         'hospital_cases': 'hospitalCases',
          'new_cases_by_specimen': 'newCasesBySpecimenDate'}

    #Get data from API
    api_filter = [f'areaType={location_type}', f'areaName={location}']
    api = Cov19API(filters=api_filter, structure=cases_and_deaths)
    data = api.get_json()

    return data

def schedule_covid_updates(update_interval, update_name, u_type='covid', repeat=None):
    """Schedule Updates"""
    from covid_dashboard.__main__ import update_covid_data
    #If update covid data schedule s_data
    if u_type == 'covid':
        #Event item template
        update_event = {
        'title': update_name,
        'type': u_type,
        'repeat': repeat,
        'event': None
        }
        #If update repeats pass arguments
        if repeat:
            update_event['event'] = s_data.enter(update_interval,
            1,
            update_covid_data,
            argument=(update_name, u_type, repeat))
        else:
            update_event['event'] = s_data.enter(update_interval, 1, update_covid_data)

        sched_updates.append(update_event)
    #If update both schedule s_data and s_news
    elif u_type == 'both':
        #Event item template
        update_event = {
        'title': update_name,
        'type': u_type,
        'repeat': repeat,
        'event': None
        }
        #If update repeats pass arguments
        if repeat:

            update_event['event'] = s_data.enter(update_interval,
            1,
            update_covid_data,
            argument=(update_name, u_type, repeat))
            sched_updates.append(update_event)

            update_event['event'] = s_news.enter(update_interval,
            1,
            update_news,
            argument=(update_name, u_type, repeat))
            update_event['title'] = f'n{update_name}'
            sched_updates.append(update_event)
        else:

            update_event['event'] = s_data.enter(update_interval, 1, update_covid_data)
            sched_updates.append(update_event)

            update_event['event'] = s_news.enter(update_interval, 1, update_news)
            update_event['title'] = f'n{update_name}'
            sched_updates.append(update_event)

    #Log Update
    enter_log('[INFO]', f'UPDATE ADDED - ({update_name})')

def infection_7_days(data):
    """Calculate 7 Day Infection Rate"""
    index = 0
    total_sum = 0
    #Find latest value
    while index < len(data['data']) and data['data'][index]['new_cases_by_specimen'] is None:
        index += 1
    #Sum 7 latest values
    for i in range(index + 1, index + 8):
        total_sum += data['data'][i]['new_cases_by_specimen']

    return total_sum

def find_value(variable_name, data):
    """Find Newest value"""

    count = 0
    found = False
    for items in data['data']:
        if data['data'][count][variable_name] is None:
            count += 1
        elif found is True:
            break
        else:
            data_name = data['data'][count][variable_name]

    return data_name

def get_data():

    """Get Covid Data"""

    #API Data
    local_data = covid_API_request()
    england_data = covid_API_request('england', 'nation')

    #---------- Set Data Values ----------#

    #National
    national_hospital_cases = find_value('hospital_cases', england_data)
    national_total_deaths = find_value('cum_deaths', england_data)
    national_area_name = find_value('area_name', england_data)
    national_case_7_days = infection_7_days(england_data)

    #Local
    local_area_name = find_value('area_name', local_data)
    local_case_7_days = infection_7_days(local_data)

    #Log Data Update
    enter_log('[INFO]', 'COVID DATA UPDATED')

    return (national_hospital_cases,
    national_total_deaths,
    national_area_name,
    national_case_7_days,
    local_area_name,
    local_case_7_days)
