import telebot
from telebot import types

import os
import sqlite3
import urllib.request

import sys
sys.path.insert(0, r'C:\Users')#path where config.py file stores with telegram TOKEN
import config
import time

#Current Database where parser store all info
conn = sqlite3.connect('files/dict.sqlite',check_same_thread=False)
cur = conn.cursor()

bot = telebot.TeleBot(config.TOKEN)

@bot.message_handler(commands=['start'])
def welcome(message):

	markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
	item1 = types.KeyboardButton("📝О сервисе")
	item2 = types.KeyboardButton("💬Чат")
	item3 = types.KeyboardButton("📧Поддержка")
	item4 = types.KeyboardButton("Запустить парсер")

	markup.add(item1, item2, item3, item4)
	bot.send_message(message.chat.id, "Привет, {0.first_name}, Выберите действия".format(message.from_user),parse_mode='html', reply_markup=markup)

def sec_to_string(sec):
	string = ""
	hours = sec//3600
	minutes = (sec%3600)//60
	sec_remaining = (sec%3600)%60
	if hours > 0:
		string = string + str(hours) + " ч."
	if minutes > 0:
		string = string + str(minutes) + " м."
	if sec_remaining > 0:
		string = string + str(sec_remaining) + " c."
	string = string + " назад"
	return string
@bot.message_handler(content_types=['text'])
def lalala(message):
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
	if message.chat.type == 'private':

		if message.text == '📝О сервисе':
			mess = "Наш бот умеет мониторить лидеров binance, и позволяет устанавливать оповещение по их позициям в моменте их открытия и закрытия. В реальном времени бот анализирует информацию со страниц лидеров(top по PNL/ROE) трейдеров и присылает сообщение с открытием или закрытием позиции:"
			bot.send_message(message.chat.id, mess)
			cur.execute('''
			SELECT id, name
			FROM Traders''')
			infos = cur.fetchall()
			if len(infos) < 1:
				bot.send_message(message.chat.id, "на данный момент никто не отслеживается")
			else:
				mess = "```| id | trader |\n"
				for info in infos:
					id, name = info
					mess = mess +  " | " +  str(id) + " | " + name + " |\n"
				mess = mess + "```"
				bot.send_message(message.chat.id, mess, parse_mode="Markdown")
		elif message.text == '💬Чат':
			bot.send_message(message.chat.id, "Ссылка на чат")
		elif message.text == '📧Поддержка':
			bot.send_message(message.chat.id, "Ссылка на поддержку")
		elif message.text == 'Остановить парсер':
			markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
			item1 = types.KeyboardButton("📝О сервисе")
			item2 = types.KeyboardButton("💬Чат")
			item3 = types.KeyboardButton("📧Поддержка")
			item4 = types.KeyboardButton("Запустить парсер")

			markup.add(item1, item2, item3, item4)
			bot.send_message(message.chat.id, "Парсер был остановлен".format(message.from_user),parse_mode='html', reply_markup=markup)

		elif message.text == 'Запустить парсер':
			item1 = types.KeyboardButton("📝О сервисе")
			item2 = types.KeyboardButton("💬Чат")
			item3 = types.KeyboardButton("📧Поддержка")
			item4 = types.KeyboardButton("Остановить парсер")
			markup.add(item1, item2, item3, item4)
			bot.send_message(message.chat.id, "парсер запущен\nожидание новой информации...".format(message.from_user),parse_mode='html', reply_markup=markup)
			us_id = message.from_user.id
			while True:

				username = message.from_user.username
				unix_time = int(time.time())
				cur.execute('''
				SELECT id, utime_checked
				FROM Users
				WHERE user_id = ? ''',(us_id,))
				infos = cur.fetchall()
				if len(infos) < 1:
					utime_checked = 0
					cur.execute('INSERT INTO Users (user_id, user_name, utime_checked) VALUES (?, ?, ?)', (us_id,username,utime_checked))
					print("new user has beed added:",us_id,username,utime_checked)
				else:
					for info in infos:
						id, utime_checked = info
						cur.execute('UPDATE Users SET utime_checked = ?  WHERE user_id = ?',(unix_time,us_id))
						print("unixtime:",us_id,username,unix_time)
				conn.commit()

				cur.execute('''
				SELECT Positions.id, ticker, size, price_en, price_mark, pnl, utime_pos, utime_checked, name, uid, opened
				FROM Positions
				INNER JOIN Traders
				ON Traders.id = Positions.tid
				WHERE utime_checked > ? ''',(utime_checked,))
				rows = cur.fetchall()

				if len(rows) < 1:
					#bot.send_message(message.chat.id, "No info")
					time.sleep(5)
					continue
				else:
					for info in rows:
						id, ticker, size, price_en, price_mark, pnl, timedb, utime_checked, name , uid, opened = info


						if opened == 1:#check the status of the position 1 is opened and 0 is cloes
							mess = '*🎓Трейдер с ником: ' + name + '*\n' + '✅Открыл позицию \n'
							time_calc = '\nВремя: ' + sec_to_string(unix_time - timedb)
						else:
							mess = '*🎓Трейдер с ником: ' + name + '*\n' + '❌Закрыл позицию \n'
							time_calc = ''
							#time_calc = '~' + sec_to_string(unix_time - timedb)

						mess = mess + '\n*💱Валюта: ' + ticker + '*\nРазмер: ' +  size + '\nЦена входа: ' + price_en + '\nЦена маркировки: ' + price_mark + '\nPNL(ROE): ' + pnl + time_calc + '\n'
						keyboard = types.InlineKeyboardMarkup()
						urllink = "https://www.binance.com/ru/futures-activity/leaderboard?type=myProfile&tradeType=PERPETUAL&encryptedUid=" + uid
						url_button = types.InlineKeyboardButton(text="Страница трейдера", url=urllink)
						keyboard.add(url_button)
						bot.send_message(message.chat.id, mess, reply_markup=keyboard, parse_mode="Markdown")#Markdown - changes ** to bold and so on
				time.sleep(10)

		else:
			item1 = types.KeyboardButton("📝О сервисе")
			item2 = types.KeyboardButton("💬Чат")
			item3 = types.KeyboardButton("📧Поддержка")
			item4 = types.KeyboardButton("Запустить парсер")

			markup.add(item1, item2, item3, item4)
			bot.send_message(message.chat.id, "Возврат в меню, Выберите действия".format(message.from_user),
				parse_mode='html', reply_markup=markup)

# RUN
bot.polling(none_stop=True)
