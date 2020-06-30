import unittest
import sys
sys.path.append(".")
from utils import *
import pandas as pd
import json
import io

class test_eg(unittest.TestCase):
    #Ids used to build this are in kubernetes demo
    #under jupyter notebook fix stardog list handling
    def test_eg_builder(self):

        data = pd.read_csv('./Tests/multiple_datasets.csv')

        eg = parse_csv(data)

        eg = clean_eg(eg)

        should_be = {
            "@id":'ark:99999/9686e156-0463-40e0-83fd-6883dc805b30',
            "name":"Created Data",
            "author":"All",
            "eg:generatedBy":{
                "@id":'ark:99999/8eb0ce33-5539-48ac-86ff-e3c3256b005a',
                'eg:usedDataset':[
                    {
                        "@id":'ark:99999/ffb37fc2-efdd-4adb-8fab-9704ab07da96',
                        "name":'Data1',
                        'author':'Justin'
                    },
                    {
                        "@id":'ark:99999/f435f304-1d46-46fe-b92b-4d177455113a',
                        "name":'Data2',
                        'author':'Max'
                    },
                ],
                "eg:usedSoftware":[
                    {
                        "@id":'ark:99999/3c797cab-758f-41d0-bb78-db1bf3c28ee6',
                        "name":'soft1',
                        'author':'Sadnan',
                    },
                    {
                        "@id":'ark:99999/35ee5d68-adc3-4d2b-b0d2-c7c6a6011c9a',
                        "name":'soft2',
                        'author':'tim',
                    },
                    {
                        "@id":'ark:99999/0c4a1dca-efd1-4922-a1eb-c2e8b4cec66d',
                        "name":'soft3',
                        'author':'Doug',
                    }
                ]
            }

        }

        self.assertEqual(eg,should_be)

if __name__ == '__main__':
    unittest.main()
