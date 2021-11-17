from selenium import webdriver
from selenium.webdriver import Firefox
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

import sqlite3
import requests
import time
import os
import re
import datetime as DT


path = os.path.abspath("files/")
os.environ["PATH"] += os.pathsep + path

conn = sqlite3.connect('files/dict.sqlite',check_same_thread=False)
cur = conn.cursor()
cur.execute('''
    CREATE TABLE IF NOT EXISTS "Positions"(
    'id' INTEGER,
    'tid' INTEGER,
    'ticker' TEXT,
    'size' TEXT,
    'price_en' TEXT,
    'price_mark' TEXT,
    'pnl' TEXT,
    'utime_pos' INTEGER,
    'utime_checked'  INTEGER,
    'opened' INTEGER,
    PRIMARY KEY("id" AUTOINCREMENT));'''
)
cur.execute('''
    CREATE TABLE IF NOT EXISTS "Traders"(
    'id' INTEGER,
    'name' TEXT,
    'uid' TEXT,
    PRIMARY KEY("id" AUTOINCREMENT));'''
)
cur.execute('''
    CREATE TABLE IF NOT EXISTS "Users"(
    'id' INTEGER,
    'user_id' INTEGER,
    'user_name' TEXT,
    'utime_checked' INTEGER,
    PRIMARY KEY("id" AUTOINCREMENT));'''
)
#STEP 1 GRABBING
driver = Firefox()
def grabdata_from_profile(tid):
    """With opened profile grab all other data for the trader"""
    driver.implicitly_wait(3) #seconds
    try:
        #click to 'Positions'
        elem = driver.find_element(By.ID, "tab-MYPOSITIONS")
        elem.click()
        #Check all Positions for the trader
        opened_poslist = list()
        positions = driver.find_elements(By.CLASS_NAME, "rc-table-row")
        for pos in positions:
            infos = pos.find_elements(By.TAG_NAME, "div")
            ticker = infos[0].text
            size = infos[1].text
            price_en = infos[2].text
            price_mark = infos[3].text

            str = infos[4].text
            pnl = str#fix it with re

            dt = DT.datetime.strptime(infos[6].text, '%Y-%m-%d %H:%M:%S')
            utime_pos = int(dt.timestamp())
            cur.execute('SELECT id FROM Positions WHERE utime_pos = ? ',(utime_pos,))
            opened_poslist.append(utime_pos)

            utime_checked = int(time.time())

            row = cur.fetchone()
            if row is None:
                cur.execute('INSERT INTO Positions (ticker, tid, size, price_en, price_mark, pnl, utime_pos, utime_checked, opened) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (ticker, tid,size, price_en, price_mark, pnl, utime_pos, utime_checked, 1))
                cur.execute('SELECT id FROM Positions WHERE utime_pos = ? ', (utime_pos, ))
                id = cur.fetchone()[0]
                print("ticker",ticker,"\nsize",size,"\nprice_en",price_en,"\nprice_mark",price_mark,"\npnl",pnl,"\ntime",utime_pos)
                print("...")
                print("newpair was added with id = ",id)
            else:
                id = row[0]
                cur.execute('UPDATE Positions SET price_en = ? , price_mark = ? WHERE utime_pos = ?',(price_en,price_mark,utime_pos))
                conn.commit()
                print("id", id , " was updated with ",price_en,price_mark)
            conn.commit()
        #When Positions is finished check Positions for open or close

        cur.execute('SELECT id, utime_pos FROM Positions WHERE tid = ? and opened = 1',(tid,))
        rows = cur.fetchall()
        for row in rows:
            id, utime_pos = row
            if utime_pos not in opened_poslist:
                print("ПОЗИЦИЯ с ID",id,"закрыта")
                cur.execute('UPDATE Positions SET opened = ? , utime_checked = ? WHERE id = ?',(0, utime_checked, id))
                conn.commit()

    except:
        pass

while True:
    with open('links.txt', 'r', encoding='utf-8') as file:
        for line in file:
            url = line.rstrip()
            #def openprofile()
            """Open a trader profile grab the name write it to database if not exists"""
            driver.get(url)
            res = re.search(r"([\w]*)$", url)
            uid = res[1]
            time.sleep(3)
            player = driver.find_element(By.CLASS_NAME, "css-1kmpww2")
            name = player.text
            if len(name) < 3:#Skip traders with nick '--'
                print("error with name for url",url)
            else:
                print(name,len(name))

                cur.execute('SELECT id FROM Traders WHERE name = ? ',(name,))
                row = cur.fetchone()
                if row is None:
                    cur.execute('INSERT INTO Traders (name, uid) VALUES (?, ?)', (name,uid))
                    cur.execute('SELECT id FROM Traders WHERE name = ? ', (name, ))
                    tid = cur.fetchone()[0]
                    print("new trader",name," with id: has been added",tid)
                else:
                    tid = row[0]
                    print("trader",name,"already in database with id: ",tid)
                conn.commit()
                grabdata_from_profile(tid)
