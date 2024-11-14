import base64
from datetime import datetime

import apprise
from jinja2 import Template


def send_mission_data_via_email_html(todays_data):
    current_date = datetime.now().strftime("%d/%m/%Y")

    if todays_data['day'] != current_date:
        print(f"No mission data available for today ({current_date}).")
        return

    with open('./src/message/mission.html.jinja', 'r') as file:
        template = Template(file.read())
    with open("./screenshot/login_reward.png", 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode('utf-8')

    mission_summary_html = template.render(
        day=todays_data['day'],
        check_in=todays_data['check_in'],
        missions=todays_data['missions'],
        login_reward_image=f"data:image/png;base64,{encoded_image}"
    )

    apobj = apprise.Apprise()
    apobj.add('mailto://galevan61:jlqrqxxtaggvnuce@gmail.com')

    try:
        apobj.notify(
            body=mission_summary_html,
            title=f"Mission Report for {todays_data['day']}",
            body_format='html',

        )
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")
