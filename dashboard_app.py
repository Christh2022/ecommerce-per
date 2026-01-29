"""
Dashboard E-commerce avec Dash (Plotly)
========================================

Tableau de bord interactif pour analyser la performance d'un site e-commerce.
Architecture multi-pages avec KPIs, graphiques interactifs et filtres dynamiques.

Auteur: Data Visualization Specialist
Date: 2026-01-28
"""

# =============================================================================
# IMPORTS
# =============================================================================

import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from dash import dash_table
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json

# Pour le caching (performance)
from flask_caching import Cache


# =============================================================================
# CONFIGURATION APPLICATION
# =============================================================================

# Initialiser l'app Dash avec Bootstrap pour styling moderne
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY, dbc.icons.FONT_AWESOME],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1"}
    ]
)

app.title = "E-commerce Dashboard"

# Configuration du cache pour optimisation performance
cache = Cache(app.server, config={
    'CACHE_TYPE': 'simple',  # ou 'redis' en production
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes
})


# =============================================================================
# CHARGEMENT DES DONNÉES
# =============================================================================

@cache.memoize(timeout=600)
def load_data():
    """
    Charge les données depuis les fichiers CSV nettoyés.
    En production, remplacer par connexion database (PostgreSQL).
    """
    try:
        # Charger les données nettoyées
        events = pd.read_csv('data/clean/events_enriched.csv', parse_dates=['timestamp'])
        user_features = pd.read_csv('data/clean/user_features.csv')
        product_features = pd.read_csv('data/clean/product_features.csv')
        
        return events, user_features, product_features
    except FileNotFoundError:
        # Fallback : générer données de démo
        print("️  Fichiers nettoyés non trouvés, génération données de démo...")
        return generate_demo_data()


def generate_demo_data():
    """
    Génère des données de démonstration pour tester le dashboard.
    À remplacer par vraies données en production.
    """
    # Générer 10000 événements sur 30 jours
    n_events = 10000
    n_users = 1000
    n_products = 200
    
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    
    events = pd.DataFrame({
        'timestamp': np.random.choice(dates, n_events),
        'visitorid': np.random.randint(1, n_users, n_events),
        'event': np.random.choice(['view', 'addtocart', 'transaction'], 
                                   n_events, p=[0.85, 0.10, 0.05]),
        'itemid': np.random.randint(1, n_products, n_events),
        'session_id': np.random.randint(1, n_events//3, n_events),
    })
    
    # Features utilisateurs (simplifiées)
    user_features = pd.DataFrame({
        'visitorid': range(1, n_users),
        'n_sessions': np.random.randint(1, 10, n_users-1),
        'n_events': np.random.randint(5, 50, n_users-1),
        'has_purchased': np.random.choice([True, False], n_users-1, p=[0.3, 0.7])
    })
    
    # Features produits (simplifiées)
    product_features = pd.DataFrame({
        'itemid': range(1, n_products),
        'n_views': np.random.randint(10, 500, n_products-1),
        'n_purchases': np.random.randint(0, 50, n_products-1)
    })
    product_features['conversion_rate'] = (
        product_features['n_purchases'] / product_features['n_views'] * 100
    )
    
    return events, user_features, product_features


# =============================================================================
# CALCUL DES KPIs
# =============================================================================

def calculate_kpis(events_df, start_date=None, end_date=None):
    """
    Calcule les KPIs principaux pour la période sélectionnée.
    
    Returns
    -------
    dict
        Dictionnaire contenant tous les KPIs
    """
    # Filtrer par période si spécifiée
    if start_date and end_date:
        mask = (events_df['timestamp'] >= start_date) & (events_df['timestamp'] <= end_date)
        df = events_df[mask]
    else:
        df = events_df
    
    # KPIs de base
    n_visitors = df['visitorid'].nunique()
    n_sessions = df['session_id'].nunique() if 'session_id' in df.columns else 0
    n_views = len(df[df['event'] == 'view'])
    n_addtocart = len(df[df['event'] == 'addtocart'])
    n_transactions = len(df[df['event'] == 'transaction'])
    
    # Taux de conversion
    conversion_rate = (n_transactions / n_visitors * 100) if n_visitors > 0 else 0
    cart_rate = (n_addtocart / n_views * 100) if n_views > 0 else 0
    abandon_rate = ((n_addtocart - n_transactions) / n_addtocart * 100) if n_addtocart > 0 else 0
    
    # AOV (simulé ici, en production utiliser vraies données prix)
    aov = np.random.uniform(40, 60)  # À remplacer par vraie logique
    
    # Revenus (simulés)
    revenue = n_transactions * aov
    
    return {
        'revenue': revenue,
        'conversion_rate': conversion_rate,
        'sessions': n_sessions,
        'aov': aov,
        'visitors': n_visitors,
        'transactions': n_transactions,
        'cart_rate': cart_rate,
        'abandon_rate': abandon_rate,
        'views': n_views,
        'addtocart': n_addtocart
    }


# =============================================================================
# COMPOSANTS UI RÉUTILISABLES
# =============================================================================

def create_kpi_card(title, value="Loading...", delta=None, icon="fa-chart-line", color="primary", id=None):
    """
    Crée une carte KPI stylisée avec valeur et évolution.
    
    Parameters
    ----------
    title : str
        Titre du KPI
    value : str
        Valeur principale à afficher
    delta : str, optional
        Évolution (ex: "+12.5%")
    icon : str
        Classe icon FontAwesome
    color : str
        Couleur Bootstrap (primary, success, danger, warning)
    id : str, optional
        ID unique pour la carte (pour callbacks dynamiques)
    """
    # Déterminer couleur du delta
    delta_color = "success"if delta and "+"in str(delta) else "danger"
    delta_icon = "▲"if delta and "+"in str(delta) else "▼"if delta else ""
    
    card = dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"fas {icon} fa-2x text-{color}"),
            ], className="text-end"),
            html.H6(title, className="text-muted text-uppercase mb-2"),
            html.H3(value, className="mb-0 font-weight-bold"),
            html.P([
                html.Span(f"{delta_icon} {delta}", className=f"text-{delta_color}")
            ], className="mb-0 mt-2") if delta else html.Div()
        ])
    ], className="shadow-sm mb-3")
    
    return card


def create_filter_section(min_date=None, max_date=None):
    """
    Crée la section de filtres globaux (date, catégorie, device).
    """
    # Utiliser les dates des données ou valeurs par défaut
    if min_date is None or max_date is None:
        max_date = datetime.now().date()
        min_date = (datetime.now() - timedelta(days=30)).date()
    
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                # Filtre Date Range
                dbc.Col([
                    html.Label("Période", className="fw-bold"),
                    dcc.DatePickerRange(
                        id='date-filter',
                        start_date=min_date,
                        end_date=max_date,
                        min_date_allowed=min_date,
                        max_date_allowed=max_date,
                        display_format='DD/MM/YYYY',
                        className="w-100"
                    )
                ], md=4),
                
                # Filtre Device
                dbc.Col([
                    html.Label("Device", className="fw-bold"),
                    dcc.Dropdown(
                        id='device-filter',
                        options=[
                            {'label': 'Tous', 'value': 'all'},
                            {'label': 'Desktop', 'value': 'desktop'},
                            {'label': 'Mobile', 'value': 'mobile'},
                            {'label': 'Tablet', 'value': 'tablet'}
                        ],
                        value='all',
                        clearable=False
                    )
                ], md=4),
                
                # Bouton Refresh
                dbc.Col([
                    html.Label("Actions", className="fw-bold"),
                    html.Div([
                        dbc.Button(
                            [html.I(className="fas fa-sync-alt me-2"), "Actualiser"],
                            id='refresh-button',
                            color="primary",
                            className="w-100"
                        )
                    ])
                ], md=4)
            ])
        ])
    ], className="mb-4 shadow-sm")


