import pywhatkit

def send_whatsapp(number, message):
    pywhatkit.sendwhatmsg_instantly(number, message)
