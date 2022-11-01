# coding=utf-8
""" collection of Page endpoints """
import calendar
import datetime as dt
from datetime import datetime
import glob
import logging
import os
import shutil
import os.path
from os import path
import resource
import socket
import subprocess
import sys
import time
import json
import sqlite3
from sqlite3 import Error
from zipfile import ZipFile
from os.path import basename
from collections import OrderedDict
from importlib import import_module

import flask_login
from flask import current_app
from flask import flash
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import send_file
from flask import url_for
from flask.blueprints import Blueprint
from flask_babel import gettext
from sqlalchemy import and_

from mycodo.config import ALEMBIC_VERSION
from mycodo.config import BACKUP_LOG_FILE
from mycodo.config import CAMERA_INFO
from mycodo.config import DAEMON_LOG_FILE
from mycodo.config import DAEMON_PID_FILE
from mycodo.config import DEPENDENCY_LOG_FILE
from mycodo.config import FRONTEND_PID_FILE
from mycodo.config import HTTP_ACCESS_LOG_FILE
from mycodo.config import HTTP_ERROR_LOG_FILE
from mycodo.config import KEEPUP_LOG_FILE
from mycodo.config import LCD_INFO
from mycodo.config import LOGIN_LOG_FILE
from mycodo.config import MYCODO_VERSION
from mycodo.config import RESTORE_LOG_FILE
from mycodo.config import THEMES_DARK
from mycodo.config import UPGRADE_LOG_FILE
from mycodo.config import USAGE_REPORTS_PATH
from mycodo.config import SQL_DATABASE_MYCODO
from mycodo.config import RECIPES_PATH
from mycodo.config import RECIPES_ICONS
from mycodo.config import SCHEDULE_WEEKS
from mycodo.config import TEMP_PATH
from mycodo.config import PATH_FUNCTIONS_CUSTOM
from mycodo.config_devices_units import MEASUREMENTS
from mycodo.databases.models import AlembicVersion
from mycodo.databases.models import Camera
from mycodo.databases.models import Conversion
from mycodo.databases.models import CustomController
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import DisplayOrder
from mycodo.databases.models import EnergyUsage
from mycodo.databases.models import Input
from mycodo.databases.models import LCD
from mycodo.databases.models import LCDData
from mycodo.databases.models import Math
from mycodo.databases.models import Measurement
from mycodo.databases.models import Misc
from mycodo.databases.models import NoteTags
from mycodo.databases.models import Notes
from mycodo.databases.models import Output
from mycodo.databases.models import OutputChannel
from mycodo.databases.models import PID
from mycodo.databases.models import Unit
from mycodo.databases.models import Widget
from mycodo.databases.models import Method
from mycodo.databases.models import MethodData
from mycodo.databases.models import Recipes
from mycodo.databases.models import Saved_Input
from mycodo.databases.models import Saved_Output
from mycodo.databases.models import Saved_Function
from mycodo.databases.models import Saved_Controller
from mycodo.databases.models import InputSchema
from mycodo.databases.models import OutputSchema
from mycodo.databases.models import FunctionSchema
from mycodo.databases.models import SavedOutputSchema
from mycodo.devices.camera import camera_record
from mycodo.mycodo_client import DaemonControl
from mycodo.mycodo_client import daemon_active
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.extensions import ma
from mycodo.mycodo_flask.forms import forms_camera
from mycodo.mycodo_flask.forms import forms_lcd
from mycodo.mycodo_flask.forms import forms_misc
from mycodo.mycodo_flask.forms import forms_notes
from mycodo.mycodo_flask.forms import forms_output
from mycodo.mycodo_flask.routes_static import inject_variables
from mycodo.mycodo_flask.utils import utils_camera
from mycodo.mycodo_flask.utils import utils_dashboard
from mycodo.mycodo_flask.utils import utils_export
from mycodo.mycodo_flask.utils import utils_general
from mycodo.mycodo_flask.utils import utils_lcd
from mycodo.mycodo_flask.utils import utils_misc
from mycodo.mycodo_flask.utils import utils_notes
from mycodo.mycodo_flask.utils import utils_recipe
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.functions import parse_function_information
from mycodo.utils.inputs import list_analog_to_digital_converters
from mycodo.utils.inputs import parse_input_information
from mycodo.utils.outputs import output_types
from mycodo.utils.outputs import parse_output_information
from mycodo.utils.system_pi import add_custom_measurements
from mycodo.utils.system_pi import add_custom_units
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import parse_custom_option_values
from mycodo.utils.system_pi import parse_custom_option_values_output_channels_json
from mycodo.utils.system_pi import return_measurement_info
from mycodo.utils.tools import calc_energy_usage
from mycodo.utils.tools import return_energy_usage
from mycodo.utils.tools import return_output_usage
from mycodo.databases.models import DisplayOrder
from mycodo.mycodo_flask.extensions import db
from mycodo.mycodo_flask.utils.utils_general import add_display_order
from mycodo.mycodo_flask.utils.utils_general import delete_entry_with_id
from mycodo.mycodo_flask.utils.utils_general import flash_success_errors
from mycodo.mycodo_flask.utils.utils_general import return_dependencies
from mycodo.utils.system_pi import csv_to_list_of_str
from mycodo.utils.system_pi import list_to_csv

