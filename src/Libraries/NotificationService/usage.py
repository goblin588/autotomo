from main import send_email
import os
# Set the subject of the email
# Read the HTML content from the file
email_receiver = 'brendanwallis01@gmail.com'
subject = 'Measurement Completed Notification'

send_email(email_receiver, subject=subject, is_html=True)
