from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime
import requests

# --- 1. FONCTIONS MÉTIER ---

def analyse_ocr_func(**kwargs):
    print("Appel de l'API OCR...")
    dag_run_conf = kwargs.get('dag_run').conf or {}
    
    bronze_id = dag_run_conf.get("bronze_id")
    if not bronze_id:
        raise ValueError("Aucun bronze_id fourni dans la configuration du DAG.")
        
    print(f"Récupération de l'image pour le document {bronze_id} depuis Datalake...")
    try:
        dl_resp = requests.get(f"http://datalake_api:8000/storage/bronze/{bronze_id}/image")
        dl_resp.raise_for_status()
        image_base64 = dl_resp.json().get("file_data")
        if not image_base64:
            raise ValueError("Le datalake n'a renvoyé aucun 'file_data'.")
    except Exception as e:
        print(f"Erreur téléchargement image Datalake : {e}")
        raise e
        
    payload = {"image_base64": image_base64}
    
    try:
        response = requests.post("http://api_ocr:8000/api/v1/analyze", json=payload)
        response.raise_for_status()
        
        resultat = response.json()
        print(f"Réponse de l'OCR : extraction réussie.")
        
        kwargs['ti'].xcom_push(key="donnees_ocr", value=[resultat.get("data")])
        return "reconnues"
    except Exception as e:
        print(f"Erreur OCR: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(response.text)
        raise e


def croisement_donnees_func(**kwargs):
    print("Appel de l'API de Validation...")
    ti = kwargs['ti']
    
    documents_extraits = ti.xcom_pull(key="donnees_ocr", task_ids='analyse_ocr')
    
    dag_run_conf = kwargs.get('dag_run').conf or {}
    siret_attendu = dag_run_conf.get("siret_principal", "73282932000074")
    nom_attendu = dag_run_conf.get("nom_principal", "MaSuperBoite SAS")

    payload = {
        "contexte_utilisateur": {
            "entreprise_id": str(dag_run_conf.get("entrepriseId", "ENT-TEST")),
            "nom_principal": nom_attendu,
            "siret_principal": siret_attendu
        },
        "documents": documents_extraits
    }

    try:
        response = requests.post("http://data_validation:5030/api/v1/documents/batch", json=payload)
        response.raise_for_status() 
        
        resultat = response.json()
        print(f"Réponse de l'API : {resultat}")

        if resultat.get("anomalies_detectees", 0) == 0:
            ti.xcom_push(key="contextes_verifies", value=resultat.get("contextes_verifies", []))
            return "conforme"
        else:
            ti.xcom_push(key="details_alertes", value=resultat.get("details_alertes"))
            ti.xcom_push(key="contextes_verifies", value=resultat.get("contextes_verifies", []))
            return "incoherentes"
            
    except Exception as e:
        print(f"Erreur de connexion à l'API Validation : {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(response.text)
        raise e


def check_conformite(**kwargs):
    statut_conformite = kwargs['ti'].xcom_pull(task_ids='croisement_donnees')
    if statut_conformite == "conforme":
        return 'enregistrement_db_conforme'
    else:
        return 'alerte_donnees_incoherentes'


def mise_a_jour_statut_func(**kwargs):
    ti = kwargs['ti']
    dag_run_conf = kwargs.get('dag_run').conf or {}
    bronze_id = dag_run_conf.get("bronze_id")
    
    statut_conformite = ti.xcom_pull(task_ids='croisement_donnees')
    statut_final = "VALIDE" if statut_conformite == "conforme" else "EN_ATTENTE_SUPERVISION"
    alertes = ti.xcom_pull(key="details_alertes", task_ids='croisement_donnees') if statut_conformite == "incoherentes" else None
    
    contextes_verifies = ti.xcom_pull(key="contextes_verifies", task_ids='croisement_donnees')
    extracted_data = contextes_verifies[0] if contextes_verifies and len(contextes_verifies) > 0 else None

    # Webhook DataLake backend
    webhook_url = "http://datalake_api:8000/webhook/airflow_result"
    
    payload = {
        "bronze_id": bronze_id,
        "statut_final": statut_final,
        "alertes": alertes,
        "extracted_data": extracted_data
    }
    
    try:
        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        print(f"Webhook envoyé avec succès : {response.json()}")
    except Exception as e:
        print(f"Erreur webhook : {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(response.text)
        raise e

    return "succes"


# --- 2. DÉFINITION DU DAG ---

with DAG(
    dag_id='hackathon_flow_complet',
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['hackathon', 'production']
) as dag:
    
    # Déclaration des tâches
    t_analyse_ocr = PythonOperator(task_id='analyse_ocr', python_callable=analyse_ocr_func)
    t_croisement = PythonOperator(task_id='croisement_donnees', python_callable=croisement_donnees_func)
    
    t_alerte_incoherentes = EmptyOperator(task_id='alerte_donnees_incoherentes')
    t_enregistrement_conforme = EmptyOperator(task_id='enregistrement_db_conforme')
    
    t_maj_statut_fin = PythonOperator(
        task_id='mise_a_jour_statut_bdd', 
        python_callable=mise_a_jour_statut_func,
        trigger_rule='none_failed_min_one_success'
    )
    
    t_fin = EmptyOperator(task_id='fin')

    # Aiguillages
    b_check_conformite = BranchPythonOperator(task_id='donnees_conformes', python_callable=check_conformite)

    # Câblage
    t_analyse_ocr >> t_croisement >> b_check_conformite
    
    b_check_conformite >> t_enregistrement_conforme >> t_maj_statut_fin
    b_check_conformite >> t_alerte_incoherentes >> t_maj_statut_fin
    
    t_maj_statut_fin >> t_fin