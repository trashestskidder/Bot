import discord
from discord import app_commands
from discord.ext import commands
import random
import string
from flask import Flask, request, jsonify
import json
import time
import os
import requests
import threading
import base64
from urllib.parse import unquote, parse_qs

app = Flask(__name__)

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

API_KEYS_FILE = "api_keys.json"

payload = {
    "captcha": "",
    "type": ""
}

def log_data(data):
    try:
        if "credit" in data["bypass_response"]:
            del data["bypass_response"]["credit"]
        if "time_taken" in data["bypass_response"]:
            del data["bypass_response"]["time_taken"]
        if "time" in data["bypass_response"]:
            del data["bypass_response"]["time"]
        if "Time Taken" in data["bypass_response"]:
            del data["bypass_response"]["Time Taken"]
        with open('api_log.txt', 'a') as log_file:
            log_file.write(json.dumps(data) + '\n')
    except OSError as e:
        if e.errno == 28:
            print("Log writing skipped")
        else:
            raise

def load_api_keys():
    if os.path.exists(API_KEYS_FILE):
        with open(API_KEYS_FILE, "r") as f:
            return json.load(f)
    return []

def save_api_keys(api_keys):
    with open(API_KEYS_FILE, "w") as f:
        json.dump(api_keys, f)

API_KEYS = load_api_keys()

@bot.event
async def on_ready():
    print(f"\x1b[42m\x1b[30m[+ Success]\x1b[0m\x1b[34m Logged in as {bot.user} \x1b[0m")
    print(f"\x1b[33m --------------------------------------------------- \x1b[0m")
    await bot.tree.sync()

def create_embed(title, description, color=15548997):
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

async def user_has_permission(interaction: discord.Interaction):
    return interaction.user.id in [1108054132130058261, 1260849093127962634]

@bot.tree.command(name="whitelist")
async def whitelist(interaction: discord.Interaction, apikey: str):
    """Whitelist a key"""
    if not await user_has_permission(interaction):
        await interaction.response.send_message("<a:failed:1297217993142698016> You dont have permission", ephemeral=False)
        return
    if apikey not in API_KEYS:
        API_KEYS.append(apikey)
        save_api_keys(API_KEYS)
        embed = create_embed("<a:sucess:1297218018597671013> Whitelist success", f"```\n{apikey}\n```")
        print(f"\x1b[42m\x1b[30m[+ Success]\x1b[0m\x1b[34m Whitelist success : {apikey} \x1b[0m")
    else:
        embed = create_embed("<a:failed:1297217993142698016> Key already whitelisted", f"```\n{apikey}\n```")
        print(f"\x1b[41m\x1b[30m[+ Error]\x1b[0m\x1b[31m Key already whitelisted : {apikey} \x1b[0m")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="blacklist")
async def blacklist(interaction: discord.Interaction, apikey: str):
    """Blacklist a key"""
    if not await user_has_permission(interaction):
        await interaction.response.send_message("<a:failed:1297217993142698016> You dont have permission", ephemeral=False)
        return
    if apikey in API_KEYS:
        API_KEYS.remove(apikey)
        save_api_keys(API_KEYS)
        embed = create_embed("<a:sucess:1297218018597671013> Blacklist success", f"```\n{apikey}\n```")
        print(f"\x1b[42m\x1b[30m[+ Success]\x1b[0m\x1b[34m Blacklist success : {apikey} \x1b[0m")
    else:
        embed = create_embed("<a:failed:1297217993142698016> Key not found", f"```\n{apikey}\n```")
        print(f"\x1b[41m\x1b[30m[+ Error]\x1b[0m\x1b[31m Key not found : {apikey} \x1b[0m")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="showkey")
async def showkey(interaction: discord.Interaction):
    """Show whitelisted key"""
    if not await user_has_permission(interaction):
        await interaction.response.send_message("<a:failed:1297217993142698016> You dont have permission", ephemeral=False)
        return
    if API_KEYS:
        keys = "\n".join(API_KEYS)
        embed = create_embed("<:key:1297218282482434198> Whitelisted key", f"```\n{keys}\n```")
        print(f"\x1b[42m\x1b[30m[+ Success]\x1b[0m\x1b[34m Whitelisted key : \n{keys} \x1b[0m")
    else:
        embed = create_embed("<a:failed:1297217993142698016> No any key are whitelisted", "")
        print(f"\x1b[41m\x1b[30m[+ Error]\x1b[0m\x1b[31m No any key are whitelisted \x1b[0m")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="genkey")
async def genkey(interaction: discord.Interaction):
    """Generate a new key"""
    if not await user_has_permission(interaction):
        await interaction.response.send_message("<a:failed:1297217993142698016> You dont have permission", ephemeral=False)
        return
    new_key = "PLUTO-" + ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    API_KEYS.append(new_key)
    save_api_keys(API_KEYS)
    embed = create_embed("<a:sucess:1297218018597671013> Generated key", f"```\n{new_key}\n```")
    print(f"\x1b[42m\x1b[30m[+ Success]\x1b[0m\x1b[34m Generated key : {new_key} \x1b[0m")
    await interaction.response.send_message(embed=embed, ephemeral=True)