# =============================================================================
# PAGE 1 : OVERVIEW
# =============================================================================

def create_overview_page():
    """
    Page principale avec vue d'ensemble des KPIs.
    """
    # Charger les données et calculer les KPIs initiaux
    events, users, products = load_data()
    kpis = calculate_kpis(events)
    
    # Obtenir les dates min/max des données
    min_date = events['timestamp'].min().date()
    max_date = events['timestamp'].max().date()
    
    return html.Div([
        html.H2("Vue d'Ensemble", className="mb-4"),
        
        # Filtres
        create_filter_section(min_date, max_date),
        
        # KPI Cards Row
        dbc.Row([
            dbc.Col(
                html.Div([
                    create_kpi_card(
                        "Revenus",
                        f"{kpis['revenue']:,.0f}€",
                        delta="+12.5%",
                        icon="fa-euro-sign",
                        color="success"
                    )
                ], id="kpi-revenue")
            , md=3),
            dbc.Col(
                html.Div([
                    create_kpi_card(
                        "Taux de Conversion",
                        f"{kpis['conversion_rate']:.2f}%",
                        delta="+0.3%",
                        icon="fa-chart-line",
                        color="primary"
                    )
                ], id="kpi-conversion")
            , md=3),
            dbc.Col(
                html.Div([
                    create_kpi_card(
                        "Sessions",
                        f"{kpis['sessions']:,}",
                        delta="-5.2%",
                        icon="fa-users",
                        color="info"
                    )
                ], id="kpi-sessions")
            , md=3),
            dbc.Col(
                html.Div([
                    create_kpi_card(
                        "Panier Moyen",
                        f"{kpis['aov']:.2f}€",
                        delta="+8.1%",
                        icon="fa-shopping-cart",
                        color="warning"
                    )
                ], id="kpi-aov")
            , md=3)
        ], className="mb-4"),
        
        # Graphique Principal
        dbc.Card([
            dbc.CardHeader(html.H5("Évolution des Revenus et Conversion")),
            dbc.CardBody([
                dcc.Graph(id='revenue-trend-graph', config={'displayModeBar': False})
            ])
        ], className="mb-4 shadow-sm"),
        
        # Row 2 graphiques côte à côte
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Funnel de Conversion")),
                    dbc.CardBody([
                        dcc.Graph(id='funnel-graph', config={'displayModeBar': False})
                    ])
                ], className="shadow-sm")
            ], md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Performance par Device")),
                    dbc.CardBody([
                        dcc.Graph(id='device-graph', config={'displayModeBar': False})
                    ])
                ], className="shadow-sm")
            ], md=6)
        ])
    ])


# =============================================================================
# PAGE 2 : PERFORMANCE
# =============================================================================

def create_performance_page():
    """
    Page d'analyse approfondie des performances.
    """
    # Charger les données pour obtenir les dates
    events, users, products = load_data()
    min_date = events['timestamp'].min().date()
    max_date = events['timestamp'].max().date()
    
    return html.Div([
        html.H2("Analyse Performance", className="mb-4"),
        
        create_filter_section(min_date, max_date),
        
        # Graphiques multiples
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Évolution Multi-Métriques")),
                    dbc.CardBody([
                        dcc.Graph(id='multi-metrics-graph')
                    ])
                ], className="shadow-sm mb-4")
            ], md=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Heatmap Activité (Jour × Heure)")),
                    dbc.CardBody([
                        dcc.Graph(id='heatmap-activity')
                    ])
                ], className="shadow-sm mb-4")
            ], md=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Répartition des Types d'Événements")),
                    dbc.CardBody([
                        dcc.Graph(id='events-distribution-graph')
                    ])
                ], className="shadow-sm")
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Tendance Hebdomadaire")),
                    dbc.CardBody([
                        dcc.Graph(id='weekly-trend-graph')
                    ])
                ], className="shadow-sm")
            ], md=6)
        ])
    ])


# =============================================================================
# PAGE 3 : USERS
# =============================================================================

def create_users_page():
    """
    Page analyse comportement utilisateurs.
    """
    # Charger les données pour obtenir les dates
    events, users, products = load_data()
    min_date = events['timestamp'].min().date()
    max_date = events['timestamp'].max().date()
    
    return html.Div([
        html.H2("Analyse Utilisateurs", className="mb-4"),
        
        create_filter_section(min_date, max_date),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Distribution Engagement")),
                    dbc.CardBody([
                        dcc.Graph(id='user-engagement-graph')
                    ])
                ], className="shadow-sm mb-4")
            ], md=6),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Nouveaux vs Récurrents")),
                    dbc.CardBody([
                        dcc.Graph(id='user-type-graph')
                    ])
                ], className="shadow-sm mb-4")
            ], md=6)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Taux de Conversion par Segment")),
                    dbc.CardBody([
                        dcc.Graph(id='conversion-segment-graph')
                    ])
                ], className="shadow-sm")
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Activité par Jour de la Semaine")),
                    dbc.CardBody([
                        dcc.Graph(id='user-activity-weekday-graph')
                    ])
                ], className="shadow-sm")
            ], md=6)
        ])
    ])


# =============================================================================
# PAGE 4 : PRODUCTS
# =============================================================================

def create_products_page():
    """
    Page analyse performance catalogue produits.
    """
    # Charger les données pour obtenir les dates
    events, users, products = load_data()
    min_date = events['timestamp'].min().date()
    max_date = events['timestamp'].max().date()
    
    return html.Div([
        html.H2("Analyse Produits", className="mb-4"),
        
        create_filter_section(min_date, max_date),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Top 20 Produits")),
                    dbc.CardBody([
                        dcc.Graph(id='top-products-graph')
                    ])
                ], className="shadow-sm mb-4")
            ], md=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("� Produits Haute Performance (Top Conv.)")),
                    dbc.CardBody([
                        dcc.Graph(id='top-conversion-products-graph')
                    ])
                ], className="shadow-sm mb-4")
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Matrice Performance (Vues × Conv.)")),
                    dbc.CardBody([
                        dcc.Graph(id='products-matrix-graph')
                    ])
                ], className="shadow-sm mb-4")
            ], md=6)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Analyse Comparative Produits")),
                    dbc.CardBody([
                        dcc.Graph(id='products-comparison-graph')
                    ])
                ], className="shadow-sm")
            ], md=12)
        ])
    ])


# =============================================================================
# PAGE 5 : FUNNEL
# =============================================================================

def create_funnel_page():
    """
    Page analyse détaillée du funnel de conversion.
    """
    # Charger les données pour obtenir les dates
    events, users, products = load_data()
    min_date = events['timestamp'].min().date()
    max_date = events['timestamp'].max().date()
    
    return html.Div([
        html.H2("Analyse Funnel", className="mb-4"),
        
        create_filter_section(min_date, max_date),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Funnel de Conversion Détaillé")),
                    dbc.CardBody([
                        dcc.Graph(id='detailed-funnel-graph')
                    ])
                ], className="shadow-sm mb-4")
            ], md=12)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Temps Moyen par Étape")),
                    dbc.CardBody([
                        dcc.Graph(id='funnel-time-graph')
                    ])
                ], className="shadow-sm mb-4")
            ], md=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Taux de Drop-off par Étape")),
                    dbc.CardBody([
                        dcc.Graph(id='funnel-dropoff-graph')
                    ])
                ], className="shadow-sm mb-4")
            ], md=6)
        ]),
        
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Évolution du Funnel (7 derniers jours)")),
                    dbc.CardBody([
                        dcc.Graph(id='funnel-evolution-graph')
                    ])
                ], className="shadow-sm mb-4")
            ], md=12)
        ]),
        
        # Recommandations automatiques
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H6("Recommandations")),
                    dbc.CardBody(id='recommendations-section')
                ], className="shadow-sm")
            ], md=12)
        ])
    ])