logger = logging.getLogger('mycodo.mycodo_flask.routes_recipe')

blueprint = Blueprint('routes_recipe',
                      __name__,
                      static_folder='../static',
                      template_folder='../templates')


@blueprint.context_processor
@flask_login.login_required
def inject_dictionary():
    return inject_variables()

@blueprint.route('/current_recipe')
@flask_login.login_required
def page_current_recipe():
    function = CustomController.query.all()
    device_measurements = DeviceMeasurements.query.all()
    input_dev = Input.query.all()
    output = Output.query.all()
    math = Math.query.all()
    scheduler = CustomController.query.filter(CustomController.device == 'Scheduler').all()
    start_date = None
    end_date = None
    recipe_id = ''
    weeks = []
    data = []
    form_mod_output = forms_output.OutputMod()
    recipes = Recipes.query.all()
    
    current_recipe = Recipes.query.filter(Recipes.current == True).first()
    if(not current_recipe):
       if utils_general.user_has_permission('edit_controllers'):
            recipe_data = Recipes(current = True)
            db.session.add(recipe_data)
            db.session.commit()
            current_recipe = Recipes.query.filter(Recipes.current == True).first()
            recipe_id = current_recipe.recipe_id
            start_date =  current_recipe.start_date
            end_date = current_recipe.end_date
    # else:
    #     if utils_general.user_has_permission('edit_controllers'):
    #         current_recipe = Recipes.query.filter(Recipes.current == True).first()
    #         recipe_id = current_recipe.recipe_id
    #         recipe_data = {"recipe_id" : recipe_id}
    #         db.session.query(Recipes).update(recipe_data)
    #         db.session.commit()

    for schedule in scheduler:
        weeks_ = list(json.loads(schedule.custom_options).keys())[2:]
        data_ = list(json.loads(schedule.custom_options).values())[2:]
        data_.insert(0,schedule.name)
        if(len(weeks_) > len(weeks)):
            weeks = list(weeks_)
        data.append(data_)

    image = "/img/button-green.png"
    return render_template('pages/current_recipe.html',image = image,recipe = current_recipe,recipe_id = recipe_id,start_date = start_date,end_date = end_date,inputs = input_dev,outputs = output ,functions = function,schedules = scheduler ,weeks = weeks ,data = data,form_mod_output=form_mod_output)

def get_saved_recipes():
    recipes = Recipes.query.all()
    inputs = Saved_Input.query.all()
    outputs = Saved_Output.query.all()
    functions = Saved_Function.query.all()
    scheduler = Saved_Function.query.filter(Saved_Function.device == 'Scheduler').all()

    weeks = []
    data = []
    for schedule in scheduler:
        weeks_ = list(json.loads(schedule.custom_options).keys())[2:]
        data_ = list(json.loads(schedule.custom_options).values())[2:]
        data_.insert(0,schedule.recipe_id)
        data_.insert(1,schedule.name)
        if(len(weeks_) > len(weeks)):
            weeks = list(weeks_)
        data.append(data_)
    
    return render_template('pages/saved_recipes.html',recipes = recipes,inputs = inputs,outputs = outputs,functions = functions,schedules = scheduler,weeks = weeks,data = data)

@blueprint.route('/saved_recipes')
@flask_login.login_required
def page_saved_recipes():
    return get_saved_recipes()

