# README

Killing streams is a Plex Pass only feature. So these scripts will **only** work for Plex Pass users.

## `kill_stream.py` examples:

### Kill transcodes

Triggers: Playback Start  
Conditions: \[ `Transcode Decision` | `is` | `transcode` \]

Arguments:
```
--jbop stream --username {username} --sessionId {session_id} --killMessage Transcoding streams are not allowed.
```

### Kill non-local streams paused for a long time

_The default values will kill anything paused for over 20 minutes, checking every 30 seconds._

Script Timeout: 0 _**Important!**_  
Triggers: Playback Paused  
Conditions:
* \[ `Stream Local` | `is not` | `1` \]
* \[ `Synced Version` | `is not` | `1` \]

Arguments:
```
--jbop paused --sessionId {session_id} --killMessage Your stream was paused for over 20 minutes and has been automatically stopped for you.
```

### Kill streams paused for a custom time

_This is an example of customizing the paused stream monitoring to check every 15 seconds, and kill any stream paused for over 5 minutes._

Script Timeout: 0 _**Important!**_  
Triggers: Playback Paused  

Arguments:
```
--jbop paused --interval 15 --limit 300 --sessionId {session_id} --killMessage Your stream was paused for over 5 minutes and has been automatically stopped for you.
```

### Kill paused transcodes

Triggers: Playback Paused  
Conditions: \[ `Transcode Decision` | `is` | `transcode` \]

Arguments:
```
--jbop stream --username {username} --sessionId {session_id} --killMessage Paused streams are automatically stopped.
```

### Limit User stream count, kill last stream

Triggers: Playback Start  
Conditions: \[ `User Streams` | `is greater than` | `3` \]

Arguments:
```
--jbop stream --username {username} --sessionId {session_id} --killMessage You are only allowed 3 streams.
```

### IP Whitelist

Triggers: Playback Start  
Conditions: \[ `IP Address` | `is not` | `192.168.0.100 or 192.168.0.101` \]

Arguments:
```
--jbop stream --username {username} --sessionId {session_id} --killMessage {ip_address} is not allowed to access {server_name}.
```

### Kill by platform

Triggers: Playback Start  
Conditions: \[ `Platform` | `is` | `Roku or Android` \]

Arguments:
```
--jbop stream --username {username} --sessionId {session_id} --killMessage {platform} is not allowed on {server_name}.
```

### Kill transcode by library

Triggers: Playback Start  
Conditions:
* \[ `Transcode Decision` | `is` | `transcode` \]
* \[ `Library Name` | `is` | `4K Movies` \]

Arguments:
```
--jbop stream --username {username} --sessionId {session_id} --killMessage Transcoding streams are not allowed from the 4K Movies library.
```

### Kill transcode by original resolution

Triggers: Playback Start  
Conditions:
* \[ `Transcode Decision` | `is` | `transcode` \]
* \[ `Video Resolution` | `is` | `1080 or 720`\]

Arguments:
```
--jbop stream --username {username} --sessionId {session_id} --killMessage Transcoding streams are not allowed for {stream_video_resolution}p streams.
```

### Kill transcode by bitrate

Triggers: Playback Start  
Conditions:
* \[ `Transcode Decision` | `is` | `transcode` \]
* \[ `Bitrate` | `is greater than` | `4000` \]

Arguments:
```
--jbop stream --username {username} --sessionId {session_id} --killMessage Transcoding streams are not allowed from over 4 Mbps (Yours: {stream_bitrate}).
```

### Kill by hours of the day

_Kills any streams during 9 AM to 10 AM._

Triggers: Playback Start  
Conditions: \[ `Timestamp` | `begins with` | `09 or 10` \]  
Arguments:
```
--jbop stream --username {username} --sessionId {session_id} --killMessage {server_name} is unavailable between 9 and 10 AM.
```

### Kill non local streams

Triggers: Playback Start  
Conditions: \[ `Stream Local` | `is not` | `1` \]  
Arguments:
```
--jbop stream --username {username} --sessionId {session_id} --killMessage {server_name} only allows local streams.
```

### Kill transcodes and send a notification to agent 1

Triggers: Playback Start  
Conditions: \[ `Transcode Decision` | `is` | `transcode` \]

Arguments:
```
--jbop stream --username {username} --sessionId {session_id} --notify 1 --killMessage Transcoding streams are not allowed.
```

### Kill transcodes using the default message

Triggers: Playback Start  
Conditions: \[ `Transcode Decision` | `is` | `transcode` \]

Arguments:
```
--jbop stream --username {username} --sessionId {session_id}
```

### Kill all of a user's streams with notification

Triggers: Playback Start  
Conditions: \[ `Username` | `is` | `Bob` \]

Arguments:
```
--jbop allStreams --userId {user_id} --notify 1 --killMessage Hey Bob, we need to talk!
```
