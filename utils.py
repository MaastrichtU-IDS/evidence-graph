import os, io, stardog,json
import pandas as pd
from werkzeug.routing import PathConverter
import requests

#session = requests.Session()
#session.auth = (SD_USERNAME,SD_PASSWORD)

SD_URL = os.environ.get('STARDOG_URL','http://stardog.uvadcos.io')
SD_USERNAME = os.environ.get('STARDOG_USERNAME')
SD_PASSWORD = os.environ.get('STARDOG_PASSWORD')

ORS_URL = os.environ.get("ORS_URL","ors.uvadco.io/")
EVI_PREFIX = 'evi:'
conn_details = {
        'endpoint': SD_URL,
        'username': SD_USERNAME,
        'password': SD_PASSWORD
    }
conn = stardog.Connection('ors', **conn_details)

class EverythingConverter(PathConverter):
    regex = '.*?'

def mint_eg_id(eg):
    '''
    Mints Id for newly created evidence graph
    '''

    r = requests.post(ORS_URL + "shoulder/ark:99999",data = json.dumps(eg))

    if 'created' in r.json():
        return r.json()['created']

def add_eg_to_og_id(ark,eg_id):

    r = requests.put(ORS_URL +  ark,
                data=json.dumps({EVI_PREFIX + 'hasEvidenceGraph':eg_id}))

def eg_exists(ark):
    '''
    Pings ors to see if ark is reconginzed
    '''

    r = requests.get(ORS_URL + ark)

    meta = r.json()

    if EVI_PREFIX + 'hasEvidenceGraph' in meta.keys():
        return True, meta[EVI_PREFIX + 'hasEvidenceGraph']
    elif 'error' in meta.keys():
        raise Exception

    return False,0

def existing_eg(eg_id):

    r = requests.get(ORS_URL + eg_id)
    eg = r.json()
    return eg


def query_stardog(ark):
    '''
    Performs the path query
    '''

    results = conn.paths("PATHS ALL START ?x=<"+ ark + "> END ?y VIA ?p",content_type='text/csv')
    string_csv = io.StringIO(results.decode("utf-8"))

    df_eg = pd.read_csv(string_csv, sep=",")

    return df_eg

def is_id(string):
    if 'ark:' in string and len(string) == 46:
        return True
    if 'orchid:' in string:
        return True
    if 'https://orcid.org/' in string:
        return True

    return False

def parse_csv(df):
    '''
    Parses the ugly csv returned from stardog
    to build json evidence graph
    '''

    context = {'http://www.w3.org/1999/02/22-rdf-syntax-ns#':'@',
               'http://schema.org/_id':'@id',
              'http://schema.org/':'',
               'http://example.org/':'eg:',
               'http://example.org/':'evi:',
               "https://wf4ever.github.io/ro/2016-01-28/wfdesc/":'wfdesc:'
              }

    eg = {}
    current = eg
    for index, row in df.iterrows():

        #Nan row indicates next item restart at root node
        if pd.isna(row['x']):
            current = eg
            continue

        #cleans tags
        for key in context:
            if key in row['p']:
                row['p'] = row['p'].replace(key,context[key])
            if key in row['y']:
                row['y'] = row['y'].replace(key,context[key])

        #If key not already in eg add it
        #If its an id make it a dict not just an element
        if row['p'] not in current.keys():
            if is_id(row['y']):
                if row['p'] == '@id':
                    current['@id'] = row['y']
                else:
                    current[row['p']] = {'@id':row['y']}
                    current = current[row['p']]
            else:
                current[row['p']] = row['y']

        #If key already exists and its a new id its
        #not single dict so make it list of dicts
        elif isinstance(current[row['p']],dict):
            if current[row['p']]['@id'] == row['y']:
                current = current[row['p']]
            else:
                current[row['p']] = [current[row['p']],{'@id':row['y']}]
                current = current[row['p']][-1]

        #Look to see if we're moving into an element of the list
        #ie this is adding on to a known id
        #or if we're appending a new id to the list
        elif isinstance(current[row['p']],list):
            missing = True
            for dictionary in current[row['p']]:
                if dictionary['@id'] == row['y']:
                    current = dictionary
                    missing = False
                    break
            if missing:
                current[row['p']].append({'@id':row['y']})
                current = current[row['p']][-1]
    return eg

def build_evidence_graph(data,clean = True):
    '''
    Parses the ugly csv returned from stardog
    to build json evidence graph
    '''
    eg = {}

    context = {'http://www.w3.org/1999/02/22-rdf-syntax-ns#':'@',
          'http://schema.org/':'',
           'http://example.org/':'eg:',
           "https://wf4ever.github.io/ro/2016-01-28/wfdesc/":'wfdesc:'
          }
    trail = []

    for index, row in data.iterrows():
        if pd.isna(row['x']):
            trail = []
            continue
        if clean:
            for key in context:
                if key in row['p']:
                    row['p'] = row['p'].replace(key,context[key])
                print(row['y'])
                if key in row['y']:
                    row['y'] = row['y'].replace(key,context[key])

        if '@id' not in eg.keys():
            eg['@id'] = row['x']

        if trail == []:

            if row['p'] not in eg.keys():
                eg[row['p']] = row['y']

            else:
                trail.append(row['p'])
                if not isinstance(eg[row['p']],dict):
                    eg[row['p']] = {'@id':row['y']}

            continue

        current = eg
        for t in trail:
            current = current[t]

        if not isinstance(current,dict):
            continue

        if row['p'] not in current.keys():
            current[row['p']] = row['y']
        else:
            trail.append(row['p'])

            if not isinstance(current[row['p']],dict):
                current[row['p']] = {'@id':row['y']}

    return eg


def clean_eg(eg,eg_only = True):
    '''
    Goes through json evidence graph removes keys unrelated to basic in or
    the evi ontology fixes minor formatting things
    '''

    for key in list(eg):

        if 'evi' not in key and 'eg' not in key and key != '@id' and key != 'author' and key != 'name' and key != '@type':
            eg.pop(key, None)
            continue

        elif isinstance(eg[key],list):

            for dictionary in eg[key]:
                if isinstance(dictionary,dict):
                    dictionary = clean_eg(dictionary)

        elif isinstance(eg[key],dict):
            if len(eg[key]) == 1:
                #if dict only has one make it no longer a dict
                #just value instead
                eg[key] = eg[key][list(eg[key].keys())[0]]
            else:

                eg[key] = clean_eg(eg[key])

    return eg

def create_eg(ark):
    '''
    Runs all functions required to create an evidence graph
    ie
        1.) Path query
        2.) Parse from csv -> json
        3.) Clean up json
    '''

    df_eg = query_stardog(ark)
    eg = parse_csv(df_eg)
    #eg = build_evidence_graph(df_eg)
    eg = clean_eg(eg)

    eg["@context"] = {
    "@vocab": "http://schema.org/",
    "evi": "http://purl.org/evi/"
    }

    return eg
