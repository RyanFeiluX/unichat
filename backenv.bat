@set timestamp=%date:~0,4%%date:~5,2%%date:~8,2%%time:~0,2%%time:~3,2%%time:~6,2%
@echo Save CONDA environment configuration ...
@call conda env export --no-builds > condaenv_%timestamp%.yaml
@copy condaenv_%timestamp%.yaml environment.yaml
@echo Save PIP environment configuration ...
@call pip list --format=freeze > pipenv_%timestamp%.txt
@copy pipenv_%timestamp%.txt requirements.txt
