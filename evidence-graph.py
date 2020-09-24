#© 2020 By The Rector And Visitors Of The University Of Virginia

#Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import flask, stardog, logging, os
import pandas as pd
from flask import Flask, render_template, request, redirect,jsonify
from utils import *
from auth import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TESTING = os.environ.get("NO_AUTH",False)

app = Flask(__name__)

app.url_map.converters['everything'] = EverythingConverter

@app.route('/')
def homepage():
    return 'working'

@app.route('/<everything:ark>')
@token_required
def eg_builder(ark):

    logger.info('Homepage handling request %s', request)

    token = request.headers.get("Authorization")

    args = request.args

    include = []
    for k, v in args.items():
        if v == '1':
            include.append(k)


    #Check to make sure request is for known ark
    try:
        exists, eg_id = eg_exists(ark,token)
    except:
        logger.error('User gievn ark does not exist ' + str(ark))
        return jsonify({'error':'Given ark does not exist.'}),503


    logger.info('Creating Evidence Graph for %s', ark)
    try:
        eg = create_eg_json(ark,keep = include)
    except:
        logger.error('Failed to create eg for ark: %s',ark,
                        exc_info=True)
        return jsonify({'error':'Server failed to create evidence graph.'}),503

    #
    # Mint ark for evidence graph
    #
    # try:
    #     eg_id = mint_eg_id(eg)
    #     add_eg_to_og_id(ark,eg_id)
    # except:
    #     logger.error('Minting evidence graph failed.',exc_info=True)
    #     return eg

    return eg

if __name__ == "__main__":
    if TESTING:
        app.config['TESTING'] = True
    app.run(host='0.0.0.0')
