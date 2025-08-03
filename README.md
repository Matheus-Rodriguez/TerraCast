
# TerraCast 

### Como utilizar

**Crie um virtual environment (neste caso chamado terracast)**
```` 
python3 -m venv terracast
```` 
**Ative o virtual environment (Linux)**
````
source terracast/bin/activate
````
***Ative o virtual environment (Windows)***
````
./terracast/Scripts/activate
````
**Em seguida instale os pacotes necessários**
```` 
pip install -r requirements.txt
````
**Para executar o site (vá para TerraCast/conflito) (Linux)**
````
python3 manage.py runserver
````
***Para executar o site (vá para TerraCast/conflito) (Windows)***
````
python manage.py runserver
````
**Por fim, abre o site no localhost na aba "mapa"**
```
http://127.0.0.1:8000/mapa/
```
**Para sair do virtual environment (o que fica aparecendo (terracast) no prompt)**
```
deactivate
```