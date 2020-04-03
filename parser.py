from PIL import Image, ImageDraw, ImageFont
import vk_api
import time
import random
from bs4 import BeautifulSoup, NavigableString, Tag
import requests

class Notifier:
    
    def __init__(self, delay, grouptoken):
        self.delay = delay
        self.grouptoken = grouptoken
        self.infected = self.get_corona_data().get("cases")
        self.vk_session = vk_api.VkApi(token=self.grouptoken)
        self.vk = self.vk_session.get_api()
        self.check_for_new()
    
    def check_for_new(self):
        while True:
            data = self.get_corona_data()
            #message = 'Заражённых: {}\nСмертей: {}\nЗаражённых по РФ: {}\nСмертей по РФ: {}\nНовых случаев в РФ: {}\n\nВ С Ё\nС\nЁ '.format(
                #data.get("cases"), data.get("deaths"), data.get("russia_cases"), data.get("russia_deaths"), data.get("russia_new"))
            #self.send_new_post(message)
            self.post_image_to_vk()
            self.infected = data.get('cases') #update old number of infected
            time.sleep(self.delay * 60)
    
    def get_corona_data(self):
        html = requests.get('https://www.worldometers.info/coronavirus/').text #get html
        soup = BeautifulSoup(html)
        main_counters = soup.findAll("div", {"class": "maincounter-number"}) #find all main counters
        
        russia_stats = soup.find(string="Russia").parent.parent #find russian table
        sorted_stats = [stat.text for stat in list(russia_stats)[:8] if isinstance(stat, Tag)] #gets stats from russian table
        sorted_stats.remove("Russia") #we don't need country name, huh

        corona_data = {'cases': main_counters[0].text,
        'deaths': main_counters[1].text,
        'recovered': main_counters[2].text,
        'russia_cases': sorted_stats[0],
        'russia_new': sorted_stats[1],
        'russia_deaths': sorted_stats[2]}
        return corona_data
    
    def post_image_to_vk(self):
        from io import BytesIO
        import requests
        import json
        
        image = self.generate_image(self.get_corona_data().get('cases'))
        fp = BytesIO()
        image.save(fp, format='PNG') #save image to bytes
        
        fp.seek(0) #switch cursor into beginning so requests can read it
        
        post_upload = requests.post(
        self.vk.photos.getWallUploadServer().get("upload_url"),
        files={'file1': ('photo.png', fp, 'image/png')}) #upload to vk wall upload with mime type and name
        
        upload_contents = json.loads(post_upload.text) #jsonize the response from post upload
        
        post_save = self.vk.photos.saveWallPhoto(
        server=upload_contents.get("server"), 
        hash=upload_contents.get("hash"), 
        photo=upload_contents.get("photo")) #finally save the photo on vk servers

        self.vk.wall.post(owner_id=-192535436,
        attachments="photo" + str(post_save[0].get("owner_id")) + '_'+ str(post_save[0].get('id'))) #format to attach the photo
        print("[" + time.strftime("%Y.%m.%d %H:%M") + "] Posted a post succesfully.")
    
    def generate_image(self, infected):

        img = Image.open("stain3.png") #open background
        d = ImageDraw.Draw(img) #open it as drawable

        font = ImageFont.truetype("arial.ttf", 35) #other things font

        data = self.get_corona_data()
        message = 'В мире: {}\nСмертей: {}\nВыздоровело:{}\nЗаражённых в РФ: {}\nСмертей в РФ: {}\nНовых случаев в РФ: {}'.format(
                data.get("cases"), data.get("deaths"), data.get("recovered"), data.get("russia_cases"), data.get("russia_deaths"), data.get("russia_new"))
        message_list = message.split('\n') #get data set. not the best way, will fix later

        d.text((456, 155), message_list[1], fill=(120,0,120,256), font=font) #number of cases
        d.text((56, 155), message_list[4], fill=(100,15,20,256), font=font) #number of deaths
        d.text((249, 155), message_list[7], fill=(0,120,31,256), font=font) #number of recovered


        d.text((130,300), message_list[9], fill=(190,190,190,256), font=font) #cases russia
        
        if not message_list[11]: #if there's no new cases, it's empty, so we replace it with 0 for organic look
            message_list[11] = "0"
        d.text((130,340), message_list[11], fill=(10,20,190,256), font=font) #new cases russia
        d.text((130, 380), message_list[10], fill=(190,15,15,256), font=font) #deaths russia
        
        font_time = ImageFont.truetype("arial.ttf", 26) #font for time
        d.text((445,400), time.strftime("%Y.%m.%d %H:%M"), fill=(0,0,0,256), font=font_time) #current time
        
        infected = int(infected[:-3].replace(',', '')) #we turn the data into int instead of string
        infected_past = int(self.infected[:-3].replace(',', ''))
        difference = infected - infected_past
        
        if infected_past != infected:
            d.text((135,220), f"Прирост за час: {difference} ({round((difference / infected) * 100, 2)}%)", fill=(190,15,15,256), font=font)
        
        img.save('pil_text.png')
        return img
    
    def send_message(self, msg):
          self.vk.messages.send(
                    chat_id=1,
                    message=msg,
                    random_id=random.randint(1000000, 1000000000))