def save_current(recipe_id):
    function = CustomController.query.all()
    device_measurements = DeviceMeasurements.query.all()
    input_dev = Input.query.all()
    output = Output.query.all()
    math = Math.query.all()
    scheduler = CustomController.query.filter(CustomController.device == 'Scheduler').all()
    recipes = Recipes.query.all()
    
    if utils_general.user_has_permission('edit_controllers'):
        input_schema = InputSchema(many=True)
        output_schema = SavedOutputSchema(many=True)
        function_schema = FunctionSchema(many=True)

        inputs = input_schema.dump(input_dev)
        outputs = output_schema.dump(output)
        functions = function_schema.dump(function)
      
        id = {"recipe_id": recipe_id}
        if(inputs):
            db.session.query(Saved_Input).filter(Saved_Input.recipe_id == recipe_id).delete()
            db.session.commit()
            for each_input in inputs:
                each_input.pop('id',None)
                each_input.update(id)
                input_data = Saved_Input(**each_input)
                try:
                    db.session.add(input_data)
                    db.session.commit()
                except:
                    pass
      
        if(outputs):
            db.session.query(Saved_Output).filter(Saved_Output.recipe_id == recipe_id).delete()
            db.session.commit()
            for each_output in outputs:
                each_output.pop('id',None)
                each_output.update(id)
                output_data = Saved_Output(**each_output)
                try:
                    db.session.add(output_data)
                    db.session.commit()
                except:
                    pass

        if(functions):
            db.session.query(Saved_Function).filter(Saved_Function.recipe_id == recipe_id).delete()
            db.session.commit()
            for each_function in functions:
                each_function.pop('id',None)
                each_function.update(id)
                function_data = Saved_Function(**each_function)
                try:
                    db.session.add(function_data)
                    db.session.commit()
                except Exception as e:
                    pass

        # recipe_data = {"recipe_id" : recipe_id}
        # db.session.query(Recipes).update(recipe_data)
        # db.session.commit()
        src_db = SQL_DATABASE_MYCODO
        dest_db = os.path.join(RECIPES_PATH,recipe_id+'.db')

        if path.isfile(dest_db):
            os.remove(dest_db)
            shutil.copy(src_db,dest_db) #copy the file to destination dir
        else:
            shutil.copy(src_db,dest_db) #copy the file to destination dir
        return "success"
    else:
         return "failed"

@blueprint.route('/save_current_recipe', methods=['POST'])
def save_current_recipe():
    """Save positions recipes"""
    recipe_id=None
    recipe_id=request.json['recipe_id']
    action=request.json['action']

    return save_current(recipe_id)

ALLOWED_EXTENSIONS = ['zip', 'rar']
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS
def read_database_summary(file):
    summary_file = os.path.join(TEMP_PATH,'summary.txt')
    customs_path = os.path.join(TEMP_PATH,'custom_functions')
    recipe_id = ""
    recipe = {}
    inputs = {}
    outputs = {}
    functions = {}
    schedules = {}

    db_path = None

    if path.isfile(file):
        with ZipFile(file, 'r') as zip:
            if not path.isdir(TEMP_PATH):
                os.mkdir(TEMP_PATH)
            zip.extractall(TEMP_PATH)

    if path.isdir(TEMP_PATH):
        if path.isdir(customs_path):
            for filename in os.listdir(customs_path):
                if not path.isfile(os.path.join(PATH_FUNCTIONS_CUSTOM,filename)):
                    shutil.copy(os.path.join(customs_path,filename),PATH_FUNCTIONS_CUSTOM) 
        if path.isfile(summary_file): 
            with open(summary_file,"r") as f:
                json_data = json.load(f)
                recipe = json_data["recipe"]
        try:
            recipe_id = recipe["recipe_id"]
        except:
            pass

        if(recipe_id):
            for filename in os.listdir(TEMP_PATH):
                if filename.endswith(".db"):
                    db_path = os.path.join(TEMP_PATH,filename)
                    inputs,outputs,functions = utils_recipe.get_summary(db_path)
                    new_db = os.path.join(RECIPES_PATH,recipe_id+'.db')
                    shutil.copy(db_path,new_db)

        
            if not path.isdir(RECIPES_ICONS):
                os.mkdir(RECIPES_ICONS)
            accepted_image = ['png','jpg','jpeg']
            for filename in os.listdir(TEMP_PATH):
                for suffix in accepted_image:
                    if filename.endswith(suffix):
                        icon_path = os.path.join(RECIPES_ICONS,recipe_id+'.'+suffix)
                        shutil.copy(os.path.join(TEMP_PATH,filename),icon_path) 
                        if recipe["icon"] != recipe_id+'.'+suffix: 
                            recipe["icon"] = recipe_id+'.'+suffix
                                  
    try:
        shutil.rmtree(TEMP_PATH)
    except OSError as e:
        pass
    return recipe,inputs,outputs,functions


