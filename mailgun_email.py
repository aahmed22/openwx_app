import requests, os
from dotenv import load_dotenv

load_dotenv()

def send_simple_message(to, subject, body, html_file, excel_file):
        
        mg_api_key = os.getenv("MAILGUN_API_KEY")
        mg_domain = os.getenv("MAILGUN_DOMAIN")
        mg_url = os.getenv("MAILGUN_URL")

        html_report = open(html_file, 'rb')
        file_attachment = open(excel_file, 'rb')
    
        try: 
            print("Sending Email Notification...")
            return requests.post(
            f"{mg_url}{mg_domain}/messages", 
            auth=("api", mg_api_key), 
            files=[("attachment", file_attachment)],
            data={"from": f"Python Language Assistant <mailgun@{mg_domain}>", 
            "to": [to], 
            "subject": subject, 
            "text": body,
            "html": html_report})
        except Exception as e:
              print(e)
              print("Failed to send email!")