# =============================================================================
# PAGE 6 : A/B TESTS
# =============================================================================

def load_ab_test_results():
    """
    Charge les résultats des tests A/B depuis le fichier JSON.
    """
    try:
        with open('data/clean/ab_test_results.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Retourner des données de démonstration si fichier absent ou corrompu
        return {
            'test_name': 'Aucun test disponible',
            'test_date': datetime.now().strftime('%Y-%m-%d'),
            'duration_days': 0,
            'group_A': {'name': 'Contrôle', 'n_users': 0, 'n_conversions': 0, 'conversion_rate': 0},
            'group_B': {'name': 'Test', 'n_users': 0, 'n_conversions': 0, 'conversion_rate': 0},
            'statistics': {
                'absolute_lift': 0, 'relative_lift': 0, 'z_score': 0,
                'p_value': 1.0, 'significant': False, 'ci_lower': 0, 'ci_upper': 0, 'power': 0
            },
            'business_impact': {
                'monthly_users': 0, 'additional_conversions_month': 0,
                'additional_revenue_month': 0, 'additional_revenue_year': 0,
                'roi_percent': 0, 'payback_months': 0
            }
        }


def create_abtests_page():
    """
    Page dédiée aux résultats des tests A/B.
    """
    # Charger les résultats
    results = load_ab_test_results()
    
    # Déterminer la couleur du badge de significativité
    if results['statistics']['significant']:
        badge_color = "success"
        badge_text = "Statistiquement Significatif"
    else:
        badge_color = "warning"
        badge_text = "️ Non Significatif"
    
    return html.Div([
        html.H2("Tests A/B", className="mb-4"),
        
        # Section Simulation
        dbc.Card([
            dbc.CardHeader(html.H5("Nouvelle Simulation A/B Test")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Label("Nom du Test", className="fw-bold"),
                        dbc.Input(id='sim-test-name', type='text', 
                                 placeholder='Ex: Checkout simplifié', value='Test Simulation')
                    ], md=6),
                    dbc.Col([
                        html.Label("Durée (jours)", className="fw-bold"),
                        dbc.Input(id='sim-duration', type='number', value=14, min=7, max=90)
                    ], md=3),
                    dbc.Col([
                        html.Label("Lift Attendu (%)", className="fw-bold"),
                        dbc.Input(id='sim-lift', type='number', value=15, min=1, max=100, step=1)
                    ], md=3)
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        html.Label("Groupe A - Nom", className="fw-bold"),
                        dbc.Input(id='sim-group-a-name', type='text', value='Contrôle')
                    ], md=3),
                    dbc.Col([
                        html.Label("Groupe A - Taux de base (%)", className="fw-bold"),
                        dbc.Input(id='sim-group-a-rate', type='number', value=3.5, min=0.1, max=50, step=0.1)
                    ], md=3),
                    dbc.Col([
                        html.Label("Groupe B - Nom", className="fw-bold"),
                        dbc.Input(id='sim-group-b-name', type='text', value='Variante')
                    ], md=3),
                    dbc.Col([
                        html.Label("Taille échantillon (par groupe)", className="fw-bold"),
                        dbc.Input(id='sim-sample-size', type='number', value=500, min=100, max=10000, step=50)
                    ], md=3)
                ], className="mb-3"),
                
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "Lancer la Simulation",
                            id='run-simulation-btn',
                            color='primary',
                            size='lg',
                            className='w-100'
                        )
                    ], md=12)
                ]),
                
                html.Div(id='simulation-status', className='mt-3')
            ])
        ], className="mb-4 shadow-sm"),
        
        # Divider
        html.Hr(),
        html.H3("Résultats du Dernier Test", className="mb-3"),
        
        # En-tête du test
        dbc.Alert([
            html.H4(results['test_name'], className="mb-2"),
            html.P([
                html.Strong("Date: "), results['test_date'], "| ",
                html.Strong("Durée: "), f"{results['duration_days']} jours"
            ], className="mb-0")
        ], color="info"),
        
        # KPI Cards comparatifs
        dbc.Row([
            # Groupe A
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Groupe A - "+ results['group_A']['name'], className="bg-secondary text-white"),
                    dbc.CardBody([
                        html.H3(f"{results['group_A']['conversion_rate']:.2%}", className="text-secondary"),
                        html.P(f"Utilisateurs: {results['group_A']['n_users']:,}", className="mb-1"),
                        html.P(f"Conversions: {results['group_A']['n_conversions']:,}", className="mb-0")
                    ])
                ], className="shadow-sm")
            ], md=4),
            
            # Lift
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Lift Observé", className="bg-primary text-white"),
                    dbc.CardBody([
                        html.H3(f"{results['statistics']['relative_lift']:+.1f}%", 
                               className="text-primary"),
                        html.P(f"Absolu: {results['statistics']['absolute_lift']:+.2%}", className="mb-1"),
                        dbc.Badge(badge_text, color=badge_color, className="mt-2")
                    ])
                ], className="shadow-sm")
            ], md=4),
            
            # Groupe B
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Groupe B - "+ results['group_B']['name'], className="bg-success text-white"),
                    dbc.CardBody([
                        html.H3(f"{results['group_B']['conversion_rate']:.2%}", className="text-success"),
                        html.P(f"Utilisateurs: {results['group_B']['n_users']:,}", className="mb-1"),
                        html.P(f"Conversions: {results['group_B']['n_conversions']:,}", className="mb-0")
                    ])
                ], className="shadow-sm")
            ], md=4),
        ], className="mb-4"),
        
        # Graphiques
        dbc.Row([
            # Graphique comparaison taux
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Comparaison Taux de Conversion")),
                    dbc.CardBody([
                        dcc.Graph(id='ab-conversion-comparison')
                    ])
                ], className="shadow-sm")
            ], md=6),
            
            # Graphique intervalle de confiance
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Intervalle de Confiance (95%)")),
                    dbc.CardBody([
                        dcc.Graph(id='ab-confidence-interval')
                    ])
                ], className="shadow-sm")
            ], md=6),
        ], className="mb-4"),
        
        # Statistiques détaillées
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Statistiques Détaillées")),
                    dbc.CardBody([
                        dbc.Table([
                            html.Tbody([
                                html.Tr([
                                    html.Td("Z-score", className="fw-bold"),
                                    html.Td(f"{results['statistics']['z_score']:.3f}")
                                ]),
                                html.Tr([
                                    html.Td("P-value", className="fw-bold"),
                                    html.Td(f"{results['statistics']['p_value']:.4f}")
                                ]),
                                html.Tr([
                                    html.Td("Intervalle de Confiance", className="fw-bold"),
                                    html.Td(f"[{results['statistics']['ci_lower']:+.2%}, {results['statistics']['ci_upper']:+.2%}]")
                                ]),
                                html.Tr([
                                    html.Td("Puissance Statistique", className="fw-bold"),
                                    html.Td(f"{results['statistics']['power']:.1%}")
                                ])
                            ])
                        ], bordered=True, hover=True, striped=True)
                    ])
                ], className="shadow-sm")
            ], md=6),
            
            # Impact business
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Impact Business Estimé")),
                    dbc.CardBody([
                        dbc.Table([
                            html.Tbody([
                                html.Tr([
                                    html.Td("Conversions additionnelles/mois", className="fw-bold"),
                                    html.Td(f"{results['business_impact']['additional_conversions_month']:.0f}")
                                ]),
                                html.Tr([
                                    html.Td("Revenus additionnels/mois", className="fw-bold"),
                                    html.Td(f"{results['business_impact']['additional_revenue_month']:,.0f}€", 
                                           className="text-success")
                                ]),
                                html.Tr([
                                    html.Td("Revenus additionnels/an", className="fw-bold"),
                                    html.Td(f"{results['business_impact']['additional_revenue_year']:,.0f}€",
                                           className="text-success fw-bold")
                                ]),
                                html.Tr([
                                    html.Td("ROI", className="fw-bold"),
                                    html.Td(f"{results['business_impact']['roi_percent']:.0f}%")
                                ])
                            ])
                        ], bordered=True, hover=True, striped=True)
                    ])
                ], className="shadow-sm")
            ], md=6)
        ], className="mb-4"),
        
        # Recommandations
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Recommandations")),
                    dbc.CardBody([
                        html.Div(id='ab-recommendations')
                    ])
                ], className="shadow-sm")
            ], md=12)
        ])
    ])


