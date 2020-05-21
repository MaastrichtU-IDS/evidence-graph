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
                data=json.dumps({'eg:hasEvidenceGraph':eg_id}))

def eg_exists(ark):
    '''
    Pings ors to see if ark is reconginzed
    '''

    r = requests.get(ORS_URL + ark)

    meta = r.json()

    if 'eg:hasEvidenceGraph' in meta.keys():
        return True, meta['eg:hasEvidenceGraph']
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

    results = conn.paths("PATHS START ?x=<"+ ark + "> END ?y VIA ?p",content_type='text/csv')
    string_csv = io.StringIO(results.decode("utf-8"))

    df_eg = pd.read_csv(string_csv, sep=",")

    return df_eg


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

        if 'eg' not in key and key != '@id' and key != 'author' and key != 'name' and key != '@type':
            eg.pop(key, None)
            continue

        if isinstance(eg[key],dict):
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
    eg = build_evidence_graph(df_eg)
    eg = clean_eg(eg)

    return eg
