import flask, stardog, logging
import pandas as pd
from flask import Flask, render_template, request, redirect,jsonify
from utils import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

app.url_map.converters['everything'] = EverythingConverter

@app.route('/')
def homepage():
    return 'working'

@app.route('/eg/<everything:ark>')
def eg_builder(ark):

    logger.info('Homepage handling request %s', request)

    #Check to make sure request is for known ark
    try:
        exists, eg_id = eg_exists(ark)
    except:
        logger.error('User gievn ark does not exist ' + str(ark))
        return jsonify({'error':'Given ark does not exist.'}),503


    logger.info('Creating Evidence Graph for %s', ark)
    try:
        eg = create_eg(ark)
    except:
        logger.error('Failed to create eg for ark: %s',ark,
                        exc_info=True)
        return jsonify({'error':'Server failed to create evidence graph.'}),503

    #
    # Mint ark for evidence graph
    #
    try:
        eg_id = mint_eg_id(eg)
        add_eg_to_og_id(ark,eg_id)
    except:
        logger.error('Minting evidence graph failed.',exc_info=True)
        return eg

    return eg

if __name__ == "__main__":
    app.run(host='0.0.0.0')