# =============================================================================
# LAYOUT PRINCIPAL
# =============================================================================

# Header
header = dbc.Navbar(
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.NavbarBrand("E-commerce Dashboard", className="ms-2", style={"fontSize": "20px", "fontWeight": "bold"})
            ], width="auto"),
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-bell me-3", style={"fontSize": "18px", "cursor": "pointer"}),
                    html.I(className="fas fa-user-circle", style={"fontSize": "18px", "cursor": "pointer"})
                ], className="d-flex align-items-center")
            ], width="auto", className="ms-auto")
        ], align="center", className="w-100")
    ], fluid=True),
    color="dark",
    dark=True,
    sticky="top",
    style={"height": "60px"}
)

# Sidebar
sidebar = html.Div([
    html.Div([
        html.H5("Navigation", className="text-center mb-4", style={"color": "#fff", "fontWeight": "bold"}),
        html.Hr(style={"borderColor": "rgba(255,255,255,0.2)"}),
        dbc.Nav([
            dbc.NavLink([
                html.I(className="fas fa-home me-2"),
                html.Span("Overview")
            ], href="/", active="exact", style={
                "color": "rgba(255,255,255,0.7)",
                "padding": "12px 20px",
                "marginBottom": "8px",
                "borderRadius": "8px",
                "display": "flex",
                "alignItems": "center"
            }),
            dbc.NavLink([
                html.I(className="fas fa-chart-line me-2"),
                html.Span("Performance")
            ], href="/performance", active="exact", style={
                "color": "rgba(255,255,255,0.7)",
                "padding": "12px 20px",
                "marginBottom": "8px",
                "borderRadius": "8px",
                "display": "flex",
                "alignItems": "center"
            }),
            dbc.NavLink([
                html.I(className="fas fa-users me-2"),
                html.Span("Users")
            ], href="/users", active="exact", style={
                "color": "rgba(255,255,255,0.7)",
                "padding": "12px 20px",
                "marginBottom": "8px",
                "borderRadius": "8px",
                "display": "flex",
                "alignItems": "center"
            }),
            dbc.NavLink([
                html.I(className="fas fa-box me-2"),
                html.Span("Products")
            ], href="/products", active="exact", style={
                "color": "rgba(255,255,255,0.7)",
                "padding": "12px 20px",
                "marginBottom": "8px",
                "borderRadius": "8px",
                "display": "flex",
                "alignItems": "center"
            }),
            dbc.NavLink([
                html.I(className="fas fa-filter me-2"),
                html.Span("Funnel")
            ], href="/funnel", active="exact", style={
                "color": "rgba(255,255,255,0.7)",
                "padding": "12px 20px",
                "marginBottom": "8px",
                "borderRadius": "8px",
                "display": "flex",
                "alignItems": "center"
            }),
            dbc.NavLink([
                html.I(className="fas fa-flask me-2"),
                html.Span("A/B Tests")
            ], href="/abtests", active="exact", style={
                "color": "rgba(255,255,255,0.7)",
                "padding": "12px 20px",
                "marginBottom": "8px",
                "borderRadius": "8px",
                "display": "flex",
                "alignItems": "center"
            }),
        ], vertical=True, pills=True)
    ], style={
        "padding": "20px",
        "height": "100vh",
        "position": "fixed",
        "top": "60px",
        "left": "0",
        "width": "250px",
        "backgroundColor": "#1a1a1a",
        "overflowY": "auto",
        "boxShadow": "2px 0 5px rgba(0,0,0,0.3)"
    })
], id="sidebar")

# Layout principal avec header, sidebar et contenu
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    header,
    html.Div([
        sidebar,
        html.Div([
            dbc.Container(id='page-content', fluid=True, style={"padding": "20px"})
        ], style={
            "marginLeft": "250px",
            "marginTop": "60px",
            "minHeight": "calc(100vh - 60px)"
        })
    ])
])


# =============================================================================
# CALLBACKS - ROUTING
# =============================================================================

@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    """Route vers la bonne page selon l'URL."""
    if pathname == '/performance':
        return create_performance_page()
    elif pathname == '/users':
        return create_users_page()
    elif pathname == '/products':
        return create_products_page()
    elif pathname == '/funnel':
        return create_funnel_page()
    elif pathname == '/abtests':
        return create_abtests_page()
    else:
        return create_overview_page()


# =============================================================================
# CALLBACKS - MISE À JOUR KPIs
# =============================================================================

@app.callback(
    [Output('kpi-revenue', 'children'),
     Output('kpi-conversion', 'children'),
     Output('kpi-sessions', 'children'),
     Output('kpi-aov', 'children')],
    [Input('date-filter', 'start_date'),
     Input('date-filter', 'end_date'),
     Input('device-filter', 'value'),
     Input('refresh-button', 'n_clicks')]
)
def update_kpis(start_date, end_date, device, n_clicks):
    """
    Met à jour les KPI cards en fonction des filtres.
    """
    # Charger données
    events, users, products = load_data()
    
    # Calculer KPIs
    kpis = calculate_kpis(events, start_date, end_date)
    
    # Formater les cards
    revenue_card = [create_kpi_card(
        "Revenus",
        f"{kpis['revenue']:,.0f}€",
        delta="+12.5%",
        icon="fa-euro-sign",
        color="success"
    )]
    
    conversion_card = [create_kpi_card(
        "Taux de Conversion",
        f"{kpis['conversion_rate']:.2f}%",
        delta="+0.3%",
        icon="fa-chart-line",
        color="primary"
    )]
    
    sessions_card = [create_kpi_card(
        "Sessions",
        f"{kpis['sessions']:,}",
        delta="-5.2%",
        icon="fa-users",
        color="info"
    )]
    
    aov_card = [create_kpi_card(
        "Panier Moyen",
        f"{kpis['aov']:.2f}€",
        delta="+8.1%",
        icon="fa-shopping-cart",
        color="warning"
    )]
    
    return revenue_card, conversion_card, sessions_card, aov_card


# =============================================================================
# CALLBACKS - GRAPHIQUES
# =============================================================================

