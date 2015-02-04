trans:
	pybabel extract -F babel.cfg -o messages.pot .
	pybabel update -i messages.pot -d translations
	rm messages.pot
compiletrans:
	pybabel compile -d translations
