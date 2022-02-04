from io import BytesIO

import requests
from colorthief import ColorThief
from PIL import Image


def color_from_image(url:str):
    response=requests.get(url, headers={'User-Agent': 'Custom'} )
    try:
        response.raise_for_status()
        bytes=BytesIO(response.content) 
        palette=ColorThief(bytes).get_palette(color_count=2,quality=2)[0:2]
        if __name__ == '__main__':
            for color in palette:
                img=Image.new(mode="RGB",size=(400,400),color=color)
                img.show()
        return palette
    except requests.exceptions.RequestException:
        print("Couldn't load "+url)
        return None

if __name__ == '__main__':
    print(color_from_image("https://tmssl.akamaized.net/images/wappen/head/27.png?lm=1498251238"))
    print(color_from_image("https://tmssl.akamaized.net/images/wappen/head/16.png?lm=1396275280"))