@app.callback(
    Output('revenue-trend-graph', 'figure'),
    [Input('date-filter', 'start_date'),
     Input('date-filter', 'end_date')]
)
def update_revenue_trend(start_date, end_date):
    """
    Graphique évolution revenus avec conversion en ligne secondaire.
    """
    # Charger données
    events, _, _ = load_data()
    
    # Filtrer par dates
    mask = (events['timestamp'] >= start_date) & (events['timestamp'] <= end_date)
    df = events[mask]
    
    # Agréger par jour
    daily = df.groupby(df['timestamp'].dt.date).agg({
        'event': 'count',
        'visitorid': 'nunique'
    }).reset_index()
    daily.columns = ['date', 'events', 'visitors']
    
    # Simuler revenus (en production, utiliser vraies données)
    daily['revenue'] = np.random.uniform(3000, 6000, len(daily))
    daily['conversion'] = np.random.uniform(1.5, 3.5, len(daily))
    
    # Créer figure
    fig = go.Figure()
    
    # Barres revenus
    fig.add_trace(go.Bar(
        x=daily['date'],
        y=daily['revenue'],
        name='Revenus (€)',
        marker_color='#2E86C1',
        yaxis='y'
    ))
    
    # Ligne conversion
    fig.add_trace(go.Scatter(
        x=daily['date'],
        y=daily['conversion'],
        name='Taux Conversion (%)',
        mode='lines+markers',
        line=dict(color='#E74C3C', width=3),
        yaxis='y2'
    ))
    
    # Layout
    fig.update_layout(
        title="Évolution Quotidienne",
        xaxis_title="Date",
        yaxis=dict(title="Revenus (€)", side='left'),
        yaxis2=dict(title="Conversion (%)", overlaying='y', side='right'),
        hovermode='x unified',
        template='plotly_dark',
        height=400
    )
    
    return fig


@app.callback(
    Output('funnel-graph', 'figure'),
    [Input('date-filter', 'start_date'),
     Input('date-filter', 'end_date')]
)
def update_funnel(start_date, end_date):
    """
    Graphique funnel de conversion.
    """
    events, _, _ = load_data()
    
    # Calculer métriques funnel
    mask = (events['timestamp'] >= start_date) & (events['timestamp'] <= end_date)
    df = events[mask]
    
    n_views = len(df[df['event'] == 'view'])
    n_cart = len(df[df['event'] == 'addtocart'])
    n_purchase = len(df[df['event'] == 'transaction'])
    
    fig = go.Figure(go.Funnel(
        y=['Vues Produit', 'Ajout Panier', 'Transaction'],
        x=[n_views, n_cart, n_purchase],
        textposition="inside",
        textinfo="value+percent initial",
        marker=dict(color=['#3498db', '#f39c12', '#2ecc71'])
    ))
    
    fig.update_layout(
        height=300,
        template='plotly_dark',
        showlegend=False
    )
    
    return fig


@app.callback(
    Output('device-graph', 'figure'),
    [Input('date-filter', 'start_date'),
     Input('date-filter', 'end_date')]
)
def update_device_chart(start_date, end_date):
    """
    Graphique performance par device (pie chart).
    """
    # Simuler répartition device
    devices = ['Desktop', 'Mobile', 'Tablet']
    values = [42, 51, 7]
    
    fig = go.Figure(data=[go.Pie(
        labels=devices,
        values=values,
        hole=0.4,
        marker=dict(colors=['#3498db', '#e74c3c', '#f39c12'])
    )])
    
    fig.update_layout(
        height=300,
        template='plotly_dark',
        showlegend=True
    )
    
    return fig


# =============================================================================
# CALLBACKS - AUTRES PAGES
# =============================================================================

@app.callback(
    Output('multi-metrics-graph', 'figure'),
    [Input('url', 'pathname')]
)
def update_multi_metrics(pathname):
    """Graphique multi-métriques pour page Performance."""
    if pathname != '/performance':
        return go.Figure()
    
    events, _, _ = load_data()
    daily = events.groupby(events['timestamp'].dt.date).size().reset_index()
    daily.columns = ['date', 'events']
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily['date'], y=daily['events'],
        name='Événements', mode='lines+markers',
        line=dict(color='#3498db', width=2)
    ))
    
    fig.update_layout(
        title="Évolution des Événements",
        xaxis_title="Date", yaxis_title="Nombre d'Événements",
        template='plotly_dark', height=400, hovermode='x unified'
    )
    return fig


@app.callback(
    Output('heatmap-activity', 'figure'),
    [Input('url', 'pathname')]
)
def update_heatmap(pathname):
    """Heatmap activité par jour et heure."""
    if pathname != '/performance':
        return go.Figure()
    
    events, _, _ = load_data()
    events['hour'] = events['timestamp'].dt.hour
    events['dayofweek'] = events['timestamp'].dt.day_name()
    
    heatmap_data = events.groupby(['dayofweek', 'hour']).size().reset_index(name='count')
    pivot = heatmap_data.pivot(index='dayofweek', columns='hour', values='count').fillna(0)
    
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot = pivot.reindex(days_order)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values, x=pivot.columns, y=pivot.index,
        colorscale='Blues', text=pivot.values, texttemplate='%{text}',
        textfont={"size": 10}
    ))
    
    fig.update_layout(
        title="Heatmap Activité (Jour × Heure)",
        xaxis_title="Heure", yaxis_title="Jour",
        template='plotly_dark', height=500
    )
    return fig


@app.callback(
    Output('events-distribution-graph', 'figure'),
    [Input('url', 'pathname')]
)
def update_events_distribution(pathname):
    """Répartition des types d'événements."""
    if pathname != '/performance':
        return go.Figure()
    
    events, _, _ = load_data()
    event_counts = events['event'].value_counts()
    
    fig = go.Figure(data=[go.Pie(
        labels=event_counts.index,
        values=event_counts.values,
        hole=0.4,
        marker=dict(colors=['#3498db', '#e74c3c', '#2ecc71'])
    )])
    
    fig.update_layout(
        title="Répartition des Types d'Événements",
        template='plotly_dark', height=400
    )
    return fig


@app.callback(
    Output('weekly-trend-graph', 'figure'),
    [Input('url', 'pathname')]
)
def update_weekly_trend(pathname):
    """Tendance hebdomadaire."""
    if pathname != '/performance':
        return go.Figure()
    
    events, _, _ = load_data()
    events['week'] = events['timestamp'].dt.isocalendar().week
    weekly = events.groupby('week').size().reset_index(name='count')
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=weekly['week'], y=weekly['count'],
        mode='lines+markers', line=dict(color='#e74c3c', width=3),
        marker=dict(size=8), fill='tozeroy'
    ))
    
    fig.update_layout(
        title="Tendance Hebdomadaire",
        xaxis_title="Semaine", yaxis_title="Nombre d'Événements",
        template='plotly_dark', height=400, showlegend=False
    )
    return fig


@app.callback(
    Output('user-engagement-graph', 'figure'),
    [Input('url', 'pathname')]
)
def update_user_engagement(pathname):
    """Distribution de l'engagement utilisateurs."""
    if pathname != '/users':
        return go.Figure()
    
    _, users, _ = load_data()
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=users['n_events'], nbinsx=20,
        marker_color='#2ecc71', name='Distribution'
    ))
    
    fig.update_layout(
        title="Distribution du Nombre d'Événements par Utilisateur",
        xaxis_title="Nombre d'Événements", yaxis_title="Nombre d'Utilisateurs",
        template='plotly_dark', height=400, showlegend=False
    )
    return fig


