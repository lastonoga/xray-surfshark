import asyncio
import json
from dotenv import dotenv_values
import telebot

config = dotenv_values(".env")

# Global vars
SURFHARK_CONFIG_FILE = 'config.json'
ALLOWED_IDS = config.get('TELEGRAM_ADMIN_IDS').split(",")

bot = telebot.TeleBot(config.get('TELEGRAM_TOKEN'))

def get_vpn_config():
    with open(SURFHARK_CONFIG_FILE) as file:
        data = json.load(file)
    
    cleaned = []
    for item in data:
        cleaned.append({
            "country": item["country"],
            "location": item["location"],
            "countryCode": item["countryCode"],
            "region": item["region"],
            "connectionName": item["connectionName"],
            "pubKey": item["pubKey"],
            "flagUrl": item["flagUrl"],
        })

    return cleaned

def generate_xray_outbound(vpn = None):
    if vpn is None:
        return {
            "protocol": "freedom",
            "tag": "DIRECT"
        }
    
    return {
        "protocol": "wireguard",
        "tag": "DIRECT",
        "settings": {
          "secretKey": config.get('WIREGUARG_SECRET'),
          "address": [
            "10.14.0.2/32"
          ],
          "peers": [
            {
              "endpoint": f"{vpn['connectionName']}:{config.get('WIREGUARG_PORT')}",
              "publicKey": vpn['pubKey']
            }
          ],
          "mtu": int(config.get('WIREGUARG_MTU')),
        }
    }

def test_xray_config(vpn = None):
    with open(config.get('XRAY_CONFIG')) as file:
        data = json.load(file)

    if not data:
        raise Exception("No Xray Config")

def update_xray(vpn = None):
    with open(config.get('XRAY_CONFIG')) as file:
        data = json.load(file)

    for index, item in enumerate(data['outbounds']):
        if item['tag'] == 'DIRECT':
            data['outbounds'][index] = generate_xray_outbound(vpn)
     
    with open(config.get('XRAY_CONFIG'), "w") as outfile:
        outfile.write(json.dumps(data, indent=4))


# Bot
commands = {
    "list": "Show all countries possible for VPN",
    "use": "Use VPN country by ID",
}

bot.set_my_commands(
    commands=[
        telebot.types.BotCommand(name, f"{name} {commands[name]}") for name in commands
    ],
)

def auth(message):
    if f'{message.from_user.id}' not in ALLOWED_IDS:
        return False
    return True

# help page
@bot.message_handler(commands=['help'])
def send_help(m):
    cid = m.chat.id
    help_text = "The following commands are available: \n"
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        help_text += "/" + key + ": "
        help_text += commands[key] + "\n"
    bot.send_message(cid, help_text)  # send the generated help page

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not auth(message):
        print(message.from_user.id)
        print(ALLOWED_IDS)
        return bot.reply_to(message, "You are not allowed. It's private bot.")
    bot.reply_to(message, "Heya, you are allowed to manage VPN")

@bot.message_handler(commands=['list'])
def list_vpns(message):
    if not auth(message):
        pass
    
    text = [
        'None - No VPN, only proxy'
    ]

    for id, item in enumerate(get_vpn_config()):
        text.append(f'#{id} – {item["country"]}, {item["location"]}') 
    
    bot.reply_to(message, "\n".join(text))


@bot.message_handler(commands=['use'])
def update_vpn(message):
    if not auth(message):
        pass
    
    id = message.text[5::]
    vpns = get_vpn_config()
    newVpn = None

    try:
        newVpn = vpns[int(id)]
    except Exception as e:
        print(e)
        
    update_xray(newVpn)

    if newVpn:
        bot.reply_to(message, f"Switch to {newVpn['country']}, {newVpn['location']}")
    else:
        bot.reply_to(message, "Disable VPN")


def run():
    test_xray_config()
    bot.infinity_polling()

if __name__ == "__main__":
    run()