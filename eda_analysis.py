"""
Script d'Analyse Exploratoire - Dataset RetailRocket E-commerce
================================================================

Ce script effectue une analyse exploratoire structurée du dataset RetailRocket.
Il couvre le chargement, le nettoyage et la création de variables dérivées.

Auteur: Data Analyst
Date: 2026-01-28
"""

# =============================================================================
# IMPORTS
# =============================================================================

# Manipulation de données
import pandas as pd
import numpy as np

# Visualisation
import matplotlib.pyplot as plt
import seaborn as sns

# Utilitaires
from datetime import datetime, timedelta
import warnings
import os

# Désactiver les warnings pour un affichage plus propre
warnings.filterwarnings('ignore')

# Configuration de l'affichage pandas
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.float_format', '{:.2f}'.format)

# Configuration des graphiques
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


# =============================================================================
# ÉTAPE 1 : CHARGEMENT DES DONNÉES
# =============================================================================

def load_events_data(file_path='data/raw/events.csv'):
    """
    Charge le fichier events.csv avec optimisation mémoire.
    
    Le fichier events contient les interactions utilisateurs :
    - timestamp : moment de l'événement (Unix milliseconds)
    - visitorid : identifiant anonyme du visiteur
    - event : type d'action (view, addtocart, transaction)
    - itemid : identifiant du produit
    - transactionid : identifiant de la transaction (si applicable)
    
    Parameters
    ----------
    file_path : str
        Chemin vers le fichier events.csv
    
    Returns
    -------
    pd.DataFrame
        DataFrame contenant les événements
    """
    print("🔄 Chargement de events.csv...")
    
    # Définir les types de colonnes pour optimiser la mémoire
    # int32 au lieu de int64 économise 50% de mémoire
    # category pour les variables catégorielles réduit aussi l'empreinte
    dtypes = {
        'visitorid': 'int32',      # Identifiant visiteur
        'event': 'category',        # Type d'événement (3 valeurs uniques)
        'itemid': 'int32',          # Identifiant produit
        'transactionid': 'float32'  # ID transaction (beaucoup de NaN)
    }
    
    # Charger le CSV avec les types spécifiés
    df = pd.read_csv(file_path, dtype=dtypes)
    
    print(f"✅ {len(df):,} événements chargés")
    print(f"   Mémoire utilisée: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    
    return df


def load_category_tree(file_path='data/raw/category_tree.csv'):
    """
    Charge la hiérarchie des catégories de produits.
    
    Structure hiérarchique où chaque catégorie peut avoir une catégorie parente.
    Les catégories racines ont parentid = NaN.
    
    Parameters
    ----------
    file_path : str
        Chemin vers le fichier category_tree.csv
    
    Returns
    -------
    pd.DataFrame
        DataFrame contenant la hiérarchie des catégories
    """
    print("🔄 Chargement de category_tree.csv...")
    
    dtypes = {
        'categoryid': 'int32',
        'parentid': 'float32'  # Float car contient des NaN pour les racines
    }
    
    df = pd.read_csv(file_path, dtype=dtypes)
    
    print(f"✅ {len(df):,} catégories chargées")
    
    return df


def load_item_properties(data_path='data/raw/'):
    """
    Charge et combine les fichiers de propriétés produits.
    
    Les propriétés sont stockées en format long (clé-valeur) :
    - timestamp : moment de la mise à jour
    - itemid : identifiant produit
    - property : nom de la propriété (categoryid, available, price, etc.)
    - value : valeur de la propriété
    
    Parameters
    ----------
    data_path : str
        Chemin vers le dossier contenant les fichiers
    
    Returns
    -------
    pd.DataFrame
        DataFrame combiné des propriétés produits
    """
    print("🔄 Chargement de item_properties (2 fichiers)...")
    print("   ⚠️  Cette étape peut prendre 1-2 minutes...")
    
    # Charger les deux parties
    part1 = pd.read_csv(f'{data_path}item_properties_part1.csv')
    part2 = pd.read_csv(f'{data_path}item_properties_part2.csv')
    
    # Combiner les deux parties
    df = pd.concat([part1, part2], ignore_index=True)
    
    print(f"✅ {len(df):,} propriétés chargées")
    
    return df


# =============================================================================
# ÉTAPE 2 : NETTOYAGE DES DONNÉES
# =============================================================================

def clean_events(df):
    """
    Nettoie et prépare le DataFrame events.
    
    Opérations effectuées :
    1. Conversion du timestamp en datetime
    2. Tri chronologique des événements
    3. Suppression des doublons éventuels
    4. Vérification de la cohérence des données
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame events brut
    
    Returns
    -------
    pd.DataFrame
        DataFrame events nettoyé
    """
    print("\n🧹 Nettoyage des données events...")
    
    # Créer une copie pour ne pas modifier l'original
    df_clean = df.copy()
    
    # --- Conversion du timestamp ---
    # Le timestamp est en millisecondes Unix, on le convertit en datetime
    print("   ⏰ Conversion des timestamps...")
    df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'], unit='ms')
    
    # --- Tri chronologique ---
    # Important pour les analyses temporelles et de parcours utilisateur
    print("   📊 Tri chronologique...")
    df_clean = df_clean.sort_values('timestamp').reset_index(drop=True)
    
    # --- Suppression des doublons ---
    # Vérifier s'il y a des lignes complètement identiques
    n_duplicates = df_clean.duplicated().sum()
    if n_duplicates > 0:
        print(f"   🗑️  Suppression de {n_duplicates:,} doublons")
        df_clean = df_clean.drop_duplicates()
    
    # --- Validation des types d'événements ---
    # Vérifier que seuls view, addtocart, transaction existent
    valid_events = ['view', 'addtocart', 'transaction']
    invalid_mask = ~df_clean['event'].isin(valid_events)
    n_invalid = invalid_mask.sum()
    
    if n_invalid > 0:
        print(f"   ⚠️  {n_invalid:,} événements invalides supprimés")
        df_clean = df_clean[~invalid_mask]
    
    # --- Statistiques de nettoyage ---
    print(f"\n✅ Nettoyage terminé:")
    print(f"   Lignes finales: {len(df_clean):,}")
    print(f"   Période: {df_clean['timestamp'].min().date()} "
          f"→ {df_clean['timestamp'].max().date()}")
    print(f"   Durée: {(df_clean['timestamp'].max() - df_clean['timestamp'].min()).days} jours")
    
    return df_clean


def check_missing_values(df, df_name='DataFrame'):
    """
    Analyse les valeurs manquantes dans un DataFrame.
    
    Affiche pour chaque colonne :
    - Le nombre de valeurs manquantes
    - Le pourcentage de valeurs manquantes
    - Le type de données
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame à analyser
    df_name : str
        Nom du DataFrame pour l'affichage
    """
    print(f"\n🔍 Analyse des valeurs manquantes - {df_name}")
    print("=" * 70)
    
    # Calculer les statistiques de valeurs manquantes
    missing_stats = pd.DataFrame({
        'Type': df.dtypes,
        'Manquants': df.isnull().sum(),
        'Pct_Manquants': (df.isnull().sum() / len(df) * 100).round(2)
    })
    
    # Filtrer uniquement les colonnes avec des valeurs manquantes
    missing_stats = missing_stats[missing_stats['Manquants'] > 0]
    
    if len(missing_stats) > 0:
        print(missing_stats.to_string())
        
        # Interprétation pour events
        if 'transactionid' in missing_stats.index:
            pct = missing_stats.loc['transactionid', 'Pct_Manquants']
            print(f"\n💡 Interprétation:")
            print(f"   transactionid est manquant pour {pct:.1f}% des lignes")
            print(f"   → Normal : seuls les événements 'transaction' ont un transactionid")
    else:
        print("✅ Aucune valeur manquante détectée")
    
    print("=" * 70)


def transform_item_properties(df):
    """
    Transforme les propriétés produits du format long au format large.
    
    Format initial (long) :
    itemid | property    | value
    123    | categoryid  | 456
    123    | available   | 1
    
    Format final (large) :
    itemid | categoryid | available
    123    | 456        | 1
    
    Cette transformation facilite grandement les analyses et jointures.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame item_properties en format long
    
    Returns
    -------
    pd.DataFrame
        DataFrame en format large avec propriétés en colonnes
    """
    print("\n🔄 Transformation des propriétés produits...")
    
    # --- Étape 1 : Conversion du timestamp ---
    df_work = df.copy()
    df_work['timestamp'] = pd.to_datetime(df_work['timestamp'], unit='ms')
    
    # --- Étape 2 : Garder la dernière valeur ---
    # Si un produit a plusieurs valeurs pour une propriété, 
    # on garde la plus récente (dernière mise à jour)
    print("   📅 Conservation de la dernière valeur par propriété...")
    df_work = df_work.sort_values('timestamp')
    df_work = df_work.drop_duplicates(
        subset=['itemid', 'property'],
        keep='last'
    )
    
    # --- Étape 3 : Sélection des propriétés importantes ---
    # On se concentre sur les propriétés les plus utiles pour l'analyse
    key_properties = ['categoryid', 'available', '790']  # 790 = price
    
    df_filtered = df_work[df_work['property'].isin(key_properties)]
    
    # --- Étape 4 : Pivot table ---
    # Transformer property en colonnes
    print("   🔄 Pivot des propriétés en colonnes...")
    df_pivot = df_filtered.pivot_table(
        index='itemid',
        columns='property',
        values='value',
        aggfunc='first'  # Au cas où il reste des doublons
    ).reset_index()
    
    # --- Étape 5 : Nettoyage des colonnes créées ---
    
    # Renommer '790' en 'price' pour plus de clarté
    if '790' in df_pivot.columns:
        df_pivot.rename(columns={'790': 'price_raw'}, inplace=True)
        
        # Extraire le prix numérique (format: "nXXXX.XX")
        print("   💰 Extraction des prix...")
        df_pivot['price'] = df_pivot['price_raw'].str.extract(
            r'n(\d+\.?\d*)'
        )[0].astype(float)
        df_pivot.drop('price_raw', axis=1, inplace=True)
    
    # Convertir categoryid en entier
    if 'categoryid' in df_pivot.columns:
        df_pivot['categoryid'] = pd.to_numeric(
            df_pivot['categoryid'],
            errors='coerce'
        ).astype('Int32')
    
    # Convertir available en entier (0 ou 1)
    if 'available' in df_pivot.columns:
        df_pivot['available'] = pd.to_numeric(
            df_pivot['available'],
            errors='coerce'
        ).astype('Int8')
    
    print(f"\n✅ Transformation terminée:")
    print(f"   Produits: {len(df_pivot):,}")
    print(f"   Colonnes: {list(df_pivot.columns)}")
    
    # Statistiques sur les colonnes créées
    if 'categoryid' in df_pivot.columns:
        pct_cat = (df_pivot['categoryid'].notna().sum() / len(df_pivot) * 100)
        print(f"   Produits avec catégorie: {pct_cat:.1f}%")
    
    if 'available' in df_pivot.columns:
        pct_avail = (df_pivot['available'].notna().sum() / len(df_pivot) * 100)
        print(f"   Produits avec disponibilité: {pct_avail:.1f}%")
    
    if 'price' in df_pivot.columns:
        pct_price = (df_pivot['price'].notna().sum() / len(df_pivot) * 100)
        print(f"   Produits avec prix: {pct_price:.1f}%")
    
    return df_pivot


# =============================================================================
# ÉTAPE 3 : CRÉATION DE NOUVELLES VARIABLES
# =============================================================================

def create_temporal_features(df):
    """
    Crée des variables temporelles à partir du timestamp.
    
    Variables créées :
    - date : date sans l'heure
    - year, month, day : composantes de la date
    - hour : heure de la journée (0-23)
    - day_of_week : jour de la semaine (0=lundi, 6=dimanche)
    - day_name : nom du jour en anglais
    - is_weekend : booléen si c'est le week-end
    - hour_of_day_category : matin/après-midi/soir/nuit
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame avec colonne 'timestamp'
    
    Returns
    -------
    pd.DataFrame
        DataFrame avec nouvelles colonnes temporelles
    """
    print("\n⏰ Création des variables temporelles...")
    
    df_temp = df.copy()
    
    # --- Variables de base ---
    print("   📅 Extraction date/heure...")
    df_temp['date'] = df_temp['timestamp'].dt.date
    df_temp['year'] = df_temp['timestamp'].dt.year
    df_temp['month'] = df_temp['timestamp'].dt.month
    df_temp['day'] = df_temp['timestamp'].dt.day
    df_temp['hour'] = df_temp['timestamp'].dt.hour
    
    # --- Jour de la semaine ---
    print("   📆 Extraction jour de la semaine...")
    df_temp['day_of_week'] = df_temp['timestamp'].dt.dayofweek
    df_temp['day_name'] = df_temp['timestamp'].dt.day_name()
    
    # Week-end (samedi=5, dimanche=6)
    df_temp['is_weekend'] = df_temp['day_of_week'].isin([5, 6])
    
    # --- Période de la journée ---
    print("   🌅 Catégorisation par période du jour...")
    def categorize_hour(hour):
        """Catégorise l'heure en période de la journée."""
        if 6 <= hour < 12:
            return 'Matin'
        elif 12 <= hour < 18:
            return 'Après-midi'
        elif 18 <= hour < 22:
            return 'Soir'
        else:
            return 'Nuit'
    
    df_temp['period_of_day'] = df_temp['hour'].apply(categorize_hour)
    df_temp['period_of_day'] = df_temp['period_of_day'].astype('category')
    
    # --- Semaine de l'année ---
    df_temp['week_of_year'] = df_temp['timestamp'].dt.isocalendar().week
    
    print(f"✅ {len(df_temp.columns) - len(df.columns)} variables temporelles créées")
    
    return df_temp


def create_user_sessions(df, timeout_minutes=30):
    """
    Crée des sessions utilisateur basées sur un timeout d'inactivité.
    
    Une nouvelle session commence quand :
    - C'est le premier événement d'un visiteur, OU
    - Plus de X minutes se sont écoulées depuis le dernier événement
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame events (doit être trié par visitorid et timestamp)
    timeout_minutes : int
        Durée d'inactivité définissant une nouvelle session (défaut: 30 min)
    
    Returns
    -------
    pd.DataFrame
        DataFrame avec colonne 'session_id'
    """
    print(f"\n🔗 Création des sessions utilisateur (timeout: {timeout_minutes} min)...")
    
    df_sess = df.copy()
    
    # --- Étape 1 : Trier par visiteur et temps ---
    df_sess = df_sess.sort_values(['visitorid', 'timestamp'])
    
    # --- Étape 2 : Calculer le temps écoulé depuis le dernier événement ---
    print("   ⏱️  Calcul des délais entre événements...")
    df_sess['time_since_last_event'] = df_sess.groupby('visitorid')[
        'timestamp'
    ].diff()
    
    # --- Étape 3 : Identifier les nouvelles sessions ---
    # Nouvelle session si :
    # - time_since_last_event est NaN (premier événement du visiteur)
    # - time_since_last_event > timeout
    timeout_threshold = timedelta(minutes=timeout_minutes)
    
    df_sess['is_new_session'] = (
        (df_sess['time_since_last_event'].isna()) |
        (df_sess['time_since_last_event'] > timeout_threshold)
    )
    
    # --- Étape 4 : Créer un identifiant de session unique ---
    print("   🆔 Génération des identifiants de session...")
    
    # Numéroter les sessions pour chaque visiteur
    df_sess['session_number'] = df_sess.groupby('visitorid')[
        'is_new_session'
    ].cumsum()
    
    # Créer un ID unique combinant visitorid et numéro de session
    df_sess['session_id'] = (
        df_sess['visitorid'].astype(str) + '_' +
        df_sess['session_number'].astype(str)
    )
    
    # --- Nettoyage : supprimer les colonnes temporaires ---
    df_sess = df_sess.drop(
        columns=['time_since_last_event', 'is_new_session', 'session_number']
    )
    
    # --- Statistiques ---
    n_sessions = df_sess['session_id'].nunique()
    n_visitors = df_sess['visitorid'].nunique()
    sessions_per_visitor = n_sessions / n_visitors
    
    print(f"\n✅ Sessions créées:")
    print(f"   Total sessions: {n_sessions:,}")
    print(f"   Sessions par visiteur: {sessions_per_visitor:.2f}")
    
    return df_sess


def create_event_sequences(df):
    """
    Crée des variables de séquence d'événements par session.
    
    Variables créées :
    - event_rank : rang de l'événement dans la session (1, 2, 3...)
    - is_first_event : booléen si c'est le premier événement
    - is_last_event : booléen si c'est le dernier événement
    - session_length : nombre total d'événements dans la session
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame avec colonne 'session_id'
    
    Returns
    -------
    pd.DataFrame
        DataFrame avec variables de séquence
    """
    print("\n🔢 Création des variables de séquence d'événements...")
    
    df_seq = df.copy()
    
    # --- Rang de l'événement dans la session ---
    print("   📊 Calcul du rang des événements...")
    df_seq['event_rank'] = df_seq.groupby('session_id').cumcount() + 1
    
    # --- Longueur de la session ---
    print("   📏 Calcul de la longueur des sessions...")
    session_lengths = df_seq.groupby('session_id').size()
    df_seq['session_length'] = df_seq['session_id'].map(session_lengths)
    
    # --- Premier et dernier événement ---
    df_seq['is_first_event'] = df_seq['event_rank'] == 1
    df_seq['is_last_event'] = df_seq['event_rank'] == df_seq['session_length']
    
    print(f"✅ Variables de séquence créées")
    
    return df_seq


def create_aggregated_features(df):
    """
    Crée des variables agrégées par utilisateur et par produit.
    
    Par visiteur :
    - n_sessions : nombre de sessions
    - n_events : nombre total d'événements
    - n_products_viewed : nombre de produits consultés
    - has_purchased : si le visiteur a effectué un achat
    
    Par produit :
    - n_views : nombre de vues
    - n_addtocart : nombre d'ajouts au panier
    - n_purchases : nombre d'achats
    - conversion_rate : taux de conversion vue -> achat
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame events avec session_id
    
    Returns
    -------
    tuple
        (user_features, product_features)
    """
    print("\n📊 Création des variables agrégées...")
    
    # =========================================================================
    # FEATURES PAR VISITEUR
    # =========================================================================
    print("   👤 Agrégation par visiteur...")
    
    user_features = df.groupby('visitorid').agg({
        'session_id': 'nunique',      # Nombre de sessions
        'timestamp': 'count',          # Nombre total d'événements
        'itemid': 'nunique'            # Nombre de produits uniques consultés
    }).reset_index()
    
    # Renommer les colonnes
    user_features.columns = [
        'visitorid',
        'n_sessions',
        'n_events',
        'n_unique_products'
    ]
    
    # Visiteur a-t-il effectué un achat ?
    purchasers = df[df['event'] == 'transaction']['visitorid'].unique()
    user_features['has_purchased'] = user_features['visitorid'].isin(
        purchasers
    )
    
    # Nombre d'achats par visiteur
    purchases_per_visitor = df[df['event'] == 'transaction'].groupby(
        'visitorid'
    ).size()
    user_features['n_purchases'] = user_features['visitorid'].map(
        purchases_per_visitor
    ).fillna(0).astype(int)
    
    # Calculer le taux de conversion par visiteur
    user_features['conversion_rate'] = (
        user_features['n_purchases'] / user_features['n_events'] * 100
    )
    
    print(f"      ✓ {len(user_features):,} visiteurs caractérisés")
    
    # =========================================================================
    # FEATURES PAR PRODUIT
    # =========================================================================
    print("   📦 Agrégation par produit...")
    
    # Compter chaque type d'événement par produit
    product_features = df.groupby(['itemid', 'event']).size().unstack(
        fill_value=0
    ).reset_index()
    
    # Renommer pour plus de clarté
    product_features.columns.name = None
    if 'view' in product_features.columns:
        product_features.rename(columns={'view': 'n_views'}, inplace=True)
    if 'addtocart' in product_features.columns:
        product_features.rename(
            columns={'addtocart': 'n_addtocart'},
            inplace=True
        )
    if 'transaction' in product_features.columns:
        product_features.rename(
            columns={'transaction': 'n_purchases'},
            inplace=True
        )
    
    # Calculer les taux de conversion
    if 'n_views' in product_features.columns:
        if 'n_addtocart' in product_features.columns:
            product_features['cart_rate'] = (
                product_features['n_addtocart'] /
                product_features['n_views'] * 100
            )
        
        if 'n_purchases' in product_features.columns:
            product_features['conversion_rate'] = (
                product_features['n_purchases'] /
                product_features['n_views'] * 100
            )
    
    # Nombre de visiteurs uniques par produit
    unique_visitors = df.groupby('itemid')['visitorid'].nunique()
    product_features['n_unique_visitors'] = product_features['itemid'].map(
        unique_visitors
    )
    
    print(f"      ✓ {len(product_features):,} produits caractérisés")
    
    print(f"\n✅ Agrégation terminée")
    
    return user_features, product_features


def compute_category_hierarchy_depth(category_tree):
    """
    Calcule la profondeur de chaque catégorie dans la hiérarchie.
    
    La profondeur = nombre de niveaux jusqu'à la racine.
    Exemple : Racine (profondeur 0) > Catégorie A (1) > Sous-catégorie B (2)
    
    Parameters
    ----------
    category_tree : pd.DataFrame
        DataFrame avec categoryid et parentid
    
    Returns
    -------
    pd.DataFrame
        DataFrame avec colonne 'depth' ajoutée
    """
    print("\n🌳 Calcul de la profondeur des catégories...")
    
    df_cat = category_tree.copy()
    
    # Initialiser la profondeur à 0 pour les catégories racines
    df_cat['depth'] = 0
    
    # Créer un dictionnaire pour un accès rapide
    parent_dict = df_cat.set_index('categoryid')['parentid'].to_dict()
    
    def get_depth(category_id, visited=None):
        """Calcule récursivement la profondeur d'une catégorie."""
        if visited is None:
            visited = set()
        
        # Éviter les boucles infinies
        if category_id in visited:
            return 0
        visited.add(category_id)
        
        # Si pas de parent, c'est une racine (profondeur 0)
        parent_id = parent_dict.get(category_id)
        if pd.isna(parent_id):
            return 0
        
        # Sinon, profondeur = 1 + profondeur du parent
        return 1 + get_depth(int(parent_id), visited)
    
    # Calculer la profondeur pour chaque catégorie
    df_cat['depth'] = df_cat['categoryid'].apply(get_depth)
    
    # Statistiques
    depth_stats = df_cat['depth'].value_counts().sort_index()
    print("\n   Distribution des profondeurs:")
    for depth, count in depth_stats.items():
        print(f"      Niveau {depth}: {count:,} catégories")
    
    print(f"\n✅ Profondeur maximale: {df_cat['depth'].max()}")
    
    return df_cat


# =============================================================================
# ÉTAPE 4 : EXPLORATION ET RÉSUMÉ
# =============================================================================

def generate_data_summary(events_df, user_features, product_features):
    """
    Génère un résumé complet des données après transformation.
    
    Parameters
    ----------
    events_df : pd.DataFrame
        DataFrame events enrichi
    user_features : pd.DataFrame
        Features par utilisateur
    product_features : pd.DataFrame
        Features par produit
    """
    print("\n" + "=" * 70)
    print("📋 RÉSUMÉ DES DONNÉES")
    print("=" * 70 + "\n")
    
    # --- Aperçu général ---
    print("📊 Vue d'ensemble:")
    print(f"   Événements totaux:       {len(events_df):>12,}")
    print(f"   Visiteurs uniques:       {events_df['visitorid'].nunique():>12,}")
    print(f"   Produits uniques:        {events_df['itemid'].nunique():>12,}")
    print(f"   Sessions créées:         {events_df['session_id'].nunique():>12,}")
    
    # --- Période ---
    print(f"\n📅 Période d'observation:")
    print(f"   Du:    {events_df['timestamp'].min()}")
    print(f"   Au:    {events_df['timestamp'].max()}")
    print(f"   Durée: {(events_df['timestamp'].max() - events_df['timestamp'].min()).days} jours")
    
    # --- Distribution des événements ---
    print(f"\n📈 Distribution des événements:")
    event_dist = events_df['event'].value_counts()
    for event_type, count in event_dist.items():
        pct = count / len(events_df) * 100
        print(f"   {event_type:15} {count:>12,}  ({pct:>5.2f}%)")
    
    # --- Métriques utilisateurs ---
    print(f"\n👤 Métriques utilisateurs (moyennes):")
    print(f"   Sessions/utilisateur:    {user_features['n_sessions'].mean():>12.2f}")
    print(f"   Événements/utilisateur:  {user_features['n_events'].mean():>12.2f}")
    print(f"   Produits/utilisateur:    {user_features['n_unique_products'].mean():>12.2f}")
    
    purchasers_pct = user_features['has_purchased'].sum() / len(user_features) * 100
    print(f"   % acheteurs:             {purchasers_pct:>12.2f}%")
    
    # --- Métriques produits ---
    print(f"\n📦 Métriques produits (moyennes):")
    if 'n_views' in product_features.columns:
        print(f"   Vues/produit:            {product_features['n_views'].mean():>12.2f}")
    if 'n_addtocart' in product_features.columns:
        print(f"   Ajouts panier/produit:   {product_features['n_addtocart'].mean():>12.2f}")
    if 'n_purchases' in product_features.columns:
        print(f"   Achats/produit:          {product_features['n_purchases'].mean():>12.2f}")
    if 'conversion_rate' in product_features.columns:
        avg_conv = product_features['conversion_rate'].mean()
        print(f"   Taux de conversion:      {avg_conv:>12.2f}%")
    
    # --- Variables créées ---
    print(f"\n🔧 Variables créées:")
    temporal_vars = ['date', 'hour', 'day_of_week', 'day_name', 
                     'is_weekend', 'period_of_day']
    session_vars = ['session_id', 'event_rank', 'session_length', 
                    'is_first_event', 'is_last_event']
    
    print(f"   Variables temporelles:   {len(temporal_vars)}")
    print(f"   Variables de session:    {len(session_vars)}")
    print(f"   Features utilisateur:    {len(user_features.columns)}")
    print(f"   Features produit:        {len(product_features.columns)}")
    
    print("\n" + "=" * 70 + "\n")


def display_sample_data(events_df, user_features, product_features):
    """
    Affiche des échantillons de données pour vérification.
    
    Parameters
    ----------
    events_df : pd.DataFrame
        DataFrame events enrichi
    user_features : pd.DataFrame
        Features par utilisateur
    product_features : pd.DataFrame
        Features par produit
    """
    print("=" * 70)
    print("🔍 ÉCHANTILLONS DE DONNÉES")
    print("=" * 70 + "\n")
    
    # --- Échantillon events ---
    print("📊 Aperçu des événements (5 premières lignes):")
    display_cols = [
        'timestamp', 'visitorid', 'event', 'itemid',
        'session_id', 'hour', 'day_name', 'period_of_day'
    ]
    available_cols = [col for col in display_cols if col in events_df.columns]
    print(events_df[available_cols].head().to_string(index=False))
    
    # --- Échantillon user features ---
    print(f"\n\n👤 Features utilisateurs (5 premiers):")
    print(user_features.head().to_string(index=False))
    
    # --- Échantillon product features ---
    print(f"\n\n📦 Features produits (5 premiers):")
    print(product_features.head().to_string(index=False))
    
    print("\n" + "=" * 70 + "\n")


# =============================================================================
# ÉTAPE 5 : EXPORT DES DONNÉES
# =============================================================================

def export_cleaned_data(events_df, user_features, product_features,
                        category_tree, output_path='data/clean/'):
    """
    Exporte les DataFrames nettoyés et enrichis.
    
    Fichiers créés :
    - events_enriched.csv : événements avec toutes les variables
    - user_features.csv : agrégations par utilisateur
    - product_features.csv : agrégations par produit
    - category_hierarchy.csv : catégories avec profondeur
    
    Parameters
    ----------
    events_df : pd.DataFrame
        DataFrame events enrichi
    user_features : pd.DataFrame
        Features par utilisateur
    product_features : pd.DataFrame
        Features par produit
    category_tree : pd.DataFrame
        Hiérarchie des catégories
    output_path : str
        Chemin du dossier de sortie
    """
    print("\n💾 Export des données nettoyées...")
    
    # Créer le dossier s'il n'existe pas
    os.makedirs(output_path, exist_ok=True)
    
    # Export avec compression pour économiser l'espace
    print(f"   📁 Création du dossier: {output_path}")
    
    # Events enrichis
    events_file = f'{output_path}events_enriched.csv'
    events_df.to_csv(events_file, index=False)
    print(f"   ✓ {events_file}")
    print(f"      {len(events_df):,} lignes | {len(events_df.columns)} colonnes")
    
    # User features
    user_file = f'{output_path}user_features.csv'
    user_features.to_csv(user_file, index=False)
    print(f"   ✓ {user_file}")
    print(f"      {len(user_features):,} lignes | {len(user_features.columns)} colonnes")
    
    # Product features
    product_file = f'{output_path}product_features.csv'
    product_features.to_csv(product_file, index=False)
    print(f"   ✓ {product_file}")
    print(f"      {len(product_features):,} lignes | {len(product_features.columns)} colonnes")
    
    # Category hierarchy
    cat_file = f'{output_path}category_hierarchy.csv'
    category_tree.to_csv(cat_file, index=False)
    print(f"   ✓ {cat_file}")
    print(f"      {len(category_tree):,} lignes | {len(category_tree.columns)} colonnes")
    
    print(f"\n✅ Export terminé dans: {output_path}")


# =============================================================================
# PIPELINE PRINCIPAL
# =============================================================================

def main():
    """
    Fonction principale orchestrant toute l'analyse exploratoire.
    
    Pipeline complet :
    1. Chargement des données
    2. Nettoyage
    3. Création de variables
    4. Agrégations
    5. Résumé et export
    """
    print("\n" + "=" * 70)
    print("🚀 ANALYSE EXPLORATOIRE - DATASET RETAILROCKET")
    print("=" * 70)
    
    # -------------------------------------------------------------------------
    # ÉTAPE 1 : CHARGEMENT
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("ÉTAPE 1/5 : CHARGEMENT DES DONNÉES")
    print("=" * 70)
    
    events = load_events_data('data/raw/events.csv')
    categories = load_category_tree('data/raw/category_tree.csv')
    # Note: item_properties est optionnel (très volumineux)
    # Décommenter si nécessaire :
    # items = load_item_properties('data/raw/')
    
    # -------------------------------------------------------------------------
    # ÉTAPE 2 : NETTOYAGE
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("ÉTAPE 2/5 : NETTOYAGE DES DONNÉES")
    print("=" * 70)
    
    events_clean = clean_events(events)
    check_missing_values(events_clean, 'Events')
    
    # Nettoyage des catégories
    check_missing_values(categories, 'Categories')
    categories_enriched = compute_category_hierarchy_depth(categories)
    
    # -------------------------------------------------------------------------
    # ÉTAPE 3 : CRÉATION DE VARIABLES
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("ÉTAPE 3/5 : CRÉATION DE NOUVELLES VARIABLES")
    print("=" * 70)
    
    # Variables temporelles
    events_enriched = create_temporal_features(events_clean)
    
    # Sessions utilisateur
    events_enriched = create_user_sessions(
        events_enriched,
        timeout_minutes=30
    )
    
    # Séquences d'événements
    events_enriched = create_event_sequences(events_enriched)
    
    # -------------------------------------------------------------------------
    # ÉTAPE 4 : AGRÉGATIONS
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("ÉTAPE 4/5 : CRÉATION DES FEATURES AGRÉGÉES")
    print("=" * 70)
    
    user_features, product_features = create_aggregated_features(
        events_enriched
    )
    
    # -------------------------------------------------------------------------
    # ÉTAPE 5 : RÉSUMÉ ET EXPORT
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("ÉTAPE 5/5 : RÉSUMÉ ET EXPORT")
    print("=" * 70)
    
    generate_data_summary(events_enriched, user_features, product_features)
    display_sample_data(events_enriched, user_features, product_features)
    
    export_cleaned_data(
        events_enriched,
        user_features,
        product_features,
        categories_enriched,
        output_path='data/clean/'
    )
    
    # -------------------------------------------------------------------------
    # FIN
    # -------------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("✅ ANALYSE EXPLORATOIRE TERMINÉE AVEC SUCCÈS")
    print("=" * 70)
    print("\n📚 Les données sont prêtes pour les analyses avancées!")
    print("💡 Prochaines étapes suggérées:")
    print("   - Visualisations des tendances temporelles")
    print("   - Analyse de cohortes utilisateurs")
    print("   - Modélisation du comportement d'achat")
    print("   - Système de recommandation")
    print("\n")
    
    return events_enriched, user_features, product_features, categories_enriched


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == '__main__':
    # Lancer le pipeline complet
    events_df, users_df, products_df, categories_df = main()
    
    print("✨ Variables disponibles:")
    print("   - events_df: DataFrame des événements enrichis")
    print("   - users_df: Features par utilisateur")
    print("   - products_df: Features par produit")
    print("   - categories_df: Hiérarchie des catégories")
