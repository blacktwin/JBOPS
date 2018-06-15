## README

Killing streams is a Plex Pass only feature. So these scripts will only work for Plex Pass users.



### Kill_stream.py examples:

#### Arguments examples:

Kill the one offending stream with a custom message and send notification to notfication agent ID 1
    
    --jbop stream --userId {user_id} --username {username} --sessionId {session_id} --killMessage You did something wrong. --notify 1

Kill all the offending users streams with a custom message and send notification to notfication agent ID 1
    
    --jbop allStreams --userId {user_id} --username {username} --sessionId {session_id} --killMessage You did something wrong. --notify 1

Kill the one offending stream with default message

    --jbop stream --userId {user_id} --username {username} --sessionId {session_id}


#### Condition Examples:

Kill transcodes:

    Set Trigger: Playback Start
    Set Conditions: [ {Transcode Decision} | {is} | {transcode} ]

Kill paused transcodes:
    
    Set Trigger: Playback Paused
    Set Conditions: [ {Transcode Decision} | {is} | {transcode} ]

Limit User stream count, kill last stream:
    
    Set Trigger: Playback Start
    Set Conditions: [ {User Streams} | {is greater than} | {3} ]

IP Whitelist:
    
    Set Trigger: Playback Start
    Set Conditions: [ {IP Address} | {is not} | {192.168.0.100 or 192.168.0.101} ]

Kill by platform:
    
    Set Trigger: Playback Start
    Set Conditions: [ {Platform} | {is} | {Roku or Android} ]

Kill transcode by library:
    
    Set Trigger: Playback Start
    Set Conditions: [ {Transcode Decision} | {is} | {transcode} ]
                [ {Library Name} | {is} | {4K Movies} ]

Kill transcode by original resolution:
    
    Set Trigger: Playback Start
    Set Conditions: [ {Transcode Decision} | {is} | {transcode} ]
                    [ {Video Resolution} | {is} | {1080 or 720}]

Kill transcode by bitrate:
    
    Set Trigger: Playback Start
    Set Conditions: [ {Transcode Decision} | {is} | {transcode} ]
                    [ {Bitrate} | {is greater than} | {4000} ]

Kill by hours of the day:
    
    Set Trigger: Playback Start
    Set Conditions: [ {Timestamp} | {begins with} | {09 or 10} ]
    # Killing any streams from 9am to 11am

Kill non local streams:
    
    Set Trigger: Playback Start
    Set Conditions: [ {Stream location} | {is} | {wan} ]
    or
    Set Conditions: [ {Stream location} | {is not} | {lan} ]

