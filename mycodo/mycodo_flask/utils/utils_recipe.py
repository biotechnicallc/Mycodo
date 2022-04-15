import sqlite3
from sqlite3 import Error
import json  
import uuid
import time
import os
import os.path
from os import path
import shutil
import subprocess

from mycodo.config import RECIPES_PATH
from mycodo.config import DATABASE_PATH

# file_path = os.path.realpath(__file__)
# database_path = str(os.path.split(file_path)[0]) + "/databases"

def get_summary(db):
    inputs = []
    outputs = []
    functions = []
    # db_path = os.path.join(database_path,db)
    db_path = os.path.join(RECIPES_PATH,db)
    print(db_path)
    if os.path.isfile(db_path):
        print("file found")
        con = sqlite3.connect(db_path ,check_same_thread=False)
        with con as conn:
            cursorObj = conn.cursor()
            cursorObj.execute("SELECT * FROM input")
            result = cursorObj.fetchall()  
            if(result):
                for _input in result:
                    data = dict(zip([c[0] for c in cursorObj.description],_input))
                    print(data)
                    inputs.append(data)

            cursorObj.execute("SELECT * FROM output")
            result = cursorObj.fetchall()  
            if(result):
                for _output in result:
                    data = dict(zip([c[0] for c in cursorObj.description],_output))
                    print(data)
                    outputs.append(data)


            cursorObj.execute("SELECT * FROM custom_controller")
            result = cursorObj.fetchall()  
            if(result):
                for _function in result:
                    data = dict(zip([c[0] for c in cursorObj.description],_function))
                    print(data)
                    functions.append(data)
                
    return inputs,outputs,functions

def dump_database(recipe_id):
    try:
        mycodo_db_path = os.path.join(DATABASE_PATH,"mycodo.db")
        backup_db_path = os.path.join(DATABASE_PATH,"mycodo_backup.db")
        set_db_path = os.path.join(RECIPES_PATH,recipe_id+'.db')

        #clean some tables in set database
        con = sqlite3.connect(set_db_path ,check_same_thread=False)
        with con as conn:
            cursorObj = conn.cursor()
            cursorObj.execute('ATTACH DATABASE "{}" AS old_db'.format(mycodo_db_path))

            cursorObj.execute("DELETE FROM users")
            con.commit()
            cursorObj.execute("DELETE FROM recipes")
            con.commit()
            cursorObj.execute("DELETE FROM saved_output")
            con.commit()
            cursorObj.execute("DELETE FROM saved_input")
            con.commit()
            cursorObj.execute("DELETE FROM saved_function")
            con.commit()
            
            #insert
            cursorObj.execute("INSERT INTO users SELECT * FROM old_db.users")
            con.commit()
            cursorObj.execute("INSERT INTO recipes SELECT * FROM old_db.recipes")
            con.commit()
            cursorObj.execute("INSERT INTO saved_output SELECT * FROM old_db.saved_output")
            con.commit()
            cursorObj.execute("INSERT INTO saved_input SELECT * FROM old_db.saved_input")
            con.commit()
            cursorObj.execute("INSERT INTO saved_function SELECT * FROM old_db.saved_function")
            con.commit()   

            cursorObj.execute("UPDATE recipes SET current = False")
            con.commit()
            cursorObj.execute("UPDATE recipes SET current = True WHERE recipe_id = '{}'".format(recipe_id))
            con.commit()
            
        shutil.move(mycodo_db_path,backup_db_path) 
        shutil.copy(set_db_path,mycodo_db_path) 
        return "success"

    except:
        os.rmdir(mycodo_db_path) 
        shutil.move(backup_db_path,mycodo_db_path) 
        return "failed"


