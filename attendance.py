import requests
from bs4 import BeautifulSoup
import pandas as pd
from pymongo import MongoClient
import smtplib
from email.mime.text import MIMEText

# MongoDB connection
client = MongoClient("mongodb+srv://22z212:TfVGyfVhyjG8hkNJ@cluster0.gbcugd2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['ecampus']  # Use your database name
collection = db['attendance']  # Use your collection name

# Email setup
def send_email(subject, body):
    sender_email = "22z212@psgtech.ac.in"
    receiver_email = ["22z235@psgtech.ac.in", "cheran411@gmail.com"]
    password = "cheran#212"  # Consider using environment variables for security

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_email)

    with smtplib.SMTP('smtp.gmail.com', 587) as server:  # Use your SMTP server details
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())


# Function to get current attendance data
def get_attendance_data():
    session = requests.Session()
    login_url = 'https://ecampus.psgtech.ac.in/studzone2/'
    
    # Perform login
    response = session.get(login_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    viewstate = soup.find('input', {'name': '__VIEWSTATE'})['value']
    viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value']
    event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})['value']

    login_data = {
        '__VIEWSTATE': viewstate,
        '__VIEWSTATEGENERATOR': viewstate_generator,
        '__EVENTVALIDATION': event_validation,
        'txtusercheck': '22z212',  # Replace with actual username
        'txtpwdcheck': 'cheran#212',  # Replace with actual password
        'abcd3': 'Login'
    }

    response = session.post(login_url, data=login_data)
    if "login failed" in response.text.lower():
        print("Login failed.")
        return None

    attendance_page_response = session.get("https://ecampus.psgtech.ac.in/studzone2/AttWfPercView.aspx")
    attendance_page_soup = BeautifulSoup(attendance_page_response.content, 'html.parser')
    attendance_table = attendance_page_soup.find('table', {'id': 'PDGcourpercView'})
    
    headers = [header.text for header in attendance_table.find_all('tr')[0].find_all('td')]
    rows = attendance_table.find_all('tr', {'onmouseover': "javascript:prettyDG_changeBackColor(this, true);"})
    
    attendance_data = []
    for row in rows:
        cells = row.find_all('td')
        row_data = [cell.text.strip() for cell in cells]
        attendance_data.append(dict(zip(headers, row_data)))
    
    return attendance_data

# Main logic
current_data = get_attendance_data()
if current_data:
    # Check for changes
    previous_data = list(collection.find({}))

    if current_data != previous_data:  # Compare current and previous data
        # Store current data
        collection.delete_many({})  # Clear previous data
        collection.insert_many(current_data)
        
        # Send an email notification
        send_email("Attendance Update", "The attendance data has changed.")
        print("Email sent regarding attendance update.")
    else:
        print("No changes in attendance data.")
