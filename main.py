import os
import threading

from flask import Flask, render_template
from flask_socketio import SocketIO
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.ImageHelpers import PILHelper

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")
margin = 15
margins = [margin, margin, margin, margin]
ball_font = ImageFont.truetype(os.path.join(os.environ['WINDIR'],'fonts','arialbd.ttf'), 100)
number_font = ImageFont.truetype(os.path.join(os.environ['WINDIR'],'fonts','arialbd.ttf'), 40)
text_font = ImageFont.truetype(os.path.join(os.environ['WINDIR'],'fonts','arialbd.ttf'), 15)
players = [
    'Team 1',
    'Team 2',
    'Team 3',
    'Team 4',
    'Team 5',
    'Team 6',
    'Team 7',
    'Team 8',
    'Team 9'
]
rounds = [
    'Round 1',
    'Round 2',
    'Round 3',
    'Semi-Finals',
    'Finals'
]
current_round = rounds[0]

def clear_keys(deck):
    image = PILHelper.to_native_format(deck, Image.new('RGB', (72, 72)))
    for key in range(deck.KEY_COUNT):
        deck.set_key_image(key, image)

def generate_blank_thumbnail():
    return PILHelper.to_native_format(deck, Image.new('RGB', (72, 72)))

def generate_number_thumnail(deck, number):
    text = str(number)
    image = Image.new('RGB', (72, 72))
    draw = ImageDraw.Draw(image)
    w, h = draw.textsize(text, font=number_font)
    draw.text(((72-w)/2,(72-h)/2), text, fill="white", font=number_font)
    return PILHelper.to_native_format(deck, PILHelper.create_scaled_image(deck,image))

def generate_ball_thumbnail(deck, has_ball):
    text = '•' if has_ball else '◦'
    image = Image.new('RGB', (72, 72))
    draw = ImageDraw.Draw(image)
    w, h = draw.textsize(text, font=ball_font)
    draw.text(((72-w)/2,(72-h)/2-h/12), text, fill="white", font=ball_font)
    return PILHelper.to_native_format(deck, PILHelper.create_scaled_image(deck,image))

def generate_player_thumbnail(deck, text):
    text = text.replace(' & ', '\n')
    image = Image.new('RGB', (72, 72))
    draw = ImageDraw.Draw(image)
    w, h = draw.textsize(text, font=text_font)
    draw.text(((72-w)/2,(72-h)/2), text, fill="white", font=text_font)
    return PILHelper.to_native_format(deck, PILHelper.create_scaled_image(deck,image))

def generate_round_thumbnail(deck, text):
    text = text.replace('-', '\n')
    image = Image.new('RGB', (72, 72))
    draw = ImageDraw.Draw(image)
    w, h = draw.textsize(text, font=text_font)
    draw.text(((72-w)/2,(72-h)/2), text, fill="white", font=text_font)
    return PILHelper.to_native_format(deck, PILHelper.create_scaled_image(deck,image))

def draw_main(deck):
    up_arrow = PILHelper.create_scaled_image(deck, Image.open(os.path.join('images', 'arrow.png')), margins=margins)
    down_arrow = up_arrow.transpose(Image.FLIP_TOP_BOTTOM)
    up_arrow_bytes = PILHelper.to_native_format(deck, up_arrow)
    down_arrow_bytes = PILHelper.to_native_format(deck, down_arrow)
    flip_arrows = PILHelper.create_scaled_image(deck, Image.open(os.path.join('images', 'flip arrows.png')), margins=margins)
    flip_arrows_bytes = PILHelper.to_native_format(deck, flip_arrows)
    new = PILHelper.create_scaled_image(deck, Image.open(os.path.join('images', 'new.png')), margins=margins)
    new_bytes = PILHelper.to_native_format(deck, new)
    for key in range(deck.KEY_COUNT):
        if key == 0:
            deck.set_key_image(0, up_arrow_bytes)
        elif key == 2:
            deck.set_key_image(key, generate_round_thumbnail(deck, current_round))
        elif key == 4:
            deck.set_key_image(key, up_arrow_bytes)
        elif key == 5:
            deck.set_key_image(key, generate_number_thumnail(deck, scores['player 1 score']))
        elif key == 6:
            deck.set_key_image(key, generate_player_thumbnail(deck, scores['player 1']))
        elif key == 7:
            deck.set_key_image(key, flip_arrows_bytes)
        elif key == 8:
            deck.set_key_image(key, generate_player_thumbnail(deck, scores['player 2']))
        elif key == 9:
            deck.set_key_image(key, generate_number_thumnail(deck, scores['player 2 score']))
        elif key == 10:
            deck.set_key_image(key, down_arrow_bytes)
        elif key == 11:
            deck.set_key_image(key, generate_ball_thumbnail(deck, scores['player 1 ball']))
        elif key == 12:
            deck.set_key_image(key, new_bytes)
        elif key == 13:
            deck.set_key_image(key, generate_ball_thumbnail(deck, scores['player 2 ball']))
        elif key == 14:
            deck.set_key_image(key, down_arrow_bytes)
        else:
            deck.set_key_image(key, generate_blank_thumbnail())
    send_update()
    deck.set_key_callback(main_key_handler)