@app.callback(
    Output('user-type-graph', 'figure'),
    [Input('url', 'pathname')]
)
def update_user_types(pathname):
    """Nouveaux vs récurrents."""
    if pathname != '/users':
        return go.Figure()
    
    _, users, _ = load_data()
    
    # Simuler nouveaux vs récurrents basé sur n_sessions
    new_users = len(users[users['n_sessions'] == 1])
    recurring = len(users[users['n_sessions'] > 1])
    
    fig = go.Figure(data=[go.Pie(
        labels=['Nouveaux', 'Récurrents'],
        values=[new_users, recurring],
        hole=0.4,
        marker=dict(colors=['#3498db', '#e74c3c'])
    )])
    
    fig.update_layout(
        title="Répartition Nouveaux vs Récurrents",
        template='plotly_dark', height=400
    )
    return fig


@app.callback(
    Output('conversion-segment-graph', 'figure'),
    [Input('url', 'pathname')]
)
def update_conversion_segment(pathname):
    """Taux de conversion par segment."""
    if pathname != '/users':
        return go.Figure()
    
    _, users, _ = load_data()
    
    # Segmenter par niveau d'activité
    users['segment'] = pd.cut(users['n_events'], bins=[0, 5, 15, 50, 1000], 
                               labels=['Faible', 'Moyen', 'Élevé', 'Très Élevé'])
    segment_conv = users.groupby('segment')['has_purchased'].mean() * 100
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=segment_conv.index.astype(str), y=segment_conv.values,
        marker_color=['#e74c3c', '#f39c12', '#2ecc71', '#3498db'],
        text=[f"{v:.1f}%" for v in segment_conv.values],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Taux de Conversion par Segment d'Activité",
        xaxis_title="Segment", yaxis_title="Taux de Conversion (%)",
        template='plotly_dark', height=400, showlegend=False
    )
    return fig


@app.callback(
    Output('user-activity-weekday-graph', 'figure'),
    [Input('url', 'pathname')]
)
def update_user_activity_weekday(pathname):
    """Activité par jour de la semaine."""
    if pathname != '/users':
        return go.Figure()
    
    events, _, _ = load_data()
    events['dayofweek'] = events['timestamp'].dt.day_name()
    
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_activity = events['dayofweek'].value_counts().reindex(days_order)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=weekday_activity.index, y=weekday_activity.values,
        marker_color='#9b59b6',
        text=weekday_activity.values, textposition='outside'
    ))
    
    fig.update_layout(
        title="Activité Utilisateurs par Jour de la Semaine",
        xaxis_title="Jour", yaxis_title="Nombre d'Événements",
        template='plotly_dark', height=400, showlegend=False
    )
    return fig


@app.callback(
    Output('top-products-graph', 'figure'),
    [Input('url', 'pathname')]
)
def update_top_products(pathname):
    """Top 20 produits."""
    if pathname != '/products':
        return go.Figure()
    
    _, _, products = load_data()
    top20 = products.nlargest(20, 'n_views')
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top20['n_views'], y=top20['itemid'].astype(str),
        orientation='h', marker_color='#9b59b6',
        text=top20['n_views'], textposition='outside'
    ))
    
    fig.update_layout(
        title="Top 20 Produits par Vues",
        xaxis_title="Nombre de Vues", yaxis_title="ID Produit",
        template='plotly_dark', height=600, showlegend=False
    )
    return fig


@app.callback(
    Output('top-conversion-products-graph', 'figure'),
    [Input('url', 'pathname')]
)
def update_top_conversion_products(pathname):
    """Produits avec meilleur taux de conversion."""
    if pathname != '/products':
        return go.Figure()
    
    _, _, products = load_data()
    # Filtrer produits avec au moins 10 vues
    products_filtered = products[products['n_views'] >= 10]
    top_conv = products_filtered.nlargest(15, 'conversion_rate')
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=top_conv['conversion_rate'], y=top_conv['itemid'].astype(str),
        orientation='h', marker_color='#2ecc71',
        text=[f"{v:.1f}%" for v in top_conv['conversion_rate']],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Top 15 Produits par Taux de Conversion",
        xaxis_title="Taux de Conversion (%)", yaxis_title="ID Produit",
        template='plotly_dark', height=500, showlegend=False
    )
    return fig


@app.callback(
    Output('products-matrix-graph', 'figure'),
    [Input('url', 'pathname')]
)
def update_products_matrix(pathname):
    """Matrice performance (vues × conversion)."""
    if pathname != '/products':
        return go.Figure()
    
    _, _, products = load_data()
    products_sample = products.sample(min(100, len(products)))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=products_sample['n_views'],
        y=products_sample['conversion_rate'],
        mode='markers',
        marker=dict(
            size=10,
            color=products_sample['n_purchases'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Achats")
        ),
        text=products_sample['itemid'],
        hovertemplate='<b>Produit %{text}</b><br>Vues: %{x}<br>Conv: %{y:.1f}%<extra></extra>'
    ))
    
    fig.update_layout(
        title="Matrice Performance Produits",
        xaxis_title="Nombre de Vues", yaxis_title="Taux de Conversion (%)",
        template='plotly_dark', height=500
    )
    return fig


@app.callback(
    Output('products-comparison-graph', 'figure'),
    [Input('url', 'pathname')]
)
def update_products_comparison(pathname):
    """Graphique de comparaison des produits (heatmap ou treemap)."""
    if pathname != '/products':
        return go.Figure()
    
    _, _, products = load_data()
    top30 = products.nlargest(30, 'n_views')
    
    # Créer un treemap interactif
    fig = go.Figure(go.Treemap(
        labels=top30['itemid'].astype(str),
        parents=['Produits'] * len(top30),
        values=top30['n_views'],
        text=top30['itemid'].astype(str),
        texttemplate='<b>%{label}</b><br>Vues: %{value}<br>Conv: ' + 
                     top30['conversion_rate'].apply(lambda x: f'{x:.1f}%').astype(str),
        marker=dict(
            colorscale='Viridis',
            cmid=top30['conversion_rate'].median(),
            colorbar=dict(title="Taux Conv. (%)")
        ),
        hovertemplate='<b>Produit %{label}</b><br>Vues: %{value}<br>Achats: ' +
                      top30['n_purchases'].astype(str) + '<extra></extra>'
    ))
    
    fig.update_layout(
        title="Analyse Comparative des Top 30 Produits (Taille = Vues, Couleur = Conversion)",
        template='plotly_dark', height=600
    )
    return fig


@app.callback(
    Output('detailed-funnel-graph', 'figure'),
    [Input('url', 'pathname')]
)
def update_detailed_funnel(pathname):
    """Funnel détaillé pour page Funnel."""
    if pathname != '/funnel':
        return go.Figure()
    
    events, _, _ = load_data()
    
    n_views = len(events[events['event'] == 'view'])
    n_cart = len(events[events['event'] == 'addtocart'])
    n_purchase = len(events[events['event'] == 'transaction'])
    
    fig = go.Figure(go.Funnel(
        y=['️ Vues Produit', 'Ajout Panier', 'Transaction'],
        x=[n_views, n_cart, n_purchase],
        textposition="inside",
        textinfo="value+percent initial+percent previous",
        marker=dict(color=['#3498db', '#f39c12', '#2ecc71']),
        connector={"line": {"color": "royalblue", "dash": "dot", "width": 3}}
    ))
    
    fig.update_layout(
        height=500, template='plotly_dark', showlegend=False
    )
    return fig


@app.callback(
    Output('funnel-time-graph', 'figure'),
    [Input('url', 'pathname')]
)
def update_funnel_time(pathname):
    """Temps moyen par étape du funnel."""
    if pathname != '/funnel':
        return go.Figure()
    
    # Données simulées pour temps moyen
    stages = ['Vue → Panier', 'Panier → Achat']
    times = [8.5, 12.3]  # minutes
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=stages, y=times,
        marker_color=['#3498db', '#e74c3c'],
        text=[f"{t:.1f} min" for t in times],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Temps Moyen par Étape",
        yaxis_title="Temps (minutes)",
        template='plotly_dark', height=400, showlegend=False
    )
    return fig


