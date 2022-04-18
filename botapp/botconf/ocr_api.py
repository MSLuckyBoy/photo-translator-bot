import requests
import json

import sys
sys.path.append('..')

from django.conf import settings

url = "https://microsoft-computer-vision3.p.rapidapi.com/ocr"
querystring = {"detectOrientation": "true", "language": "unk"}
headers = {
    'content-type': "application/json",
    "x-rapidapi-key": settings.OCR_API_KEY,
    'x-rapidapi-host': "microsoft-computer-vision3.p.rapidapi.com"
}

def scan(img_url, max_width=70):
    response = requests.request("POST", url, json={"url": img_url}, headers=headers, params=querystring)
    
    data = json.loads(response.text)

    text = ''
    i = 0
    for region in data['regions']:
        region_width = int(region['boundingBox'].split(",")[2]) / 100
        i+=1
        
        for line in region['lines']:
            for word in line['words']:
                text += word['text'] + ' '

            lls = line['words'][-1]['text'][-1]
            line_width = int(line['boundingBox'].split(",")[2]) / region_width

            if lls in [".", ";", ":"]:
                text += '\n'
            elif line_width <= max_width:
                text += '\n'

        if i != len(data['regions']):
            text += '\n\n'

    return text
