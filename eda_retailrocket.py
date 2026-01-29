"""
Analyse Exploratoire du Dataset RetailRocket E-commerce
========================================================
Auteur: Data Analyst
Date: 2026-01-28

Ce script effectue une EDA complète du dataset RetailRocket incluant:
- Nettoyage et préparation des données
- Analyses statistiques descriptives
- Analyses comportementales utilisateurs
- Visualisations business
"""

# =============================================================================
# 1. IMPORTS ET CONFIGURATION
# =============================================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings

# Configuration
warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', 100)
pd.set_option('display.float_format', lambda x: f'{x:.2f}')

# Style des graphiques
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (12, 6)
plt.rcParams['font.size'] = 10


# =============================================================================
# 2. CHARGEMENT DES DONNÉES
# =============================================================================

def load_data(data_path='data/raw/'):
    """
    Charge les fichiers CSV du dataset RetailRocket.
    
    Parameters
    ----------
    data_path : str
        Chemin vers le dossier contenant les fichiers raw
        
    Returns
    -------
    dict
        Dictionnaire contenant les DataFrames chargés
    """
    print("📂 Chargement des données...")
    
    # Events - Table principale
    events = pd.read_csv(
        f'{data_path}events.csv',
        dtype={
            'visitorid': 'int32',
            'event': 'category',
            'itemid': 'int32',
            'transactionid': 'float32'
        }
    )
    
    # Category tree - Hiérarchie produits
    category_tree = pd.read_csv(
        f'{data_path}category_tree.csv',
        dtype={
            'categoryid': 'int32',
            'parentid': 'float32'
        }
    )
    
    # Item properties - Métadonnées produits
    print("⏳ Chargement item_properties (peut prendre 1-2 min)...")
    item_props_1 = pd.read_csv(f'{data_path}item_properties_part1.csv')
    item_props_2 = pd.read_csv(f'{data_path}item_properties_part2.csv')
    item_properties = pd.concat([item_props_1, item_props_2], 
                                 ignore_index=True)
    
    print(f"✅ Données chargées:")
    print(f"   - Events: {len(events):,} lignes")
    print(f"   - Category Tree: {len(category_tree):,} lignes")
    print(f"   - Item Properties: {len(item_properties):,} lignes\n")
    
    return {
        'events': events,
        'category_tree': category_tree,
        'item_properties': item_properties
    }


# =============================================================================
# 3. NETTOYAGE ET PRÉPARATION DES DONNÉES
# =============================================================================