@app.callback(
    Output('funnel-dropoff-graph', 'figure'),
    [Input('url', 'pathname')]
)
def update_funnel_dropoff(pathname):
    """Taux de drop-off par étape."""
    if pathname != '/funnel':
        return go.Figure()
    
    events, _, _ = load_data()
    n_views = len(events[events['event'] == 'view'])
    n_cart = len(events[events['event'] == 'addtocart'])
    n_purchase = len(events[events['event'] == 'transaction'])
    
    dropoff_1 = ((n_views - n_cart) / n_views * 100) if n_views > 0 else 0
    dropoff_2 = ((n_cart - n_purchase) / n_cart * 100) if n_cart > 0 else 0
    
    stages = ['Vue → Panier', 'Panier → Achat']
    dropoffs = [dropoff_1, dropoff_2]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=stages, y=dropoffs,
        marker_color=['#f39c12', '#e74c3c'],
        text=[f"{d:.1f}%" for d in dropoffs],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Taux de Drop-off par Étape",
        yaxis_title="Drop-off (%)",
        template='plotly_dark', height=400, showlegend=False
    )
    return fig


@app.callback(
    Output('funnel-evolution-graph', 'figure'),
    [Input('url', 'pathname')]
)
def update_funnel_evolution(pathname):
    """Évolution du funnel sur 7 jours."""
    if pathname != '/funnel':
        return go.Figure()
    
    events, _, _ = load_data()
    
    # Derniers 7 jours
    last_7_days = events['timestamp'].max() - pd.Timedelta(days=7)
    recent = events[events['timestamp'] >= last_7_days]
    
    recent['date'] = recent['timestamp'].dt.date
    daily_funnel = recent.groupby(['date', 'event']).size().unstack(fill_value=0)
    
    fig = go.Figure()
    
    for event_type in ['view', 'addtocart', 'transaction']:
        if event_type in daily_funnel.columns:
            fig.add_trace(go.Scatter(
                x=daily_funnel.index,
                y=daily_funnel[event_type],
                mode='lines+markers',
                name=event_type.capitalize(),
                line=dict(width=3)
            ))
    
    fig.update_layout(
        title="Évolution du Funnel (7 derniers jours)",
        xaxis_title="Date", yaxis_title="Nombre d'Événements",
        template='plotly_dark', height=400, hovermode='x unified'
    )
    return fig


@app.callback(
    Output('recommendations-section', 'children'),
    [Input('url', 'pathname')]
)
def update_funnel_recommendations(pathname):
    """Recommandations basées sur le funnel."""
    if pathname != '/funnel':
        return ""
    
    events, _, _ = load_data()
    n_views = len(events[events['event'] == 'view'])
    n_cart = len(events[events['event'] == 'addtocart'])
    n_purchase = len(events[events['event'] == 'transaction'])
    
    cart_rate = (n_cart / n_views * 100) if n_views > 0 else 0
    purchase_rate = (n_purchase / n_cart * 100) if n_cart > 0 else 0
    
    recommendations = []
    
    if cart_rate < 10:
        recommendations.append(html.Li("️ Taux d'ajout au panier faible (<10%). Améliorer les fiches produits et ajouter des avis clients."))
    
    if purchase_rate < 50:
        recommendations.append(html.Li("️ Fort taux d'abandon panier. Simplifier le checkout et proposer plusieurs modes de paiement."))
    
    if not recommendations:
        recommendations.append(html.Li("Funnel de conversion performant ! Continuez le monitoring."))
    
    return html.Ul(recommendations)


# =============================================================================
# CALLBACKS - A/B TESTS
# =============================================================================

@app.callback(
    Output('simulation-status', 'children'),
    [Input('run-simulation-btn', 'n_clicks')],
    [State('sim-test-name', 'value'),
     State('sim-duration', 'value'),
     State('sim-lift', 'value'),
     State('sim-group-a-name', 'value'),
     State('sim-group-a-rate', 'value'),
     State('sim-group-b-name', 'value'),
     State('sim-sample-size', 'value')]
)
def run_ab_simulation(n_clicks, test_name, duration, lift, group_a_name, base_rate, group_b_name, sample_size):
    """Lance une simulation A/B test avec les paramètres donnés."""
    if n_clicks is None or n_clicks == 0:
        return ""
    
    import scipy.stats as stats
    from datetime import datetime
    
    # Calculer les taux
    base_rate = base_rate / 100
    lift_decimal = lift / 100
    variant_rate = base_rate * (1 + lift_decimal)
    
    # Simuler les conversions
    np.random.seed(42 + n_clicks)
    conversions_a = int(np.random.binomial(sample_size, base_rate))
    conversions_b = int(np.random.binomial(sample_size, variant_rate))
    
    rate_a = conversions_a / sample_size
    rate_b = conversions_b / sample_size
    
    # Tests statistiques
    pooled_rate = (conversions_a + conversions_b) / (2 * sample_size)
    se = np.sqrt(pooled_rate * (1 - pooled_rate) * (2 / sample_size))
    z_score = (rate_b - rate_a) / se if se > 0 else 0
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    # Intervalle de confiance
    se_diff = np.sqrt((rate_a * (1 - rate_a) / sample_size) + (rate_b * (1 - rate_b) / sample_size))
    ci_lower = (rate_b - rate_a) - 1.96 * se_diff
    ci_upper = (rate_b - rate_a) + 1.96 * se_diff
    
    # Impact business
    lift_abs = rate_b - rate_a
    lift_rel = ((rate_b / rate_a) - 1) * 100 if rate_a > 0 else 0
    additional_conv_month = lift_abs * 10000  # Simulé sur 10k users/mois
    additional_revenue_month = additional_conv_month * 50  # AOV simulé
    additional_revenue_year = additional_revenue_month * 12
    
    # Créer le JSON des résultats
    results = {
        'test_name': test_name,
        'test_date': datetime.now().strftime('%Y-%m-%d'),
        'duration_days': int(duration),
        'group_A': {
            'name': group_a_name,
            'n_users': int(sample_size),
            'n_conversions': int(conversions_a),
            'conversion_rate': float(rate_a)
        },
        'group_B': {
            'name': group_b_name,
            'n_users': int(sample_size),
            'n_conversions': int(conversions_b),
            'conversion_rate': float(rate_b)
        },
        'statistics': {
            'absolute_lift': float(lift_abs),
            'relative_lift': float(lift_rel),
            'z_score': float(z_score),
            'p_value': float(p_value),
            'significant': bool(p_value < 0.05),
            'ci_lower': float(ci_lower),
            'ci_upper': float(ci_upper),
            'power': 0.8
        },
        'business_impact': {
            'monthly_users': 10000,
            'additional_conversions_month': float(additional_conv_month),
            'additional_revenue_month': float(additional_revenue_month),
            'additional_revenue_year': float(additional_revenue_year),
            'roi_percent': 500,
            'payback_months': 2
        }
    }
    
    # Sauvegarder les résultats
    import os
    os.makedirs('data/clean', exist_ok=True)
    with open('data/clean/ab_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    # Message de succès
    if p_value < 0.05:
        alert_color = "success"
        message = f"Simulation terminée ! Résultat SIGNIFICATIF (p={p_value:.4f}). Lift: {lift_rel:+.1f}%. Rechargez la page pour voir les résultats complets."
    else:
        alert_color = "warning"
        message = f"Simulation terminée. Résultat NON significatif (p={p_value:.4f}). Lift: {lift_rel:+.1f}%. Rechargez la page pour voir les résultats."
    
    return dbc.Alert([
        html.H5("Simulation réussie !", className="mb-2"),
        html.P(message),
        dbc.Button("Recharger la Page", id='reload-btn', color='primary', className='mt-2', 
                   href='/abtests', external_link=False)
    ], color=alert_color)


@app.callback(
    Output('ab-conversion-comparison', 'figure'),
    Input('url', 'pathname')
)
def update_ab_comparison_chart(pathname):
    """
    Graphique de comparaison des taux de conversion A/B.
    """
    if pathname != '/abtests':
        return go.Figure()
    
    results = load_ab_test_results()
    
    groups = ['Groupe A\n'+ results['group_A']['name'], 
              'Groupe B\n'+ results['group_B']['name']]
    rates = [results['group_A']['conversion_rate'], 
             results['group_B']['conversion_rate']]
    colors = ['#95a5a6', '#27ae60']
    
    fig = go.Figure()
    
    # Barres
    bars = fig.add_trace(go.Bar(
        x=groups,
        y=rates,
        marker=dict(color=colors),
        text=[f"{r:.2%}" for r in rates],
        textposition='outside',
        textfont=dict(size=14, color='black'),
        showlegend=False
    ))
    
    # Ligne de lift
    fig.add_trace(go.Scatter(
        x=[0, 1],
        y=rates,
        mode='lines',
        line=dict(color='red', dash='dash', width=2),
        showlegend=False
    ))
    
    # Annotation du lift
    mid_x = 0.5
    mid_y = (rates[0] + rates[1]) / 2
    fig.add_annotation(
        x=mid_x, y=mid_y,
        text=f"Lift: {results['statistics']['relative_lift']:+.1f}%",
        showarrow=False,
        font=dict(size=12, color='red'),
        bgcolor='white',
        bordercolor='red',
        borderwidth=2
    )
    
    fig.update_layout(
        title="Comparaison des Taux de Conversion",
        yaxis_title="Taux de Conversion",
        yaxis=dict(tickformat='.1%'),
        height=400,
        template='plotly_dark',
        showlegend=False
    )
    
    return fig


@app.callback(
    Output('ab-confidence-interval', 'figure'),
    Input('url', 'pathname')
)
def update_ab_ci_chart(pathname):
    """
    Graphique de l'intervalle de confiance.
    """
    if pathname != '/abtests':
        return go.Figure()
    
    results = load_ab_test_results()
    
    lift = results['statistics']['absolute_lift']
    ci_lower = results['statistics']['ci_lower']
    ci_upper = results['statistics']['ci_upper']
    
    fig = go.Figure()
    
    # Point du lift observé
    fig.add_trace(go.Scatter(
        x=[0],
        y=[lift],
        mode='markers',
        marker=dict(size=20, color='#27ae60'),
        name='Lift Observé',
        error_y=dict(
            type='data',
            symmetric=False,
            array=[ci_upper - lift],
            arrayminus=[lift - ci_lower],
            color='#34495e',
            thickness=3,
            width=10
        )
    ))
    
    # Ligne à zéro
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="red",
        annotation_text="Pas de différence",
        annotation_position="right"
    )
    
    fig.update_layout(
        title="Intervalle de Confiance à 95%",
        yaxis_title="Lift Absolu",
        yaxis=dict(tickformat='.2%'),
        xaxis=dict(showticklabels=False, range=[-0.5, 0.5]),
        height=400,
        template='plotly_dark',
        showlegend=False
    )
    
    return fig