@blueprint.route('/import_recipe', methods=['POST'])
def import_recipe():
    """Saved recipes"""
    recipes = Recipes.query.all()
    inputs = Saved_Input.query.all()
    outputs = Saved_Output.query.all()
    functions = Saved_Function.query.all()
    scheduler = Saved_Function.query.filter(Saved_Function.device == 'Scheduler').all()
    weeks = []
    data = []

    for schedule in scheduler:
        weeks_ = list(json.loads(schedule.custom_options).keys())[2:]
        data_ = list(json.loads(schedule.custom_options).values())[2:]
        data_.insert(0,schedule.recipe_id)
        data_.insert(1,schedule.name)
        if(len(weeks_) > len(weeks)):
            weeks = list(weeks_)
        data.append(data_)
   
    """Imported recipe"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return render_template('pages/saved_recipes.html',recipes = recipes,inputs = inputs,outputs = outputs,functions = functions,schedules = scheduler,weeks = weeks,data = data)

        uploaded_file = request.files['file']
        if uploaded_file == '':
            flash('No selected file')
            return render_template('pages/saved_recipes.html',recipes = recipes,inputs = inputs,outputs = outputs,functions = functions,schedules = scheduler,weeks = weeks,data = data)
       
        if uploaded_file and allowed_file(uploaded_file.filename):
            filepath = os.path.join(TEMP_PATH,uploaded_file.filename)
            if not path.isdir(TEMP_PATH):
                os.mkdir(TEMP_PATH)
            if not path.isfile(filepath):
                uploaded_file.save(filepath)

            recipe,_inputs,_outputs,_functions = read_database_summary(filepath)
            recipe_id =  recipe["recipe_id"]
            recipe_icon = recipe["icon"]
            exist_recipe = Recipes.query.filter(Recipes.recipe_id == recipe_id).first()

            if not exist_recipe:
                if utils_general.user_has_permission('edit_controllers'):
                    try:
                        input_schema = InputSchema(many=True)
                        output_schema = SavedOutputSchema(many=True)
                        function_schema = FunctionSchema(many=True)

                        inputs = input_schema.dump(_inputs)
                        outputs = output_schema.dump(_outputs)
                        functions = function_schema.dump(_functions)

                        id = {"recipe_id": recipe_id}
                        if(inputs):
                            db.session.query(Saved_Input).filter(Saved_Input.recipe_id == recipe_id).delete()
                            db.session.commit()
                            for each_input in inputs:
                                each_input.pop('id',None)
                                each_input.update(id)
                                input_data = Saved_Input(**each_input)
                            
                                db.session.add(input_data)
                                db.session.commit()
                            
                    
                        if(outputs):
                            db.session.query(Saved_Output).filter(Saved_Output.recipe_id == recipe_id).delete()
                            db.session.commit()
                            for each_output in outputs:
                                each_output.pop('id',None)
                                each_output.update(id)
                                output_data = Saved_Output(**each_output)
                            
                                db.session.add(output_data)
                                db.session.commit()
                            

                        if(functions):
                            db.session.query(Saved_Function).filter(Saved_Function.recipe_id == recipe_id).delete()
                            db.session.commit()
                            for each_function in functions:
                                each_function.pop('id',None)
                                each_function.update(id)
                                function_data = Saved_Function(**each_function)
                                
                                db.session.add(function_data)
                                db.session.commit()
                        
                        recipe_data = Recipes(recipe_id = recipe_id,icon = recipe_icon)
                        db.session.add(recipe_data)
                        db.session.commit()

                    except:
                        pass

                recipes = Recipes.query.all()
                inputs = Saved_Input.query.all()
                outputs = Saved_Output.query.all()
                functions = Saved_Function.query.all()
                scheduler = Saved_Function.query.filter(Saved_Function.device == 'Scheduler').all()
                weeks = []
                data = []

                for schedule in scheduler:
                    weeks_ = list(json.loads(schedule.custom_options).keys())[2:]
                    data_ = list(json.loads(schedule.custom_options).values())[2:]
                    data_.insert(0,schedule.recipe_id)
                    data_.insert(1,schedule.name)
                    if(len(weeks_) > len(weeks)):
                        weeks = list(weeks_)
                    data.append(data_)
            return render_template('pages/saved_recipes.html',recipes = recipes,inputs = inputs,outputs = outputs,functions = functions,schedules = scheduler,weeks = weeks,data = data)
            
    return render_template('pages/saved_recipes.html',recipes = recipes,inputs = inputs,outputs = outputs,functions = functions,schedules = scheduler,weeks = weeks,data = data)

def get_all_file_paths(directory):
    file_paths = []
    # crawling through directory and subdirectories
    for root, directories, files in os.walk(directory):
        for filename in files:
            # join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)
    return file_paths   

def get_dict_object(object_data):
    data = []
    for each_data in object_data:
        each_data.pop('id',None)
        data.append(each_data)
    return data

@blueprint.route('/export_recipe', methods=['POST','GET'])
def export_recipe():
    recipe_id=None
    # recipe_id=request.json['recipe_id']
    # action=request.json['action']
    recipe_id = request.args.get('recipe_id')
    recipe_icon = request.args.get('recipe_icon')
    icon_path = os.path.join(RECIPES_ICONS,recipe_icon) 
    _inputs = Saved_Input.query.filter(Saved_Input.recipe_id == recipe_id).all()
    _outputs = Saved_Output.query.filter(Saved_Output.recipe_id == recipe_id).all()
    _functions = Saved_Function.query.filter(Saved_Function.recipe_id == recipe_id).all()
    _scheduler = Saved_Function.query.filter(Saved_Function.device == 'Scheduler').filter(Saved_Input.recipe_id == recipe_id).all()
    
    input_schema = InputSchema(many=True)
    output_schema = SavedOutputSchema(many=True)
    function_schema = FunctionSchema(many=True)

    if path.isdir(TEMP_PATH):                           
        try:
            shutil.rmtree(TEMP_PATH)
            os.mkdir(TEMP_PATH)
        except OSError as e:
            pass 
    else:
        os.mkdir(TEMP_PATH)
    
    if path.isdir(TEMP_PATH): 
        _recipe = {"recipe_id" : recipe_id,"icon": recipe_icon}
        _input = input_schema.dump(_inputs)
        _output = output_schema.dump(_outputs)
        _function = function_schema.dump(_functions)
        _schedule = function_schema.dump(_scheduler)

        data = {
            "recipe" : _recipe,
            "inputs" : get_dict_object(_input),
            "outputs" : get_dict_object(_output),
            "functions" : get_dict_object(_function),
            "schedules" : get_dict_object(_schedule)
        }
        sum_path = os.path.join(TEMP_PATH,"summary.txt")
        db_path = os.path.join(RECIPES_PATH,recipe_id+'.db')
        if path.isfile(db_path):
            with open(sum_path,'w+') as f:
                json.dump(data,f)

            shutil.copy(db_path,os.path.join(TEMP_PATH,recipe_id+'.db'))
            file_paths = get_all_file_paths(TEMP_PATH)
            zip_file = os.path.join(TEMP_PATH,recipe_id+'.zip')
            with ZipFile(zip_file,'w') as zip:
                for file in file_paths:
                    zip.write(file,basename(file))
                zip.write(icon_path,basename(icon_path))

            if path.isfile(zip_file):
                return send_file(zip_file, as_attachment=True)
                #return "success"
            return "failed"
    return "failed"

@blueprint.route('/use_recipe', methods=['POST','GET'])
def use_recipe():
    recipe_id = request.args.get('recipe_id')

    current_recipe = Recipes.query.filter(Recipes.current == True).first()
    old_recipe_id  = current_recipe.recipe_id
    save_current(old_recipe_id)

    #copy recipe_to mycodo
    #set recipe to current
    utils_recipe.dump_database(recipe_id)
    # time.sleep(5)
    return get_saved_recipes()

ALLOWED_IMAGES = ['png', 'jpeg' ,'jpg']
def allowed_image(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_IMAGES 


@blueprint.route('/toggleactive_recipe', methods=['POST','GET'])
def toggleactive_recipe():
    recipe_id = request.json['recipe_id']
    action = request.json['action']

    logger.info("Activating Recipe id : {}  action : {}".format(recipe_id,action))

    recipes = Recipes.query.all()
    inputs = Saved_Input.query.all()
    outputs = Saved_Output.query.all()
    functions = Saved_Function.query.all()
    scheduler = Saved_Function.query.filter(Saved_Function.device == 'Scheduler').all()
    weeks = []
    data = []

    for schedule in scheduler:
        weeks_ = list(json.loads(schedule.custom_options).keys())[2:]
        data_ = list(json.loads(schedule.custom_options).values())[2:]
        data_.insert(0,schedule.recipe_id)
        data_.insert(1,schedule.name)
        if(len(weeks_) > len(weeks)):
            weeks = list(weeks_)
        data.append(data_)

    enabled = False
    if(action == "Activate"):
        enabled = True
    else:
        enabled = False

    db.session.query(Recipes).filter(Recipes.recipe_id == recipe_id).\
    update({"enabled":enabled})
    db.session.commit()

    controllers = CustomController.query.filter().all()
    for _function in controllers:
        db.session.query(CustomController).filter(CustomController.unique_id == _function.unique_id).\
        update({"is_activated":enabled})
        db.session.commit()
       
    return render_template('pages/saved_recipes.html',recipes = recipes,inputs = inputs,outputs = outputs,functions = functions,schedules = scheduler,weeks = weeks,data = data)

def update_weekly_methods(start_date,end_date):
    try:
        #current_recipe = Recipes.query.filter(Recipes.current == True).first()
        weekly_methods = Method.query.filter(Method.method_type == 'Weekly').all()
        _end = None
        week_dates = {}
        
        weeks = (end_date - start_date).days//7
        for week in range(weeks):
            _start = start_date + dt.timedelta(days=7*week, hours=0)
            _end = _start + dt.timedelta(days=7, hours=0)
            week_dates[week] = {"start" : _start,"end" : _end}
           
        other_days = (end_date - _end).days
        if other_days > 0:
            _start = _end
            _end = end_date
            week_dates[weeks + 1] = {"start" : _start,"end" : _end}

        for _method in weekly_methods:
            method_data = MethodData.query.filter(MethodData.method_id == _method.unique_id).all()
            id = 0
            for _method_data in method_data:
                if id in week_dates.keys():
                    _method_data.time_start =  week_dates[id]["start"]
                    _method_data.time_end = week_dates[id]["end"]
                    db.session.commit()

                else:
                    delete_entry_with_id(
                        MethodData,_method_data.unique_id)
                    method_order = Method.query.filter(
                        Method.unique_id == _method.unique_id).first()
                    display_order = csv_to_list_of_str(method_order.method_order)
                    display_order.remove(_method_data.unique_id)
                    method_order.method_order = list_to_csv(display_order)
                    db.session.commit()
                    
                id += 1
            
            if(len(week_dates) > id):
                for _id in range(id,len(week_dates)):
                    new_method_data = MethodData()
                    new_method_data.method_id = _method.unique_id
                    new_method_data.time_start = week_dates[_id]["start"]
                    new_method_data.time_end = week_dates[_id]["end"]
                    new_method_data.setpoint_start = 10
                    new_method_data.setpoint_end = 10
                    
                    db.session.add(new_method_data)
                    db.session.commit()

                    display_order = csv_to_list_of_str(_method.method_order)
                    method = Method.query.filter(
                        Method.unique_id == _method.unique_id).first()
                    method.method_order = add_display_order(
                        display_order, new_method_data.unique_id)
                    db.session.commit()
        return True

    except Exception as except_msg:
        logger.info(except_msg)
        return False

def update_scheduler():
    try:
        scheduler = CustomController.query.filter(CustomController.device == 'Scheduler').all()
        logger.info("Updating Scheduler")
        _spraydata = {}
        for wk in range(1,SCHEDULE_WEEKS+1):
            week_spray = {"week_{}".format(wk) : False}
            _spraydata.update(week_spray)
      
        for schedule in scheduler:
            _custom = json.loads(schedule.custom_options)
            _custom["sprayed"] = _spraydata

            db.session.query(CustomController).filter(CustomController.unique_id == schedule.unique_id).\
            update({"custom_options":json.dumps(_custom)})
            db.session.commit()

    except Exception as ex:
        logger.info("Error resetting schedule sprayed {}".format(ex))


@blueprint.route('/change_settings', methods=['POST','GET'])
def change_settings():
    recipe_id = request.form.get('recipe_id')
    recipe_name = request.form.get('recipe_name')
    start_date = request.form.get('recipe_start')
    end_date = request.form.get('recipe_end')

    current_recipe = Recipes.query.filter(Recipes.recipe_id == recipe_id).first()
    recipe_icon = current_recipe.icon
    
    recipes = Recipes.query.all()
    inputs = Saved_Input.query.all()
    outputs = Saved_Output.query.all()
    functions = Saved_Function.query.all()
    scheduler = Saved_Function.query.filter(Saved_Function.device == 'Scheduler').all()
    weeks = []
    data = []

    for schedule in scheduler:
        weeks_ = list(json.loads(schedule.custom_options).keys())[2:]
        data_ = list(json.loads(schedule.custom_options).values())[2:]
        data_.insert(0,schedule.recipe_id)
        data_.insert(1,schedule.name)
        if(len(weeks_) > len(weeks)):
            weeks = list(weeks_)
        data.append(data_)

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return render_template('pages/saved_recipes.html',recipes = recipes,inputs = inputs,outputs = outputs,functions = functions,schedules = scheduler,weeks = weeks,data = data)

        uploaded_file = request.files['file']
        if uploaded_file == '':
            flash('No selected file')
            return render_template('pages/saved_recipes.html',recipes = recipes,inputs = inputs,outputs = outputs,functions = functions,schedules = scheduler,weeks = weeks,data = data)
       
        if uploaded_file and allowed_image(uploaded_file.filename):
            new_icon_path = ""
            icon_suffix = ""
            accepted_image = ['png','jpg','jpeg']
            for suffix in accepted_image:
                if uploaded_file.filename.endswith(suffix):
                    icon_suffix = suffix
                    new_icon_path = os.path.join(RECIPES_ICONS,recipe_id+'.'+suffix)
            
            icon_path = os.path.join(RECIPES_ICONS,recipe_icon)
            filepath = os.path.join(RECIPES_ICONS,uploaded_file.filename)
            if path.isfile(icon_path) and recipe_icon != "default.png":
                os.remove(icon_path) 
            
            uploaded_file.save(filepath)
            if new_icon_path:
                shutil.move(filepath,new_icon_path)
                db.session.query(Recipes).filter(Recipes.recipe_id == recipe_id).\
                update({"icon": recipe_id+"."+icon_suffix})
                db.session.commit()

        if recipe_name:
            try:
                db.session.query(Recipes).filter(Recipes.recipe_id == recipe_id).\
                update({"name":recipe_name})
                db.session.commit()
            except:
                flash('Wrong date format')
        if(start_date or end_date):
            if start_date:
                try:
                    _start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
                    db.session.query(Recipes).filter(Recipes.recipe_id == recipe_id).\
                    update({"start_date":_start_date})
                    db.session.commit()
                
                except:
                    flash('Wrong date format')
            if end_date:
                try:
                    _end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')
                    db.session.query(Recipes).filter(Recipes.recipe_id == recipe_id).\
                    update({"end_date":_end_date})
                    db.session.commit()
                except:
                    flash('Wrong date format')

            current_recipe = Recipes.query.filter(Recipes.recipe_id == recipe_id).first()
            response = update_weekly_methods(current_recipe.start_date,current_recipe.end_date)
            update_scheduler()
           
    return render_template('pages/saved_recipes.html',recipes = recipes,inputs = inputs,outputs = outputs,functions = functions,schedules = scheduler,weeks = weeks,data = data)

@blueprint.route('/activate_recipe', methods=['POST','GET'])
def activate_recipe():
    recipe_id = request.form.get('recipe_id')
    recipe_activate = request.form.get('recipe_activate')