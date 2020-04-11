from PIL import Image, ImageDraw, ImageFont
import time
import random
from bs4 import BeautifulSoup, NavigableString, Tag
import requests

class Coronaparser:
    
    def __init__(self, delay=60, grouptoken=None, groupid=None):
        self.delay = delay
        self.grouptoken = grouptoken
        if grouptoken:
            import vk_api
            self.vk_session = vk_api.VkApi(token=self.grouptoken)
            self.vk = self.vk_session.get_api()
            self.groupid = groupid
    
    def generate_new(self, country=None):
        while True:
            if self.grouptoken:
                self.post_image_to_vk(country=country)
                continue
            self.generate_image(country)
            time.sleep(self.delay * 60)
    
    def get_corona_data(self, country=None):
        html = requests.get('https://www.worldometers.info/coronavirus/').text #get html
        soup = BeautifulSoup(html)
        main_counters = soup.findAll("div", {"class": "maincounter-number"}) #find infected, deaths and recovered
        
        corona_data = {'cases': main_counters[0].text,
                'deaths': main_counters[1].text,
                'recovered': main_counters[2].text}
        
        if country:
            try:
                country_stats = soup.find(string=country).parent.parent.parent #find country table
                sorted_stats = [stat.text for stat in list(country_stats)[:8] if isinstance(stat, Tag)][1:] #gets stats from country table, cut off the country name

                corona_data[f'{country}_cases'] = sorted_stats[0]
                corona_data[f'{country}_new'] = sorted_stats[1] if sorted_stats[1] else "0"
                corona_data[f'{country}_deaths']= sorted_stats[2]
            except:
                raise NameError("The country has not been recognized. Try inputting a different country, perhaps?")
        
        return corona_data
    
    def post_image_to_vk(self, country=None):
        from io import BytesIO
        import requests
        import json
        
        image = self.generate_image(country=country)
        fp = BytesIO()
        image.save(fp, format='PNG') #save image to bytes
        
        fp.seek(0) #switch cursor into beginning so requests can read it
        
        post_upload = requests.post(
        self.vk.photos.getWallUploadServer().get("upload_url"),
        files={'file1': ('photo.png', fp, 'image/png')}) #upload to vk wall upload with mime type and name
        
        upload_contents = json.loads(post_upload.text) #jsonize the response from post upload
        
        post_save = self.vk.photos.saveWallPhoto(
        server=upload_contents["server"], 
        hash=upload_contents["hash"], 
        photo=upload_contents["photo"]) #finally save the photo on vk servers

        attachment = "photo" + str(post_save[0].get("owner_id")) + '_'+ str(post_save[0].get('id'))
        self.vk.wall.post(owner_id=-self.groupid,
        attachments=attachment)
        print("[" + time.strftime("%Y.%m.%D %H:%M") + "] Posted a post succesfully.")
    
    def generate_image(self, country=None):

        img = Image.open("bg_eng.png") #open background
        canvas = ImageDraw.Draw(img) #open it as drawable

        font = ImageFont.truetype("font.ttf", 35) #numbers font
        
        data = self.get_corona_data(country=country)

        canvas.text((458, 125), data["cases"], fill=(120,0,120), font=font) #number of cases
        canvas.text((65, 125), data["deaths"], fill=(100,15,20), font=font) #number of deaths
        canvas.text((255, 125), data["recovered"], fill=(0,120,31), font=font) #number of recovered

        if country:
            canvas.text((130,300), f"Infected in {country}: " + data[f"{country}_cases"], fill=(190,190,190), font=font) #cases country
            canvas.text((130,340), f"New cases in {country}: " + data[f"{country}_new"], fill=(10,20,190), font=font) #new cases country
            canvas.text((130, 380), f"Deaths in {country}: " + data[f"{country}_deaths"], fill=(190,15,15), font=font) #deaths country
            
        font_time = ImageFont.truetype("font.ttf", 26) #font for time
        canvas.text((445,400), time.strftime("%Y.%m.%d %H:%M"), fill=(0,0,0), font=font_time) #current time

        img.save('pil_text.png')
        print('[' + time.strftime("%Y.%m.%d %H:%M") + '] Image generated.')
        return img
