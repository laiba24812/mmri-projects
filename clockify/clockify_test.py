import requests
import pandas as pd
from datetime import datetime
import re

API_KEY = "OWQyNzc1NTItNTkzZS00NWRlLTliM2EtYTNhNzJjZmZhZWY1"
WORKSPACE_ID = "5d31e75e59da6530a30fc2f1"

headers = {"X-Api-Key": API_KEY}

name_mapping = {
    "feenstdr": "Darren Feenstra",
    "Patrick Chin": "Patrick Chin",
    "Kristin Bennett": "Kristin Bennett",
    # add others as you identify them
}

# Get projects
projects_response = requests.get(
    f"https://api.clockify.me/api/v1/workspaces/{WORKSPACE_ID}/projects",
    headers=headers
)
projects = {p['id']: p['name'] for p in projects_response.json()}

# Get users
users_response = requests.get(
    f"https://api.clockify.me/api/v1/workspaces/{WORKSPACE_ID}/users",
    headers=headers
)
users = users_response.json()

def parse_duration(duration):
    if not duration:
        return 0
    hours = re.search(r'(\d+)H', duration)
    minutes = re.search(r'(\d+)M', duration)
    h = int(hours.group(1)) if hours else 0
    m = int(minutes.group(1)) if minutes else 0
    return round(h + m/60, 2)

all_entries = []

for user in users:
    user_id = user['id']
    user_name = user['name']
    
    entries_response = requests.get(
        f"https://api.clockify.me/api/v1/workspaces/{WORKSPACE_ID}/user/{user_id}/time-entries",
        headers=headers
    )
    entries = entries_response.json()
    
    for entry in entries:
        project_id = entry.get('projectId', '')
        project_name = projects.get(project_id, 'No Project')
        duration = entry.get('timeInterval', {}).get('duration', '')
        start = entry.get('timeInterval', {}).get('start', '')
        
        if start:
            date = datetime.fromisoformat(start.replace('Z', '+00:00')).strftime('%Y-%m-%d')
            week = datetime.fromisoformat(start.replace('Z', '+00:00')).strftime('%Y-W%W')
        else:
            date = ''
            week = ''

        MMRI_PROJECTS = ['ORF0', 'ORF3', 'FACTR1', 'TRAIN8', 'TYCOS10', 'ENGAGE1', 'MONO1']

        if any(code in project_name for code in MMRI_PROJECTS):
             all_entries.append({
                'Employee': name_mapping.get(user_name, user_name),
                'Project': project_name,
                'Date': date,
                'Week': week,
                'Hours': parse_duration(duration)
    })
        
        all_entries.append({
            'Employee': name_mapping.get(user_name, user_name),
            'Project': project_name,
            'Date': date,
            'Week': week,
            'Hours': parse_duration(duration)
        })

        # Get all projects
projects_response = requests.get(
    f"https://api.clockify.me/api/v1/workspaces/{WORKSPACE_ID}/projects",
    headers=headers
)
projects = projects_response.json()
for p in projects:
    print(p['id'], '-', p['name'])

df = pd.DataFrame(all_entries)
df.to_csv('clockify_data.csv', index=False)
print("Done! clockify_data.csv created")
print(df.head())