@app.callback(
    Output('ab-recommendations', 'children'),
    Input('url', 'pathname')
)
def update_ab_recommendations(pathname):
    """
    Génère les recommandations basées sur les résultats.
    """
    if pathname != '/abtests':
        return ""
    
    results = load_ab_test_results()
    
    if results['statistics']['significant']:
        recommendations = [
            dbc.Alert([
                html.H5("Test Concluant - Recommandation: DÉPLOYER", className="alert-heading"),
                html.Hr(),
                html.P([
                    "Le test montre une amélioration statistiquement significative de ",
                    html.Strong(f"{results['statistics']['relative_lift']:+.1f}%"),
                    f"(p-value = {results['statistics']['p_value']:.4f} < 0.05)."
                ]),
                html.P("Actions recommandées:", className="fw-bold mb-2"),
                html.Ul([
                    html.Li("Planifier un déploiement progressif (5% → 25% → 100%)"),
                    html.Li(f"Impact attendu: {results['business_impact']['additional_revenue_year']:,.0f}€/an"),
                    html.Li(f"ROI estimé: {results['business_impact']['roi_percent']:.0f}%"),
                    html.Li("Monitorer les métriques pendant 30 jours post-déploiement"),
                    html.Li("Mettre en place un plan de rollback si nécessaire")
                ])
            ], color="success")
        ]
    else:
        power = results['statistics']['power']
        recommendations = [
            dbc.Alert([
                html.H5("️ Test Non Concluant - Recommandation: PROLONGER", className="alert-heading"),
                html.Hr(),
                html.P([
                    "Le test ne montre pas de différence statistiquement significative ",
                    f"(p-value = {results['statistics']['p_value']:.4f} >= 0.05)."
                ]),
                html.P("Actions recommandées:", className="fw-bold mb-2"),
                html.Ul([
                    html.Li(f"️ Prolonger le test (puissance actuelle: {power:.1%}, cible: 80%+)"),
                    html.Li("️ Augmenter la taille de l'échantillon"),
                    html.Li("️ Vérifier qu'il n'y a pas de bugs techniques"),
                    html.Li("️ Analyser par segments (mobile vs desktop, nouveaux vs réguliers)"),
                    html.Li("Ne PAS déployer sans preuve d'effet significatif")
                ])
            ], color="warning")
        ]
    
    # Ajouter considérations additionnelles
    recommendations.append(
        dbc.Card([
            dbc.CardHeader("Considérations Additionnelles"),
            dbc.CardBody([
                html.P("Métriques à surveiller post-déploiement:", className="fw-bold"),
                html.Ul([
                    html.Li("Valeur panier moyenne (AOV)"),
                    html.Li("Taux de retour produits"),
                    html.Li("Satisfaction client (NPS)"),
                    html.Li("Volume de tickets support"),
                    html.Li("Taux de réachat à 30/60/90 jours")
                ]),
                html.P([
                    "Durée recommandée du test: ",
                    html.Strong("28 jours minimum"),
                    "pour couvrir 2 cycles hebdomadaires complets."
                ])
            ])
        ], className="mt-3")
    )
    
    return recommendations


# =============================================================================
# EXÉCUTION
# =============================================================================

if __name__ == '__main__':
    # Mode développement avec debug=True
    # En production : utiliser gunicorn
    app.run_server(
        debug=True,
        host='0.0.0.0',
        port=8050
    )
    
    print("\n"+ "="*70)
    print("Dashboard lancé avec succès!")
    print("="*70)
    print(f"URL : http://localhost:8050")
    print(f"Pages disponibles :")
    print(f"- Home        : http://localhost:8050/")
    print(f"- Performance : http://localhost:8050/performance")
    print(f"- Users       : http://localhost:8050/users")
    print(f"- Products    : http://localhost:8050/products")
    print(f"- Funnel      : http://localhost:8050/funnel")
    print(f"- A/B Tests   : http://localhost:8050/abtests")
    print(f"\n Pour voir les A/B tests: lancez d'abord 'python simulate_ab_test_from_data.py'")
    print("="*70 + "\n")
    print(f"- Funnel    : http://localhost:8050/funnel")
    print("="*70 + "\n")