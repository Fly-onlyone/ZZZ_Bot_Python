from datetime import datetime

import apprise


def send_mission_data_via_email_html(todays_data):
    # Get the current date in the format 'day/month/year'
    current_date = datetime.now().strftime("%d/%m/%Y")

    if todays_data['day'] != current_date:
        print(f"No mission data available for today ({current_date}).")
        return

    # HTML Email body with inline CSS styles
    mission_summary_html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            h1 {{ color: #4CAF50; }}
            table {{ width: 100%; border-collapse: collapse; margin: 25px 0; }}
            th, td {{ padding: 12px 15px; border: 1px solid #ddd; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
        </style>
    </head>
    <body>
        <h1>Mission Report for {todays_data['day']}</h1>
        <p><strong>Check-in Status:</strong> {todays_data['check_in']}</p>
        <h2>Mission Status:</h2>
        <table>
            <tr>
                <th>Mission</th>
                <th>Status</th>
            </tr>
    """

    for mission in todays_data['missions']:
        mission_summary_html += f"""
            <tr>
                <td>{mission['name']}</td>
                <td>{mission['state']}</td>
            </tr>
        """

    mission_summary_html += """
        </table>
    </body>
    </html>
    """

    # Apprise instance
    apobj = apprise.Apprise()

    # Add your email provider (make sure credentials are correct)
    apobj.add('mailto://***REMOVED***:***REMOVED***@gmail.com')

    # Send the HTML-formatted email
    try:
        apobj.notify(
            body=mission_summary_html,
            title=f"Mission Report for {todays_data['day']}",
            body_format='html',  # This tells Apprise to send HTML content
        )
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")