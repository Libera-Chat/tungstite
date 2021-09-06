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

