.PHONY: default, help, nextweek, current, today, convert

default: nextweek

help:
	scripts/help next_week
	scripts/help current
	scripts/help today
	scripts/help convert

nextweek:
	scripts/nextweek $(date)

current:
	scripts/current $(date)

today:
	scripts/today

convert:
	scripts/convert $(file)