# Out Baby Out

**Real-life tag, scored from a log a human can write while the game is happening.**

Two teams, a timer. You freeze someone by getting close to them — *vish*. A teammate who reaches them brings them back — *amrit*. Whoever has more players standing when the timer ends wins.

```
py -3 outbabyout.py match.txt --html
```

```
  20:00 match, 6 players
  --------------------------------------------------------
  BLUE      2 of 3   ##.
  RED       2 of 3   ##.

  Drawn on 2 each: BLUE, RED
  4 tags, 2 amrits.
  The amrits are why it was still a game at the end.
```

## Why the revive is the whole thing

Every app in this category — TagTown, ZombieShoe, HideZone, Zombie Apocalypse GPS — is last-human-standing. Straight infection has no way back, so the second half of every match is a formality and the losing side goes home.

**Vish Amrit** is a game Indian children already play: touched, you are *vish* and must sit; a teammate touching you gives *amrit* and you are back in. It turns a death spiral into a tug of war, and it means the clock decides the match instead of attrition.

It is not a localisation. It is a better rule that happens to already have a name here.

## The log is plain text on purpose

The first games are played with **no app at all** — people in a park, tags called out loud, someone typing lines on their phone. This reads that, and it will read a phone's output later without changing, because the format is the same either way.

```
# Gachibowli, 13 Sept
LENGTH 20:00

RED   gokul, arjun, sai
BLUE  daniel, priya, rahul

02:14  gokul > priya      # a tag
03:40  daniel + priya     # an amrit
```

## What it refuses

A log it cannot read is **BLOCKED**, never scored. It exits 2 and says which line.

That is not politeness. A match that scores 3–2 because two tags were unreadable looks exactly like a match that really was 3–2. So every one of these stops the run rather than moving the score quietly:

- a player who is not on any team, or is on both
- tagging your own teammate, or reviving someone else's
- a frozen player acting
- freezing someone already frozen, reviving someone who is not
- events out of order, or after full time
- a line that is not a team, a `LENGTH`, or an event

`py -3 outbabyout.py --check` runs all of it. The checks were verified by breaking the logic and confirming they fail.

## What it is not

Not an app. Not a fitness tracker. Not location sharing — when there is a phone build, it will report **direction and distance only**, never position, because every incumbent in this category died on live location. Not playable from a vehicle: bikes are how you travel between zones, never how you tag, and that will be absent from the schema rather than forbidden in a rule.

## Next

1. ~~Score a match~~
2. Run one real game with ten people and no app
3. Measure BLE proximity — does a tag register at 2m and not at 10m
4. Only then, an app

Standard library only.
