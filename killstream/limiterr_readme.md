# README

Killing streams is a Plex Pass only feature. So these scripts will **only** work for Plex Pass users.

## `limitter.py` examples:

### Limit user to an amount of Plays of a show during a time of day
_For users falling asleep while autoplaying a show_ :sleeping:\
Triggers: Playback Start  
Conditions: \[ `Current Hour` | `is` | `22 or 23 or 0 or 1` \]

Arguments:
```
--jbop limit --username {username} --sessionId {session_id} --grandparent_rating_key {grandparent_rating_key} --limit plays=3 --delay 60 --killMessage "You sleeping?"
```

### Limit user to total Plays/Watches and send a notification to agent 1
_Completed play sessions_ \
Triggers: Playback Start  

Arguments:
```
--jbop watch --username {username} --sessionId {session_id} --limit plays=3 --notify 1 --killMessage "You have met your limit of 3 watches."
```

### Limit user to total Plays/Watches in a specific library (Movies)
_Completed play sessions_ \
Triggers: Playback Start  

Arguments:
```
--jbop watch --username {username} --sessionId {session_id} --limit plays=3 --section Movies --killMessage "You have met your limit of 3 watches."
```

### Limit user to total time watching

Triggers: Playback Start  

Arguments:
```
--jbop time --username {username} --sessionId {session_id} --limit days=3 --limit hours=10 --killMessage "You have met your limit of 3 days and 10 hours."
```


### Limit user to total play sessions for the day

Triggers: Playback Start  

Arguments:
```
--jbop plays --username {username} --sessionId {session_id} --days 0 --limit plays=3 --killMessage "You have met your limit of 3 play sessions."
```

### Limit user to total time watching for the week, including duration of item starting

Triggers: Playback Start  

Arguments:
```
--jbop time --username {username} --sessionId {session_id} --duration {duration} --days 7 --limit hours=10 --killMessage "You have met your weekly limit of 10 hours."
```
