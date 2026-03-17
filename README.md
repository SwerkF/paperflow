# paperflow

Petit projet de test avec `PaddleOCR` pour extraire le texte d'une image et sauvegarder les resultats en JSON et en image annotee.

## Prerequis

- Python 3.10 ou plus recent
- `pip`
- Une connexion Internet au premier lancement pour telecharger les modeles PaddleOCR

## Installation

Il est recommande de creer un environnement virtuel.

### Windows PowerShell

```powershell
cd paperflow
python -m venv env
.\env\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install paddlepaddle paddleocr
```

### Linux / macOS

```bash
cd paperflow
python3 -m venv env
source env/bin/activate
python -m pip install --upgrade pip
python -m pip install paddlepaddle paddleocr
```

## Fichiers

- `test.py` : lance un OCR sur une image de demonstration distante.
- `test_local.py` : lance un OCR sur `facture_electricite.png` exposee en local via `http://127.0.0.1:8000/`.
- `facture_electricite.png` : image de facture utilisee pour le test local.

## Utilisation

Important : lance les commandes depuis le dossier `paperflow`, sinon le dossier `output2` sera cree ailleurs.

### 1. Script de demo

Ce script utilise une image distante fournie par PaddleOCR.

```powershell
cd paperflow
.\env\Scripts\Activate.ps1
python test.py
```

Ce que fait le script :

- initialise `PaddleOCR` en mode CPU
- telecharge et analyse l'image de demo
- cree le dossier `output2` si besoin
- enregistre un fichier `result_0.json`
- regroupe tous les resultats dans `output2/result.json`
- sauvegarde aussi une image annotee dans `output2`

### 2. Script local

`test_local.py` ne lit pas directement un fichier disque : il attend une image servie en HTTP a l'adresse `http://127.0.0.1:8000/facture_electricite.png`.

Ouvre un premier terminal :

```powershell
cd paperflow
python -m http.server 8000
```

Puis, dans un second terminal :

```powershell
cd paperflow
.\env\Scripts\Activate.ps1
python test_local.py
```

Ce script produit :

- `output2/facture_result_0.json`
- `output2/facture_result.json`
- une image annotee dans `output2`

## Structure des sorties

Les scripts creent automatiquement le dossier `output2/` avec :

- des fichiers JSON par resultat
- un JSON final qui regroupe l'ensemble
- des images annotees generees par PaddleOCR

## Notes utiles

- Les scripts forcent l'utilisation du CPU avec `device="cpu"`.
- `enable_mkldnn=False` et `FLAGS_use_mkldnn=0` sont desactivent certaines optimisations CPU pour eviter des problemes de compatibilite.
- Au premier lancement, l'initialisation peut etre plus longue a cause du telechargement des modeles.

## Depannage

### `ModuleNotFoundError: No module named 'paddleocr'`

L'environnement virtuel n'est probablement pas active, ou les dependances ne sont pas installees :

```powershell
.\env\Scripts\Activate.ps1
python -m pip install paddlepaddle paddleocr
```

### `http://127.0.0.1:8000/facture_electricite.png` ne repond pas

Il faut lancer le serveur local dans `paperflow` :

```powershell
cd paperflow
python -m http.server 8000
```

### Les fichiers de sortie ne sont pas dans `paperflow/output2`

Les scripts utilisent un chemin relatif. Execute-les bien depuis le dossier `paperflow`.