def main_key_handler(deck, key, pressed):
    global scores
    if pressed:
        if key == 0:
            scores['player 1 score'] += 1
            draw_main(deck)
        elif key == 2:
            draw_choose_round(deck)
        elif key == 4:
            scores['player 2 score'] += 1
            draw_main(deck)
        elif key == 6:
            draw_choose_player(deck)
            deck.set_key_callback(player_1_chooser)
        elif key == 7:
            temp_score = scores.copy()
            scores['player 1'] = temp_score['player 2']
            scores['player 1 score'] = temp_score['player 2 score']
            scores['player 2'] = temp_score['player 1']
            scores['player 2 score'] = temp_score['player 1 score']
            del temp_score
            draw_main(deck)
        elif key == 8:
            draw_choose_player(deck)
            deck.set_key_callback(player_2_chooser)
        elif key == 10:
            if scores['player 1 score'] > 0:
                scores['player 1 score'] -= 1
            draw_main(deck)
        elif key == 11:
            scores['player 1 ball'] = True
            scores['player 2 ball'] = False
            draw_main(deck)
        elif key == 12:
            reset_scores()
            draw_main(deck)
        elif key == 13:
            scores['player 1 ball'] = False
            scores['player 2 ball'] = True
            draw_main(deck)
        elif key == 14:
            if scores['player 2 score'] > 0:
                scores['player 2 score'] -= 1
            draw_main(deck)

def draw_choose_player(deck):
    clear_keys(deck)
    for number, player in enumerate(players):
        deck.set_key_image(number, generate_player_thumbnail(deck, player))
    deck.set_key_callback(player_1_chooser)

def player_1_chooser(deck, key, pressed):
    if pressed:
        if key in range(len(players)):
            global scores
            scores['player 1'] = players[key]
            draw_main(deck)

def player_2_chooser(deck, key, pressed):
    if pressed:
        if key in range(len(players)):
            global scores
            scores['player 2'] = players[key]
            draw_main(deck)

def reset_scores():
    global scores
    scores = {
        'player 1': 'Team 1',
        'player 1 ball': False,
        'player 1 score': 0,
        'player 2': 'Team 2',
        'player 2 ball': False,
        'player 2 score': 0
    }    

def draw_choose_round(deck):
    clear_keys(deck)
    for number, round in enumerate(rounds):
        deck.set_key_image(number, generate_round_thumbnail(deck, round))
    deck.set_key_callback(round_chooser)

def round_chooser(deck, key, pressed):
    if pressed:
        if key in range(len(rounds)):
            global current_round
            current_round = rounds[key]
            draw_main(deck)

@app.route("/")
def hello_world():
    return render_template('home.html')

@socketio.on('update_req')
def send_update(test=None):
    global scores
    global current_round
    socketio.emit('update',{
        'scores': scores,
        'round': current_round,
    })

if __name__ == '__main__':
    deck = DeviceManager().enumerate()[0]
    deck.open()
    deck.set_brightness(100)
    reset_scores()
    draw_main(deck)

    threading.Thread(target=socketio.run, args=(app,)).start()

    for t in threading.enumerate():
        if t is threading.currentThread():
            continue
        if t.is_alive():
            t.join()

    print