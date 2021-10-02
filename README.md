# tungstite

log and recall MTA delivery status

## rationale

Atheme, in its current state, is incapable of knowing what happened to an
email once it has passed it off to e.g. sendmail, and thus the only way to
track down why a user is reporting that they did not receive their nickserv
email is to grep MTA logs. This bot is automated MTA log grepping.

## setup

```
$ cp config.example.yaml config.yaml
$ vim config.yaml
```

## running

```
$ python3 -m tungstite config.yaml
```

## using
```
< jess> !emailstatus liberachat@example.com
-tungstite- 2021-10-02T02:35:19 (57s ago) liberachat@example.com is sent: 250 2.0.0 Queued as 09400E201AF
-tungstite- 2021-10-02T02:35:14 (1m2s ago) liberachat@example.com is sent: 250 2.0.0 Queued as DAD9199221E
-tungstite- 2021-10-02T02:34:00 (1m16s ago) liberachat@example.com is deferred: lost connection with example.com[127.0.0.1] while receiving the initial server greeting
```