@app.route('/bypass', methods=['GET'])
def bypass_api():
    api_key = request.args.get('api_key')
    if api_key not in API_KEYS:
        return jsonify({"error": "Invalid API key"}), 403
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Please enter URL to bypass or go /supported to see all supported bypass"}), 400
    start_time = time.time()
    if url.startswith('https://flux.li/android/external/start.php?HWID='):
        bypass_api_url = f'https://bypass-beta.vercel.app/api/bypass?url={url}'
        bypass_type = "fluxus"
    elif url.startswith('https://mobile.codex.lol'):
        bypass_api_url = f'http://37.114.41.55:6346/api/codex?url={url}'
        bypass_type = "codex"
    elif url.startswith('https://gateway.platoboost.com/a/8?id='):
        bypass_api_url = f'https://api.robloxexecutorth.workers.dev/delta?url={url}'
        bypass_type = "delta"
    elif url.startswith('https://mobile.codex.lol'):
        bypass_api_url = f'https://api-codex.onrender.com/api/codex?url={url}'
        bypass_type = "codex"
    elif url.startswith('https://linkvertise.com') or url.startswith('https://paster.so') or url.startswith('https://loot-link.com') or url.startswith('https://lootlabs.gg') or url.startswith('https://boost.ink') or url.startswith('https://mboost.me') or url.startswith('https://socialwolvez.com') or url.startswith('https://www.sub2get.com') or url.startswith('https://social-unlock.com') or url.startswith('https://unlocknow.net') or url.startswith('https://sub2unlock.com') or url.startswith('https://sub2unlock.net') or url.startswith('https://sub2unlock.io') or url.startswith('https://sub4unlock.io') or url.startswith('https://rekonise.com') or url.startswith('https://adfoc.us') or url.startswith('https://v.gd') or url.startswith('https://bit.ly') or url.startswith('https://tinyurl.com') or url.startswith('https://is.gd') or url.startswith('https://tiny.cc'):
        bypass_api_url = f'https://api.bypass.vip/bypass?url={url}'
        bypass_type = "ad"
    elif url.startswith('https://gateway.platoboost.com/a/39097?id='):
        return cryptic_bypass(url, start_time)
    else:
        return jsonify({"error": "Unsupported link"}), 400
    try:
        response = requests.get(bypass_api_url)
        data = response.json()
        bypass_time = time.time() - start_time
        log_data({
            "status": "success",
            "url": url,
            "bypass_type": bypass_type,
            "bypass_response": data,
            "bypass_time": bypass_time
        })
        return jsonify({
            "status": "success",
            "result": data.get("key") or data.get("result") or data.get("status"),
            "time": bypass_time
        }), 200
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

def cryptic_bypass(url, start_time):
    id = url.replace("https://gateway.platoboost.com/a/39097?id=", "")
    session = requests.Session()
    bypass_time = time.time() - start_time
    try:
        response = session.get(f"https://api-gateway.platoboost.com/v1/authenticators/39097/{id}").text
        if "key" in response:
            key = json.loads(response)["key"]
            bypass_time = time.time() - start_time
            return jsonify({
                "status": "success",
                "result": key,
                "time": bypass_time
            }), 200
        auth_response = session.post(f"https://api-gateway.platoboost.com/v1/sessions/auth/39097/{id}", json=payload).text
        auth_data = json.loads(auth_response)
        if 'redirect' not in auth_data:
            return jsonify({
                "status": "success",
                "result": "Redirect URL not found in auth response",
                "time": bypass_time
            }), 200
        redirect_url = auth_data["redirect"]
        code = base64.b64decode(parse_qs(unquote(redirect_url))['r'][0].encode()).decode().replace(f"https://gateway.platoboost.com/a/39097?id={id}&tk=", "")
        time.sleep(5)
        second_auth_response = session.put(f"https://api-gateway.platoboost.com/v1/sessions/auth/39097/{id}/{code}", json=payload).text
        second_auth_data = json.loads(second_auth_response)
        if 'redirect' not in second_auth_data:
            return jsonify({
                "status": "success",
                "result": "Second redirect URL not found in second auth response",
                "time": bypass_time
            }), 200
        redirect_url_2 = second_auth_data["redirect"]
        code = base64.b64decode(parse_qs(unquote(redirect_url_2))['r'][0].encode()).decode().replace(f"https://gateway.platoboost.com/a/39097?id={id}&tk=", "")
        time.sleep(5)
        session.put(f"https://api-gateway.platoboost.com/v1/sessions/auth/39097/{id}/{code}", json=payload).text
        final_response = session.get(f"https://api-gateway.platoboost.com/v1/authenticators/39097/{id}").text
        key = json.loads(final_response)["key"]
        bypass_time = time.time() - start_time
        return jsonify({
            "status": "success",
            "result": key,
            "time": bypass_time
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "result": "Please solve the captcha and try again later (5s~)",
            "time": bypass_time
        }), 200
    
@app.route('/supported', methods=['GET'])
def supported():
    return jsonify({"response": "Fluxus, Codex, Delta Android (without hcapcha), Cryptic (without hcapcha), Linkvertise, Paster.so, Loot-link, Loot-labs, Boost.ink, Mboost.me, Socialwolvez, Sub2get, Social-unlock, Unlocknow.net, Sub2unlock.com, Sub2unlock.net, Sub2unlock.io, Sub4unlock.io, Rekonise, Adfoc.us, V.gd, Bit.ly, Tinurl.com, Is.gd, Tiny.cc"}), 200

def run_flask_app():
    app.run(host='0.0.0.0', port=6243)

flask_thread = threading.Thread(target=run_flask_app)
flask_thread.start()

bot.run('MTI5NzIxMDQzMDA4MjY1MDEzMg.GHWjiL.ZipP1mNjkIgy35MGOFPHTHB6tjUaqGUABpzj6I')
