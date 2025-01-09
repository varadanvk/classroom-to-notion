# from functools import partial
from mac_notifications import client

if __name__ == "__main__":
    client.create_notification(
        title="Notion Auth Token Expired!!",
        subtitle="THIS IS A NOTIFICATION LIL BRO",
        icon="/Users/jorrick/zoom.png",
        sound="Frog",
        action_button_str="Kill Yourself",
        # action_callback=partial(join_zoom_meeting, conf_number=zoom_conf_number)
    )
