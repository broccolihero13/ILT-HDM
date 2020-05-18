#!/usr/bin/python
import click
import pandas as pd
import requests
import os
import json
import dateutil.parser
import csv
from datetime import datetime, timedelta
import colorama
#note: this app is used for Live Training historical data migrations in Bridge
#it must use a CSV with the following fields (LT courses must already exist in Bridge):
# uid,live_course_id,completed_at  
# a new session will be created for each unique completed_at date (ISO 8601 format YYYY-MM-DD)

error_csv_list = []
success_csv_list = []
created_sessions = {}
base_url = ""
headers = {}

@click.command()
@click.option("--domain","-d", prompt=True, required=True, help="The domain for the bridge instance, for example use 'acme' for acme.bridgeapp.com")
@click.option("--token","-t", prompt=True, required=True, help="The API token for accessing the domain")
@click.option("--file","-f", prompt=True, required=True)
def main(domain, token, file):
    click.secho(f"Let's get started by adding historical ILT enrollments to https://{domain}.bridgeapp.com", fg="green")
    global base_url, headers 
    base_url = f"https://{domain}.bridgeapp.com/api/"
    headers = {'Authorization':token,'Content-Type':'application/json'}
    
    # Make sure we have what we need to proceed (domain is valid, file exists, timezone is set for )
    account_settings = requests.get(f"{base_url}config/sub_account", headers=headers)
    if account_settings.status_code != 200:
        raise EnvironmentError(click.style(f'ERROR: Status Code == {account_settings.status_code} This Bridge account could not be found! Check that the domain is valid!', fg="red"))

    if not os.path.isfile(file):
        raise ValueError(click.style('the file does not exist or the path is incorrect', fg="red"))
    
    try:
        timezone = account_settings.json()["sub_accounts"][0]["config"]["time_zone"]
    except:
        raise ValueError(click.style(f'Could not retrieve the timezone for your specific Bridge account, check that the URL is a valid one.',fg="red"))
    click.secho(timezone, fg="blue")
    all_possible_sessions = []

    # read, create/check unique value, and sort the CSV file
    df = pd.read_csv(file)
    
    df['uniq'] = df.uid.map(str) + "-" + df.live_course_id.map(str)
    df['uniq_course'] = df.completed_at.map(str) + "-" + df.live_course_id.map(str)
    df = df.sort_values(['uniq', 'completed_at'], ascending=[True, True])
    df.to_csv("uniq_added.csv", index=False)
    
    for index, row in df.iterrows():
        all_possible_sessions.append((row["live_course_id"], row["completed_at"]))
    uniq_sessions = set(all_possible_sessions)

    for i in uniq_sessions:
        # create and publish sessions and make a dictionary with the unique values as the keys
        if create_session(i, timezone):
            click.secho(f"Session created for {i[0]}-{i[1]}", fg="yellow")
            if publish_session(i):
                click.secho(f"Session published for {i[0]}-{i[1]}", fg="yellow")
        
    # register the users in the session
    for index, row in df.iterrows():
        register_user(row)
    # return a CSV of the successful registrations
    write_error_log(error_csv_list, domain)
    # return  a CSV for errors that occurred during this process to be reviewed by the IC
    write_return_log(success_csv_list, domain)


def create_session(tup, timezone):
    # click.echo(base_url) #for troubleshooting purposes
    d = dateutil.parser.parse(f"{tup[1]}T12:00:00")
    d_plus_60 = d + timedelta(hours=1)
    new_end = d_plus_60.isoformat()
    payload = {
        "sessions":[
            {
                "timezone":timezone,"start_at":d.isoformat(),"end_at":new_end
            }]
        }
    try:
        session_created = requests.post(f"{base_url}author/live_courses/{tup[0]}/sessions", headers=headers, data=json.dumps(payload))
        if session_created.status_code == 201:
            session_id = session_created.json()["sessions"][0]["id"]
            created_sessions[f"{tup[1]}-{tup[0]}"] = {"session_id":session_id}
            return True
        else:
            error_csv_list.append({"status_code":session_created.status_code,"message":f"The API call failed to create a session for course: {tup[0]}. Date: {tup[1]}"})
    except:
        error_csv_list.append({"status_code":"Unknown", "message":f"Something went wrong when trying to create the session for course: {tup[0]}. Date: {tup[1]}"})
    
    return False

def publish_session(tup):
    try:
        sess_id = created_sessions[f"{tup[1]}-{tup[0]}"]["session_id"]
        publish_session = requests.post(f"{base_url}author/live_courses/{tup[0]}/sessions/{sess_id}/publish", headers=headers)
        if publish_session.status_code == 200:
            created_sessions[f"{tup[1]}-{tup[0]}"]["published"] = True
            return True
        else:
            error_csv_list.append({"status_code":publish_session.status_code,"message":f"The API call failed to publish a session for course: {tup[0]}. Date: {tup[1]}"})
    except:
        error_csv_list.append({"status_code":"Unknown", "message":f"Something went wrong when trying to publish the session for uniq {tup[0]}-{tup[i]}"})
    
    return False
            
def register_user(from_row):
    try:
        id_string = from_row["uniq_course"]
        get_user = requests.get(f"{base_url}author/users/uid:{from_row['uid']}", headers=headers)
        if get_user.status_code == 200 and created_sessions[id_string]["published"]:
            get_user_id = get_user.json()["users"][0]["id"]
            id_for_session_reg = created_sessions[id_string]["session_id"]
            click.secho(f"Session ID:{id_for_session_reg} - Uniq:{from_row['uniq_course']} - User: {from_row['uid']}", fg="yellow")
            payload = {"user_id": get_user_id}
            try:
                user_register = requests.post(f"{base_url}author/live_course_sessions/{id_for_session_reg}/registrations", headers=headers, data=json.dumps(payload))
                if user_register.status_code == 204:
                    success_csv_list.append({"uid":from_row["uid"], "session_id":id_for_session_reg, "live_course_id": from_row["live_course_id"]})
                else:
                    error_csv_list.append({"status_code":user_register.status_code, "message": f"The API call could not register the user {from_row['uid']} in session {id_for_session_reg}"})
            except:
                error_csv_list.append({"status_code":"Unknown", "message":f"Something went wrong when to register the user {from_row['uid']} in session {id_for_session_reg}"})
        else:
            if get_user.status_code == 200:
                error_csv_list.append({"status_code":None, "message":f"The publish session call failed for session_id: {created_sessions[id_string]['session_id']}"})
            else:
                error_csv_list.append({"status_code":get_user.status_code, "message":f"The API call could not return a user with the UID: {from_row['uid']}"})
    except:
        error_csv_list.append({"status_code":"Unknown", "message":f"Something went wrong when to get the user {from_row['uid']} from Bridge"})

def write_error_log(error_list, domain):
    with open(f'{domain}_ILT_HDM_errors_' + str(datetime.today()).replace(" ", "_")[0:-16] + '.csv',newline='',mode='w+') as err_file:
        fieldnames = ['status_code','message']
        writer = csv.DictWriter(err_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in error_list:
            writer.writerow(row)

def write_return_log(return_list, domain):
    with open(f"{domain}_ILT_HDM_return_" + str(datetime.today()).replace(" ","_")[0:-16] + '.csv',newline='',mode='w+') as return_file:
        fieldnames =['uid','session_id','live_course_id']
        writer = csv.DictWriter(return_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in return_list:
            writer.writerow(row)

if __name__ == "__main__":
    main()
