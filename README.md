# Projet Memetracker

Cet ensemble de programmes permet l'analyse et la visualisation de données textuelles provenant de pages web et réseaux sociaux (en particulier Twitter).

# Prérequis
L'ensemble des programmes est écrit en langage **Python** (version 3) pour l'analyse et **Javascript** pour la visualisation. Python doit etre installé sur la machine afin de faire tourner les scripts. De plus, les fichiers *.ipynb sont des notebooks Jupyter qui necessitent que [Jupyter](http://jupyter.org/) soit installé avec Python.

# Comment l'utiliser

## Analyse avec Python
Les données à analyser sont supposés être sous forme de fichiers csv, chaque ligne etant une publication.
Le fichier *memeconfig.ini* contient les chemins où sont stockés les divers fichiers.
```ini
[DEFAULT]
data_path = /csv_data_path/
pickle_data_path = /path_where_python_save_processed_data/
viz_data_path = /path_for_the_visualization_files/
time_data_path = /path_for_the_visualisation_of_time_evolution/
```

### Preprocessing
Le preprocessing consiste en l'extraction des données des fichiers csv et leur traitement par "natural language processing" avec la toolbox Python NLTK.Les caractères spéciaux contenus dans les textes sont enlevés ainsi que les "stopwords". Les résultats sont ensuite stockés dans des fichiers *.pickle, format standard de Python. Ce preprocessing est effectué en appelant la fonction suivante:
```bash
python preprocess_text_data.py
```
Le choix de la série à traiter se fait à l'intérieur du fichier (variable à modifier).

### Le graphe multicouches
Un graphe est construit à partir des données traitées/ filtrées par le pre-processing. A partir de ce graph, des composants dynamiques sont extraits pour être affichés. La fonction suivante crée le multigraphe et sauve les composants dans des fichiers distincts. Le temps est découpé en jours.
```bash
python compute_c_components.py
```
Une variante de ce fichier traite les données en découpant des tranches par heure.
```bash
python compute_c_components_hours.py
```

### L'arbre à mèmes
Un fichier python permet créer un arbre à partir d'un mot choisi. Les branches sont les mots qui suivent le mot choisi avec le nombre de fois qu'ils apparaissent à sa suite dans le corpus de document. Le résultat est stocké comme un graphe dans un fichier json. La commande pour créer ce fichier est le suivant:
```bash
python compute_treegraph.py
```
Le mot choisi ainsi que la série et le nombre de mots suivants doivent etre paramétré à l'intérieur du fichier. Une version avec des paramètre en ligne de commande peut être appelée, par exemple pour le mot "politique" dans la serie "Baron Noir" pendant l'année 2016:
```bash
python compute_treegraph_cmd.py 'politique' 'baron_noir' '01-01-2016' '31-12-2016'
```
Cette commande est aussi appelée par le programme de visualisation.

### La toolbox python
Un module python sous forme de toolbox a été créée pour structurer le code. Ce module se nomme memebox est peut etre utilisé dans un programme python en utilisant la commande "import memebox".




