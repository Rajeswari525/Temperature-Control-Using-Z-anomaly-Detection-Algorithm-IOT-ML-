import json,time,math,statistics,conf,requests
from boltiot import Bolt,Sms,Email
def send_telegram_message(message):      
    url = "https://api.telegram.org/" + conf.telegram_bot_id + "/sendMessage"    
    data = { "chat_id": conf.telegram_chat_id,             
             "text": message      
           }  
    try:  
        response = requests.request( "GET",  
                                      url,                                   
                                      params=data                          
                                   )    
        print("This is the Telegram response")     
        print(response.text)        
        telegram_data = json.loads(response.text)       
        return telegram_data["ok"]   
    except Exception as e:      
        print("An error occurred in sending the alert message via Telegram")    
        print(e)
        return False      
def compute_bounds(history_data,frame_size,factor):
    if len(history_data)<frame_size :      
        return None    
    if len(history_data)>frame_size :     
        del history_data[0:len(history_data)-frame_size]
    Mn=statistics.mean(history_data)
    Variance=0 
    for data in history_data: 
        Variance += math.pow((data-Mn),2)
    Zn=0
    Zn = factor*math.sqrt(history_data[frame_size-1])+Zn    
    Low_bound = history_data[frame_size-1]-Zn
    High_bound = history_data[frame_size-1]+Zn
    return [High_bound,Low_bound] 
mybolt = Bolt(conf.API_KEY, conf.DEVICE_ID)
sms = Sms(conf.SSID, conf.AUTH_TOKEN, conf.TO_NUMBER, conf.FROM_NUMBER)
mailer = Email(conf.MAILGUN_API_KEY, conf.SANDBOX_URL,conf.SENDER_MAIL,conf.RECIPIENT_MAIL)
history_data=[]

while True:    
    response = mybolt.analogRead('A0')
    data = json.loads(response)  
    if data['success'] != 1:     
        print("There was an error while retriving the data.")   
        print("This is the error:"+data['value'])       
        time.sleep(2)   
        continue  
    sensor_value= int(data['value'])   
    sensor_valuec = sensor_value/10.24    
    print ("The current sensor value is : "+str(sensor_valuec))
    sensor_value=0  
    try:      
        sensor_value = int(data['value']) 
    except e: 
        print("There was an error while parsing the response: ",e)    
        continue  
    bound = compute_bounds(history_data,conf.FRAME_SIZE,conf.MUL_FACTOR) 
    if not bound:    
        required_data_count=conf.FRAME_SIZE-len(history_data)   
        print("Not enough data to compute Z-score. Need ",required_data_count," more data points")     
        history_data.append(int(data['value']))    
        time.sleep(2)     
        continue
    try:   
        if sensor_value > bound[0] :
            buzz=mybolt.digitalWrite('1',"HIGH")
            print(buzz)
            print("Anomaly of the temperature occured because of increase in temperature sending an alert messages") 
            """ SMS """
            print ("The temperature level increased suddenly. Sending an SMS")   
            response = sms.send_sms("The temperature has raised to:"+str(sensor_valuec)+"degree celcius")          
            print("This is the response ",response) 
            """ TELEGRAM """
            message = "Alert! Sensor value has increased The current value is " + str(sensor_valuec)     
            telegram_status = send_telegram_message(message)        
            print("This is the Telegram status:", telegram_status) 
            """ MAIL """
            print("Making request to Mailgun to send an email")     
            response = mailer.send_email("Alert","The Current temperature sensor value is " +str(sensor_valuec))     
            response_text = json.loads(response.text)      
            print("Response received from Mailgun is:"+str(response_text['message']))           
            print(message.sid)
        elif sensor_value < bound[1]:
             buzz=mybolt.digitalWrite('1',"HIGH")
             print(buzz)
             print("Anomaly of the temperature occured because of increase in temperature sending an alert messages") 
             """ SMS """
             print ("The temperature level decreased suddenly. Sending an SMS")    
             response = sms.send_sms("The temperature has decreased to : "+str(sensor_valuec)+"degree celcius")          
             print("This is the response ",response)   
             """ TELEGRAM """
             message = "Alert! Sensor value has decreased The current value is " + str(sensor_valuec)     
             telegram_status = send_telegram_message(message)       
             print("This is the Telegram status:", telegram_status)
             """ MAIL """
             print("Making request to Mailgun to send an email")     
             response = mailer.send_email("Alert","The Current temperature sensor value is " +str(sensor_valuec))          
             response_text = json.loads(response.text)           
             print("Response received from Mailgun is:"+str(response_text['message']))       
        history_data.append(sensor_value);   
    except Exception as e:      
        print ("Error",e)  
    time.sleep(2)