def clean_events(events_df):
    """
    Nettoie et prépare le DataFrame events.
    
    - Conversion des timestamps
    - Création de variables temporelles
    - Tri chronologique
    - Validation des types d'événements
    """
    print("🧹 Nettoyage du DataFrame events...")
    
    df = events_df.copy()
    
    # Conversion timestamp (millisecondes -> datetime)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Extraction de variables temporelles
    df['date'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek  # 0=Lundi, 6=Dimanche
    df['day_name'] = df['timestamp'].dt.day_name()
    df['week'] = df['timestamp'].dt.isocalendar().week
    
    # Tri chronologique
    df = df.sort_values('timestamp').reset_index(drop=True)
    
    # Validation des événements
    valid_events = ['view', 'addtocart', 'transaction']
    invalid_events = ~df['event'].isin(valid_events)
    
    if invalid_events.sum() > 0:
        print(f"⚠️  {invalid_events.sum()} événements invalides supprimés")
        df = df[~invalid_events]
    
    print(f"✅ Events nettoyé: {len(df):,} lignes")
    print(f"   Période: {df['date'].min()} → {df['date'].max()}\n")
    
    return df


def process_item_properties(item_props_df):
    """
    Transforme item_properties en format pivot pour faciliter l'analyse.
    
    Extrait les propriétés clés:
    - categoryid
    - available
    - price (si disponible)
    """
    print("🔧 Traitement de item_properties...")
    
    df = item_props_df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Garder la dernière valeur pour chaque propriété par item
    df = df.sort_values('timestamp').drop_duplicates(
        subset=['itemid', 'property'],
        keep='last'
    )
    
    # Pivot sur les propriétés clés
    props_of_interest = ['categoryid', 'available', '790']  # 790=price
    df_filtered = df[df['property'].isin(props_of_interest)]
    
    item_master = df_filtered.pivot_table(
        index='itemid',
        columns='property',
        values='value',
        aggfunc='first'
    ).reset_index()
    
    # Renommer et typer
    if 'categoryid' in item_master.columns:
        item_master['categoryid'] = pd.to_numeric(
            item_master['categoryid'], 
            errors='coerce'
        ).astype('Int32')
    
    if 'available' in item_master.columns:
        item_master['available'] = pd.to_numeric(
            item_master['available'], 
            errors='coerce'
        ).astype('Int8')
    
    if '790' in item_master.columns:
        item_master['price'] = item_master['790'].str.extract(
            r'n(\d+\.?\d*)'
        ).astype(float)
        item_master = item_master.drop('790', axis=1)
    
    print(f"✅ {len(item_master):,} produits avec métadonnées\n")
    
    return item_master


def handle_missing_values(df, strategy='report'):
    """
    Gère les valeurs manquantes selon une stratégie définie.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame à analyser
    strategy : str
        'report' (par défaut) | 'drop' | 'fill'
    """
    print(f"🔍 Analyse des valeurs manquantes (stratégie: {strategy})...")
    
    missing_stats = pd.DataFrame({
        'missing_count': df.isnull().sum(),
        'missing_pct': (df.isnull().sum() / len(df) * 100).round(2),
        'dtype': df.dtypes
    })
    missing_stats = missing_stats[missing_stats['missing_count'] > 0]
    
    if len(missing_stats) > 0:
        print(missing_stats)
        
        if strategy == 'drop':
            # Supprimer colonnes avec >80% manquants
            cols_to_drop = missing_stats[
                missing_stats['missing_pct'] > 80
            ].index.tolist()
            df = df.drop(columns=cols_to_drop)
            print(f"🗑️  Colonnes supprimées: {cols_to_drop}")
            
        elif strategy == 'fill':
            # Stratégie simple: remplir selon le type
            for col in missing_stats.index:
                if df[col].dtype in ['int64', 'float64']:
                    df[col].fillna(df[col].median(), inplace=True)
                else:
                    df[col].fillna('UNKNOWN', inplace=True)
            print("✅ Valeurs manquantes imputées")
    else:
        print("✅ Aucune valeur manquante détectée")
    
    print()
    return df


# =============================================================================
# 4. STATISTIQUES DESCRIPTIVES
# =============================================================================

def descriptive_statistics(events_df):
    """
    Calcule les statistiques descriptives globales du dataset.
    """
    print("="*70)
    print("📊 STATISTIQUES DESCRIPTIVES")
    print("="*70 + "\n")
    
    # Période d'observation
    period_days = (events_df['date'].max() - 
                   events_df['date'].min()).days + 1
    
    print(f"📅 Période d'observation: {period_days} jours\n")
    
    # Distribution des événements
    print("📈 Distribution des événements:")
    event_counts = events_df['event'].value_counts()
    event_pcts = events_df['event'].value_counts(normalize=True) * 100
    
    for event in event_counts.index:
        print(f"   {event:15} {event_counts[event]:>12,} "
              f"({event_pcts[event]:>5.2f}%)")
    
    # Métriques utilisateurs
    print(f"\n👥 Utilisateurs:")
    unique_visitors = events_df['visitorid'].nunique()
    events_per_visitor = len(events_df) / unique_visitors
    
    print(f"   Visiteurs uniques:     {unique_visitors:>12,}")
    print(f"   Événements/visiteur:   {events_per_visitor:>12.2f}")
    
    # Métriques produits
    print(f"\n📦 Produits:")
    unique_items = events_df['itemid'].nunique()
    views_per_item = events_df[events_df['event'] == 'view'].groupby(
        'itemid'
    ).size()
    
    print(f"   Produits uniques:      {unique_items:>12,}")
    print(f"   Vues/produit (moy):    {views_per_item.mean():>12.2f}")
    print(f"   Vues/produit (med):    {views_per_item.median():>12.2f}")
    
    # Métriques transactionnelles
    print(f"\n💰 Transactions:")
    transactions = events_df[events_df['event'] == 'transaction']
    n_transactions = transactions['transactionid'].nunique()
    items_per_transaction = transactions.groupby(
        'transactionid'
    )['itemid'].count()
    
    print(f"   Transactions totales:  {n_transactions:>12,}")
    print(f"   Items/transaction:     {items_per_transaction.mean():>12.2f}")
    
    # Taux de conversion
    views = len(events_df[events_df['event'] == 'view'])
    addtocart = len(events_df[events_df['event'] == 'addtocart'])
    
    conversion_rate = (n_transactions / unique_visitors) * 100
    cart_rate = (addtocart / views) * 100
    checkout_rate = (n_transactions / addtocart) * 100 if addtocart > 0 else 0
    
    print(f"\n🎯 Taux de conversion:")
    print(f"   Visiteur → Transaction: {conversion_rate:>11.2f}%")
    print(f"   Vue → Ajout panier:     {cart_rate:>11.2f}%")
    print(f"   Panier → Transaction:   {checkout_rate:>11.2f}%")
    
    print("\n" + "="*70 + "\n")


def top_products_analysis(events_df, top_n=10):
    """
    Analyse les produits les plus performants.
    """
    print(f"🏆 TOP {top_n} PRODUITS\n")
    
    # Top produits par vues
    top_viewed = events_df[
        events_df['event'] == 'view'
    ]['itemid'].value_counts().head(top_n)
    
    print("📊 Plus consultés:")
    for i, (item_id, count) in enumerate(top_viewed.items(), 1):
        print(f"   {i:2d}. Item {item_id:>7} : {count:>7,} vues")
    
    # Top produits par transactions
    top_sold = events_df[
        events_df['event'] == 'transaction'
    ]['itemid'].value_counts().head(top_n)
    
    print(f"\n💰 Plus vendus:")
    for i, (item_id, count) in enumerate(top_sold.items(), 1):
        print(f"   {i:2d}. Item {item_id:>7} : {count:>7,} ventes")
    
    print()


# =============================================================================
# 5. ANALYSES COMPORTEMENTALES UTILISATEURS
# =============================================================================

def create_user_sessions(events_df, timeout_minutes=30):
    """
    Crée des sessions utilisateur basées sur un timeout d'inactivité.
    
    Parameters
    ----------
    events_df : pd.DataFrame
        DataFrame events nettoyé
    timeout_minutes : int
        Durée d'inactivité définissant une nouvelle session
        
    Returns
    -------
    pd.DataFrame
        DataFrame avec colonne 'session_id'
    """
    print(f"🔗 Création des sessions (timeout: {timeout_minutes}min)...")
    
    df = events_df.sort_values(['visitorid', 'timestamp']).copy()
    
    # Calculer le temps entre événements pour chaque visiteur
    df['time_diff'] = df.groupby('visitorid')['timestamp'].diff()
    
    # Nouvelle session si time_diff > timeout ou nouveau visiteur
    timeout_delta = timedelta(minutes=timeout_minutes)
    df['new_session'] = (
        (df['time_diff'] > timeout_delta) | 
        (df['time_diff'].isnull())
    )
    
    # Créer session_id unique
    df['session_id'] = df.groupby('visitorid')['new_session'].cumsum()
    df['session_id'] = (
        df['visitorid'].astype(str) + '_' + 
        df['session_id'].astype(str)
    )
    
    df = df.drop(columns=['time_diff', 'new_session'])
    
    n_sessions = df['session_id'].nunique()
    sessions_per_user = n_sessions / df['visitorid'].nunique()
    
    print(f"✅ {n_sessions:,} sessions créées")
    print(f"   Sessions/visiteur: {sessions_per_user:.2f}\n")
    
    return df


def analyze_user_behavior(events_df):
    """
    Analyse approfondie du comportement utilisateur.
    """
    print("="*70)
    print("👤 ANALYSES COMPORTEMENTALES UTILISATEURS")
    print("="*70 + "\n")
    
    # Créer sessions
    df = create_user_sessions(events_df)
    
    # Métriques par session
    session_metrics = df.groupby('session_id').agg({
        'timestamp': ['min', 'max'],
        'event': 'count',
        'itemid': 'nunique',
        'visitorid': 'first'
    }).reset_index()
    
    session_metrics.columns = [
        'session_id', 'start_time', 'end_time', 
        'n_events', 'n_unique_items', 'visitorid'
    ]
    
    # Durée de session
    session_metrics['duration_minutes'] = (
        (session_metrics['end_time'] - session_metrics['start_time'])
        .dt.total_seconds() / 60
    )
    
    print("📊 Métriques de session:")
    print(f"   Événements/session (moy):   "
          f"{session_metrics['n_events'].mean():>8.2f}")
    print(f"   Événements/session (med):   "
          f"{session_metrics['n_events'].median():>8.2f}")
    print(f"   Produits/session (moy):     "
          f"{session_metrics['n_unique_items'].mean():>8.2f}")
    print(f"   Durée session (moy):        "
          f"{session_metrics['duration_minutes'].mean():>8.2f} min")
    print(f"   Durée session (med):        "
          f"{session_metrics['duration_minutes'].median():>8.2f} min")
    
    # Parcours d'achat
    print("\n🛒 Analyse du parcours d'achat:")
    
    # Sessions avec transaction
    transactions_by_session = df[
        df['event'] == 'transaction'
    ]['session_id'].unique()
    
    conversion_sessions = df[df['session_id'].isin(transactions_by_session)]
    non_conversion_sessions = df[
        ~df['session_id'].isin(transactions_by_session)
    ]
    
    conv_session_metrics = conversion_sessions.groupby(
        'session_id'
    )['event'].count()
    non_conv_session_metrics = non_conversion_sessions.groupby(
        'session_id'
    )['event'].count()
    
    print(f"   Sessions avec achat:        "
          f"{len(transactions_by_session):>8,} "
          f"({len(transactions_by_session)/len(session_metrics)*100:.2f}%)")
    print(f"   Événements (avec achat):    "
          f"{conv_session_metrics.mean():>8.2f}")
    print(f"   Événements (sans achat):    "
          f"{non_conv_session_metrics.mean():>8.2f}")
    
    # Temps jusqu'à l'achat
    purchase_sessions = df[df['session_id'].isin(transactions_by_session)]
    purchase_times = []
    
    for session in transactions_by_session:
        session_data = purchase_sessions[
            purchase_sessions['session_id'] == session
        ].sort_values('timestamp')
        
        first_event = session_data['timestamp'].iloc[0]
        purchase_event = session_data[
            session_data['event'] == 'transaction'
        ]['timestamp'].iloc[0]
        
        time_to_purchase = (
            (purchase_event - first_event).total_seconds() / 60
        )
        purchase_times.append(time_to_purchase)
    
    if purchase_times:
        print(f"   Temps jusqu'à achat (moy):  "
              f"{np.mean(purchase_times):>8.2f} min")
        print(f"   Temps jusqu'à achat (med):  "
              f"{np.median(purchase_times):>8.2f} min")
    
    # Analyse temporelle
    print("\n⏰ Patterns temporels:")
    hourly_activity = df.groupby('hour').size()
    peak_hour = hourly_activity.idxmax()
    
    daily_activity = df.groupby('day_name').size()
    peak_day = daily_activity.idxmax()
    
    print(f"   Heure de pointe:            {peak_hour:>8}h "
          f"({hourly_activity[peak_hour]:,} événements)")
    print(f"   Jour de pointe:             {peak_day:>8} "
          f"({daily_activity[peak_day]:,} événements)")
    
    print("\n" + "="*70 + "\n")
    
    return df, session_metrics


def funnel_analysis(events_df):
    """
    Analyse du funnel de conversion.
    """
    print("🎯 ANALYSE DU FUNNEL DE CONVERSION\n")
    
    # Visiteurs par étape
    visitors_viewed = events_df[
        events_df['event'] == 'view'
    ]['visitorid'].nunique()
    
    visitors_addtocart = events_df[
        events_df['event'] == 'addtocart'
    ]['visitorid'].nunique()
    
    visitors_purchased = events_df[
        events_df['event'] == 'transaction'
    ]['visitorid'].nunique()
    
    # Affichage du funnel
    print(f"   1. Vue produit:      {visitors_viewed:>10,}  (100.00%)")
    
    if visitors_viewed > 0:
        pct_cart = (visitors_addtocart / visitors_viewed) * 100
        print(f"   2. Ajout panier:     {visitors_addtocart:>10,}  "
              f"({pct_cart:>5.2f}%)  [-{100-pct_cart:.2f}%]")
        
        pct_purchase = (visitors_purchased / visitors_viewed) * 100
        print(f"   3. Transaction:      {visitors_purchased:>10,}  "
              f"({pct_purchase:>5.2f}%)  [-{100-pct_purchase:.2f}%]")
    
    print()


# =============================================================================
# 6. VISUALISATIONS
# =============================================================================

def plot_event_distribution(events_df, save_path='outputs/'):
    """
    Visualise la distribution des types d'événements.
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 5))
    
    # Distribution globale
    event_counts = events_df['event'].value_counts()
    axes[0].bar(event_counts.index, event_counts.values, 
                color=['#3498db', '#e74c3c', '#2ecc71'])
    axes[0].set_title('Distribution des Événements', 
                      fontsize=14, fontweight='bold')
    axes[0].set_ylabel('Nombre d\'événements')
    axes[0].set_xlabel('Type d\'événement')
    
    for i, v in enumerate(event_counts.values):
        axes[0].text(i, v, f'{v:,}', ha='center', va='bottom')
    
    # Distribution temporelle (par jour)
    daily_events = events_df.groupby(['date', 'event']).size().unstack(
        fill_value=0
    )
    daily_events.plot(ax=axes[1], marker='o', linewidth=2)
    axes[1].set_title('Évolution Temporelle des Événements', 
                      fontsize=14, fontweight='bold')
    axes[1].set_ylabel('Nombre d\'événements')
    axes[1].set_xlabel('Date')
    axes[1].legend(title='Événement')
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{save_path}event_distribution.png', dpi=300, 
                bbox_inches='tight')
    print(f"📊 Graphique sauvegardé: event_distribution.png")
    plt.show()


def plot_hourly_heatmap(events_df, save_path='outputs/'):
    """
    Heatmap de l'activité par heure et jour de la semaine.
    """
    hourly_dow = events_df.groupby(['day_of_week', 'hour']).size().unstack(
        fill_value=0
    )
    
    # Renommer les jours
    day_names = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 
                 'Vendredi', 'Samedi', 'Dimanche']
    hourly_dow.index = [day_names[i] for i in hourly_dow.index]
    
    plt.figure(figsize=(16, 6))
    sns.heatmap(hourly_dow, cmap='YlOrRd', annot=False, 
                fmt='d', cbar_kws={'label': 'Nombre d\'événements'})
    plt.title('Heatmap d\'Activité: Jour de la Semaine × Heure', 
              fontsize=14, fontweight='bold')
    plt.xlabel('Heure de la journée')
    plt.ylabel('Jour de la semaine')
    plt.tight_layout()
    plt.savefig(f'{save_path}hourly_heatmap.png', dpi=300, 
                bbox_inches='tight')
    print(f"📊 Graphique sauvegardé: hourly_heatmap.png")
    plt.show()


def plot_funnel(events_df, save_path='outputs/'):
    """
    Visualisation du funnel de conversion.
    """
    visitors_viewed = events_df[
        events_df['event'] == 'view'
    ]['visitorid'].nunique()
    visitors_addtocart = events_df[
        events_df['event'] == 'addtocart'
    ]['visitorid'].nunique()
    visitors_purchased = events_df[
        events_df['event'] == 'transaction'
    ]['visitorid'].nunique()
    
    stages = ['Vue Produit', 'Ajout Panier', 'Transaction']
    values = [visitors_viewed, visitors_addtocart, visitors_purchased]
    colors = ['#3498db', '#e67e22', '#2ecc71']
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Créer l'effet d'entonnoir
    y_positions = [3, 2, 1]
    bar_widths = [val / visitors_viewed for val in values]
    
    for i, (stage, value, width, color) in enumerate(
        zip(stages, values, bar_widths, colors)
    ):
        ax.barh(y_positions[i], width, height=0.6, 
                color=color, alpha=0.8, edgecolor='black')
        
        # Annotations
        retention_pct = (value / visitors_viewed) * 100
        ax.text(width/2, y_positions[i], 
                f'{stage}\n{value:,} visiteurs ({retention_pct:.1f}%)',
                ha='center', va='center', fontweight='bold', fontsize=11)
    
    ax.set_xlim(0, 1.1)
    ax.set_ylim(0.5, 3.5)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    plt.title('Funnel de Conversion E-commerce', 
              fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(f'{save_path}conversion_funnel.png', dpi=300, 
                bbox_inches='tight')
    print(f"📊 Graphique sauvegardé: conversion_funnel.png")
    plt.show()


def plot_session_metrics(session_metrics_df, save_path='outputs/'):
    """
    Visualise les métriques de session.
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Distribution événements par session
    axes[0, 0].hist(session_metrics_df['n_events'], bins=50, 
                    color='#3498db', edgecolor='black', alpha=0.7)
    axes[0, 0].set_title('Distribution: Événements par Session', 
                         fontweight='bold')
    axes[0, 0].set_xlabel('Nombre d\'événements')
    axes[0, 0].set_ylabel('Fréquence')
    axes[0, 0].axvline(session_metrics_df['n_events'].median(), 
                       color='red', linestyle='--', 
                       label=f'Médiane: {session_metrics_df["n_events"].median():.1f}')
    axes[0, 0].legend()
    
    # Distribution durée de session
    duration_filtered = session_metrics_df[
        session_metrics_df['duration_minutes'] < 60
    ]['duration_minutes']
    axes[0, 1].hist(duration_filtered, bins=50, 
                    color='#e74c3c', edgecolor='black', alpha=0.7)
    axes[0, 1].set_title('Distribution: Durée de Session (<60 min)', 
                         fontweight='bold')
    axes[0, 1].set_xlabel('Durée (minutes)')
    axes[0, 1].set_ylabel('Fréquence')
    axes[0, 1].axvline(duration_filtered.median(), 
                       color='blue', linestyle='--', 
                       label=f'Médiane: {duration_filtered.median():.1f} min')
    axes[0, 1].legend()
    
    # Produits uniques par session
    axes[1, 0].hist(session_metrics_df['n_unique_items'], bins=30, 
                    color='#2ecc71', edgecolor='black', alpha=0.7)
    axes[1, 0].set_title('Distribution: Produits Uniques par Session', 
                         fontweight='bold')
    axes[1, 0].set_xlabel('Nombre de produits')
    axes[1, 0].set_ylabel('Fréquence')
    
    # Corrélation événements vs durée
    sample = session_metrics_df[
        session_metrics_df['duration_minutes'] < 60
    ].sample(min(5000, len(session_metrics_df)))
    
    axes[1, 1].scatter(sample['n_events'], 
                       sample['duration_minutes'], 
                       alpha=0.3, s=10, color='#9b59b6')
    axes[1, 1].set_title('Corrélation: Événements × Durée Session', 
                         fontweight='bold')
    axes[1, 1].set_xlabel('Nombre d\'événements')
    axes[1, 1].set_ylabel('Durée (minutes)')
    
    # Ligne de tendance
    z = np.polyfit(sample['n_events'], sample['duration_minutes'], 1)
    p = np.poly1d(z)
    axes[1, 1].plot(sample['n_events'], p(sample['n_events']), 
                    "r--", linewidth=2, label='Tendance')
    axes[1, 1].legend()
    
    plt.tight_layout()
    plt.savefig(f'{save_path}session_metrics.png', dpi=300, 
                bbox_inches='tight')
    print(f"📊 Graphique sauvegardé: session_metrics.png")
    plt.show()


def plot_top_products(events_df, top_n=15, save_path='outputs/'):
    """
    Visualise les produits les plus performants.
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Top produits par vues
    top_viewed = events_df[
        events_df['event'] == 'view'
    ]['itemid'].value_counts().head(top_n)
    
    axes[0].barh(range(len(top_viewed)), top_viewed.values, 
                 color='#3498db')
    axes[0].set_yticks(range(len(top_viewed)))
    axes[0].set_yticklabels([f'Item {x}' for x in top_viewed.index])
    axes[0].invert_yaxis()
    axes[0].set_xlabel('Nombre de vues')
    axes[0].set_title(f'Top {top_n} Produits les Plus Consultés', 
                      fontweight='bold')
    axes[0].grid(axis='x', alpha=0.3)
    
    # Top produits par ventes
    top_sold = events_df[
        events_df['event'] == 'transaction'
    ]['itemid'].value_counts().head(top_n)
    
    axes[1].barh(range(len(top_sold)), top_sold.values, 
                 color='#2ecc71')
    axes[1].set_yticks(range(len(top_sold)))
    axes[1].set_yticklabels([f'Item {x}' for x in top_sold.index])
    axes[1].invert_yaxis()
    axes[1].set_xlabel('Nombre de ventes')
    axes[1].set_title(f'Top {top_n} Produits les Plus Vendus', 
                      fontweight='bold')
    axes[1].grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{save_path}top_products.png', dpi=300, 
                bbox_inches='tight')
    print(f"📊 Graphique sauvegardé: top_products.png")
    plt.show()


# =============================================================================
# 7. PIPELINE PRINCIPAL
# =============================================================================

def run_eda_pipeline(data_path='data/raw/', output_path='outputs/'):
    """
    Exécute le pipeline complet d'analyse exploratoire.
    
    Parameters
    ----------
    data_path : str
        Chemin vers les données brutes
    output_path : str
        Chemin pour sauvegarder les graphiques
    """
    print("\n" + "="*70)
    print("🚀 DÉMARRAGE DE L'ANALYSE EXPLORATOIRE RETAILROCKET")
    print("="*70 + "\n")
    
    # Créer dossier outputs
    import os
    os.makedirs(output_path, exist_ok=True)
    
    # 1. Chargement
    data = load_data(data_path)
    
    # 2. Nettoyage
    events_clean = clean_events(data['events'])
    item_master = process_item_properties(data['item_properties'])
    
    # 3. Gestion des valeurs manquantes
    events_clean = handle_missing_values(events_clean, strategy='report')
    
    # 4. Statistiques descriptives
    descriptive_statistics(events_clean)
    top_products_analysis(events_clean, top_n=10)
    
    # 5. Analyses comportementales
    events_with_sessions, session_metrics = analyze_user_behavior(
        events_clean
    )
    funnel_analysis(events_clean)
    
    # 6. Visualisations
    print("="*70)
    print("📊 GÉNÉRATION DES GRAPHIQUES")
    print("="*70 + "\n")
    
    plot_event_distribution(events_clean, output_path)
    plot_hourly_heatmap(events_clean, output_path)
    plot_funnel(events_clean, output_path)
    plot_session_metrics(session_metrics, output_path)
    plot_top_products(events_clean, top_n=15, save_path=output_path)
    
    # 7. Export des données nettoyées
    print("\n" + "="*70)
    print("💾 EXPORT DES DONNÉES NETTOYÉES")
    print("="*70 + "\n")
    
    clean_path = 'data/clean/'
    os.makedirs(clean_path, exist_ok=True)
    
    events_with_sessions.to_csv(f'{clean_path}events_clean.csv', 
                                 index=False)
    session_metrics.to_csv(f'{clean_path}session_metrics.csv', 
                           index=False)
    item_master.to_csv(f'{clean_path}item_master.csv', index=False)
    
    print(f"✅ Fichiers sauvegardés dans {clean_path}")
    print(f"   - events_clean.csv ({len(events_with_sessions):,} lignes)")
    print(f"   - session_metrics.csv ({len(session_metrics):,} lignes)")
    print(f"   - item_master.csv ({len(item_master):,} lignes)")
    
    print("\n" + "="*70)
    print("✅ ANALYSE EXPLORATOIRE TERMINÉE")
    print("="*70 + "\n")
    
    return {
        'events': events_with_sessions,
        'sessions': session_metrics,
        'items': item_master
    }


# =============================================================================
# 8. EXÉCUTION
# =============================================================================

if __name__ == '__main__':
    # Lancer le pipeline complet
    results = run_eda_pipeline(
        data_path='data/raw/',
        output_path='outputs/'
    )
    
    print("📚 Données disponibles dans le dictionnaire 'results':")
    print("   - results['events']: DataFrame events avec sessions")
    print("   - results['sessions']: Métriques de session")
    print("   - results['items']: Master data produits")
