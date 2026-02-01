"""
Générateur de Rapport PDF - Analyse E-commerce et Tests A/B
============================================================

Ce script génère un rapport PDF professionnel contenant :
- Analyse exploratoire des données
- Visualisations clés
- Résultats des tests A/B
- Recommandations business

Auteur: Data Analyst
Date: Février 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

# Configuration globale pour les graphiques
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def create_title_page(pdf, title, subtitle, author, date):
    """Crée une page de titre professionnelle"""
    fig = plt.figure(figsize=(8.5, 11))
    fig.patch.set_facecolor('white')
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    # Titre principal
    ax.text(0.5, 0.7, title, 
            ha='center', va='center', 
            fontsize=28, fontweight='bold',
            color='#2c3e50')
    
    # Sous-titre
    ax.text(0.5, 0.6, subtitle,
            ha='center', va='center',
            fontsize=16, color='#34495e')
    
    # Ligne de séparation
    ax.plot([0.2, 0.8], [0.5, 0.5], 'k-', linewidth=2, color='#3498db')
    
    # Informations
    ax.text(0.5, 0.35, f'Auteur: {author}',
            ha='center', va='center',
            fontsize=12, color='#7f8c8d')
    
    ax.text(0.5, 0.3, f'Date: {date}',
            ha='center', va='center',
            fontsize=12, color='#7f8c8d')
    
    # Logo ou décoration (optionnel)
    ax.text(0.5, 0.15, '📊 Dashboard Analytics',
            ha='center', va='center',
            fontsize=14, color='#3498db')
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def create_section_page(pdf, section_title, section_number):
    """Crée une page de section"""
    fig = plt.figure(figsize=(8.5, 11))
    fig.patch.set_facecolor('#ecf0f1')
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    ax.text(0.5, 0.5, f'{section_number}. {section_title}',
            ha='center', va='center',
            fontsize=32, fontweight='bold',
            color='#2c3e50')
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def add_text_page(pdf, title, content):
    """Ajoute une page de texte avec titre et contenu"""
    fig = plt.figure(figsize=(8.5, 11))
    fig.patch.set_facecolor('white')
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    # Titre
    ax.text(0.5, 0.95, title,
            ha='center', va='top',
            fontsize=20, fontweight='bold',
            color='#2c3e50')
    
    # Contenu
    ax.text(0.1, 0.85, content,
            ha='left', va='top',
            fontsize=10, color='#34495e',
            wrap=True)
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def load_and_analyze_data():
    """Charge et analyse les données"""
    print("📊 Chargement des données...")
    
    # Charger les événements enrichis
    try:
        events_df = pd.read_csv('data/clean/events_enriched.csv', nrows=100000)
        print(f"   ✅ Chargé {len(events_df):,} événements")
    except FileNotFoundError:
        print("   ⚠️  Fichier events_enriched.csv introuvable, utilisation de events.csv")
        try:
            events_df = pd.read_csv('data/raw/events.csv', nrows=100000)
            events_df['timestamp'] = pd.to_datetime(events_df['timestamp'], unit='ms')
        except:
            print("   ❌ Impossible de charger les données d'événements")
            events_df = None
    
    # Charger les résultats A/B test
    try:
        ab_test_df = pd.read_csv('ab_test_simulation_results.csv')
        print(f"   ✅ Chargé {len(ab_test_df):,} sessions A/B test")
    except:
        print("   ❌ Impossible de charger les résultats A/B test")
        ab_test_df = None
    
    return events_df, ab_test_df


def create_executive_summary(pdf, events_df, ab_test_df):
    """Crée le résumé exécutif"""
    fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
    fig.suptitle('Résumé Exécutif - KPIs Clés', fontsize=16, fontweight='bold', y=0.98)
    
    # KPI 1: Volume total d'événements
    ax = axes[0, 0]
    if events_df is not None:
        total_events = len(events_df)
        total_users = events_df['visitorid'].nunique()
        
        ax.text(0.5, 0.7, f'{total_events:,}', 
                ha='center', va='center', fontsize=36, fontweight='bold', color='#3498db')
        ax.text(0.5, 0.4, 'Événements Totaux',
                ha='center', va='center', fontsize=14, color='#7f8c8d')
        ax.text(0.5, 0.2, f'{total_users:,} utilisateurs uniques',
                ha='center', va='center', fontsize=10, color='#95a5a6')
    ax.axis('off')
    
    # KPI 2: Taux de conversion global
    ax = axes[0, 1]
    if events_df is not None:
        views = (events_df['event'] == 'view').sum()
        transactions = (events_df['event'] == 'transaction').sum()
        conv_rate = (transactions / views * 100) if views > 0 else 0
        
        ax.text(0.5, 0.7, f'{conv_rate:.2f}%',
                ha='center', va='center', fontsize=36, fontweight='bold', color='#27ae60')
        ax.text(0.5, 0.4, 'Taux de Conversion',
                ha='center', va='center', fontsize=14, color='#7f8c8d')
        ax.text(0.5, 0.2, f'{transactions:,} transactions / {views:,} vues',
                ha='center', va='center', fontsize=10, color='#95a5a6')
    ax.axis('off')
    
    # KPI 3: Résultat A/B Test
    ax = axes[1, 0]
    if ab_test_df is not None:
        conv_a = ab_test_df[ab_test_df['group'] == 'A']['converted_final'].mean() * 100
        conv_b = ab_test_df[ab_test_df['group'] == 'B']['converted_final'].mean() * 100
        lift = ((conv_b - conv_a) / conv_a * 100) if conv_a > 0 else 0
        
        ax.text(0.5, 0.7, f'+{lift:.1f}%',
                ha='center', va='center', fontsize=36, fontweight='bold', 
                color='#e74c3c' if lift < 0 else '#27ae60')
        ax.text(0.5, 0.4, 'Lift du Test A/B',
                ha='center', va='center', fontsize=14, color='#7f8c8d')
        ax.text(0.5, 0.2, f'Groupe B vs Groupe A',
                ha='center', va='center', fontsize=10, color='#95a5a6')
    ax.axis('off')
    
    # KPI 4: Significativité statistique
    ax = axes[1, 1]
    if ab_test_df is not None:
        # Calcul p-value
        group_a = ab_test_df[ab_test_df['group'] == 'A']['converted_final']
        group_b = ab_test_df[ab_test_df['group'] == 'B']['converted_final']
        
        # Test z de proportions
        n_a, n_b = len(group_a), len(group_b)
        p_a, p_b = group_a.mean(), group_b.mean()
        pooled_p = (group_a.sum() + group_b.sum()) / (n_a + n_b)
        se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n_a + 1/n_b))
        z_score = (p_b - p_a) / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
        
        is_significant = p_value < 0.05
        
        ax.text(0.5, 0.7, '✓' if is_significant else '✗',
                ha='center', va='center', fontsize=48, fontweight='bold',
                color='#27ae60' if is_significant else '#e74c3c')
        ax.text(0.5, 0.4, 'Significatif' if is_significant else 'Non Significatif',
                ha='center', va='center', fontsize=14, color='#7f8c8d')
        ax.text(0.5, 0.2, f'p-value: {p_value:.4f}',
                ha='center', va='center', fontsize=10, color='#95a5a6')
    ax.axis('off')
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def create_event_distribution_chart(pdf, events_df):
    """Crée le graphique de distribution des événements"""
    if events_df is None:
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))
    fig.suptitle('Distribution des Événements', fontsize=14, fontweight='bold')
    
    # Graphique en barres
    event_counts = events_df['event'].value_counts()
    colors = ['#3498db', '#e74c3c', '#2ecc71']
    ax1.bar(event_counts.index, event_counts.values, color=colors[:len(event_counts)])
    ax1.set_xlabel('Type d\'événement', fontsize=11)
    ax1.set_ylabel('Nombre d\'événements', fontsize=11)
    ax1.set_title('Distribution par Type')
    
    # Formater les valeurs de l'axe y
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x/1000)}K' if x >= 1000 else str(int(x))))
    
    # Graphique en camembert
    ax2.pie(event_counts.values, labels=event_counts.index, autopct='%1.1f%%',
            colors=colors[:len(event_counts)], startangle=90)
    ax2.set_title('Répartition en Pourcentage')
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def create_temporal_analysis(pdf, events_df):
    """Crée l'analyse temporelle"""
    if events_df is None or 'timestamp' not in events_df.columns:
        return
    
    try:
        events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])
        events_df['date'] = events_df['timestamp'].dt.date
        events_df['hour'] = events_df['timestamp'].dt.hour
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8))
        fig.suptitle('Analyse Temporelle des Événements', fontsize=14, fontweight='bold')
        
        # Évolution quotidienne
        daily_events = events_df.groupby('date').size()
        ax1.plot(daily_events.index, daily_events.values, marker='o', linewidth=2, color='#3498db')
        ax1.fill_between(daily_events.index, daily_events.values, alpha=0.3, color='#3498db')
        ax1.set_xlabel('Date', fontsize=11)
        ax1.set_ylabel('Nombre d\'événements', fontsize=11)
        ax1.set_title('Évolution Quotidienne')
        ax1.grid(True, alpha=0.3)
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Distribution horaire
        hourly_events = events_df.groupby('hour').size()
        ax2.bar(hourly_events.index, hourly_events.values, color='#e74c3c', alpha=0.7)
        ax2.set_xlabel('Heure de la journée', fontsize=11)
        ax2.set_ylabel('Nombre d\'événements', fontsize=11)
        ax2.set_title('Distribution Horaire')
        ax2.set_xticks(range(0, 24))
        ax2.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        pdf.savefig(fig, bbox_inches='tight')
        plt.close()
    except Exception as e:
        print(f"   ⚠️  Erreur lors de l'analyse temporelle: {e}")


def create_funnel_analysis(pdf, events_df):
    """Crée l'analyse du funnel de conversion"""
    if events_df is None:
        return
    
    fig, ax = plt.subplots(figsize=(11, 6))
    fig.suptitle('Funnel de Conversion', fontsize=14, fontweight='bold')
    
    # Calculer les étapes du funnel
    views = (events_df['event'] == 'view').sum()
    addtocarts = (events_df['event'] == 'addtocart').sum()
    transactions = (events_df['event'] == 'transaction').sum()
    
    stages = ['Vues', 'Ajouts Panier', 'Transactions']
    values = [views, addtocarts, transactions]
    colors = ['#3498db', '#f39c12', '#27ae60']
    
    # Calculer les pourcentages
    percentages = [100, (addtocarts/views*100) if views > 0 else 0, 
                   (transactions/views*100) if views > 0 else 0]
    
    # Dessiner le funnel
    for i, (stage, value, pct, color) in enumerate(zip(stages, values, percentages, colors)):
        y_pos = 3 - i
        width = pct / 100 * 0.8
        
        ax.barh(y_pos, width, height=0.6, left=(1-width)/2, color=color, alpha=0.7)
        
        # Texte au centre
        ax.text(0.5, y_pos, f'{stage}\n{value:,} ({pct:.1f}%)',
                ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0.5, 3.5)
    ax.axis('off')
    
    # Ajouter les taux de conversion entre étapes
    if views > 0:
        conv_to_cart = (addtocarts / views * 100)
        ax.text(0.9, 2.3, f'↓ {conv_to_cart:.1f}%', ha='center', fontsize=10, color='#7f8c8d')
    
    if addtocarts > 0:
        conv_to_transaction = (transactions / addtocarts * 100)
        ax.text(0.9, 1.3, f'↓ {conv_to_transaction:.1f}%', ha='center', fontsize=10, color='#7f8c8d')
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def create_ab_test_results(pdf, ab_test_df):
    """Crée l'analyse détaillée des résultats A/B test"""
    if ab_test_df is None:
        return
    
    fig = plt.figure(figsize=(11, 8.5))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    fig.suptitle('Résultats Détaillés du Test A/B', fontsize=16, fontweight='bold')
    
    # Calculer les métriques
    group_a = ab_test_df[ab_test_df['group'] == 'A']
    group_b = ab_test_df[ab_test_df['group'] == 'B']
    
    n_a, n_b = len(group_a), len(group_b)
    conv_a = group_a['converted_final'].mean()
    conv_b = group_b['converted_final'].mean()
    
    # Test statistique
    pooled_p = (group_a['converted_final'].sum() + group_b['converted_final'].sum()) / (n_a + n_b)
    se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n_a + 1/n_b))
    z_score = (conv_b - conv_a) / se
    p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
    
    lift = ((conv_b - conv_a) / conv_a * 100) if conv_a > 0 else 0
    
    # 1. Comparaison des taux de conversion
    ax1 = fig.add_subplot(gs[0, 0])
    groups = ['Groupe A\n(Contrôle)', 'Groupe B\n(Variante)']
    conv_rates = [conv_a * 100, conv_b * 100]
    colors_bars = ['#3498db', '#2ecc71']
    
    bars = ax1.bar(groups, conv_rates, color=colors_bars, alpha=0.7, edgecolor='black')
    ax1.set_ylabel('Taux de Conversion (%)', fontsize=11)
    ax1.set_title('Comparaison des Taux de Conversion', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Ajouter les valeurs sur les barres
    for bar, rate in zip(bars, conv_rates):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.2f}%', ha='center', va='bottom', fontweight='bold')
    
    # 2. Tableau des statistiques
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.axis('off')
    
    stats_data = [
        ['Métrique', 'Groupe A', 'Groupe B'],
        ['Taille échantillon', f'{n_a:,}', f'{n_b:,}'],
        ['Conversions', f'{int(group_a["converted_final"].sum())}', f'{int(group_b["converted_final"].sum())}'],
        ['Taux conversion', f'{conv_a*100:.2f}%', f'{conv_b*100:.2f}%'],
        ['', '', ''],
        ['Lift relatif', '', f'{lift:+.1f}%'],
        ['Z-score', '', f'{z_score:.3f}'],
        ['P-value', '', f'{p_value:.4f}'],
        ['Significatif (α=0.05)', '', '✓ Oui' if p_value < 0.05 else '✗ Non']
    ]
    
    table = ax2.table(cellText=stats_data, cellLoc='left', loc='center',
                     colWidths=[0.4, 0.3, 0.3])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # Mise en forme du tableau
    for i in range(len(stats_data)):
        for j in range(3):
            cell = table[(i, j)]
            if i == 0:
                cell.set_facecolor('#34495e')
                cell.set_text_props(weight='bold', color='white')
            elif i == 4:
                cell.set_facecolor('#ecf0f1')
            elif i >= 5:
                cell.set_facecolor('#e8f8f5')
    
    # 3. Distribution des conversions
    ax3 = fig.add_subplot(gs[1, :])
    
    conv_data = [
        group_a['converted_final'].value_counts().sort_index(),
        group_b['converted_final'].value_counts().sort_index()
    ]
    
    x = np.arange(2)
    width = 0.35
    
    ax3.bar(x - width/2, [n_a - group_a['converted_final'].sum(), n_b - group_b['converted_final'].sum()], 
            width, label='Non converti', color='#e74c3c', alpha=0.7)
    ax3.bar(x + width/2, [group_a['converted_final'].sum(), group_b['converted_final'].sum()], 
            width, label='Converti', color='#2ecc71', alpha=0.7)
    
    ax3.set_ylabel('Nombre de sessions', fontsize=11)
    ax3.set_title('Distribution des Conversions par Groupe', fontsize=12, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(['Groupe A', 'Groupe B'])
    ax3.legend()
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Intervalle de confiance
    ax4 = fig.add_subplot(gs[2, :])
    
    # Calculer intervalles de confiance (95%)
    z_crit = 1.96
    ci_a = z_crit * np.sqrt(conv_a * (1 - conv_a) / n_a)
    ci_b = z_crit * np.sqrt(conv_b * (1 - conv_b) / n_b)
    
    y_pos = [1, 0]
    ax4.errorbar([conv_a * 100], y_pos[0], xerr=ci_a * 100, fmt='o', markersize=10,
                 color='#3498db', capsize=5, capthick=2, label='Groupe A', linewidth=2)
    ax4.errorbar([conv_b * 100], y_pos[1], xerr=ci_b * 100, fmt='o', markersize=10,
                 color='#2ecc71', capsize=5, capthick=2, label='Groupe B', linewidth=2)
    
    ax4.set_xlabel('Taux de Conversion (%) avec IC 95%', fontsize=11)
    ax4.set_yticks(y_pos)
    ax4.set_yticklabels(['Groupe A', 'Groupe B'])
    ax4.set_title('Intervalles de Confiance à 95%', fontsize=12, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def create_recommendations_page(pdf, ab_test_df):
    """Crée la page des recommandations"""
    fig = plt.figure(figsize=(8.5, 11))
    fig.patch.set_facecolor('white')
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    # Titre
    ax.text(0.5, 0.95, 'Recommandations Business',
            ha='center', va='top',
            fontsize=22, fontweight='bold', color='#2c3e50')
    
    if ab_test_df is not None:
        group_a = ab_test_df[ab_test_df['group'] == 'A']
        group_b = ab_test_df[ab_test_df['group'] == 'B']
        
        conv_a = group_a['converted_final'].mean()
        conv_b = group_b['converted_final'].mean()
        lift = ((conv_b - conv_a) / conv_a * 100) if conv_a > 0 else 0
        
        # Calculer p-value
        n_a, n_b = len(group_a), len(group_b)
        pooled_p = (group_a['converted_final'].sum() + group_b['converted_final'].sum()) / (n_a + n_b)
        se = np.sqrt(pooled_p * (1 - pooled_p) * (1/n_a + 1/n_b))
        z_score = (conv_b - conv_a) / se
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
        
        is_significant = p_value < 0.05
        
        # Contenu des recommandations
        y_pos = 0.85
        
        # Recommandation 1
        ax.text(0.1, y_pos, '1. Décision sur le Test A/B',
                ha='left', va='top', fontsize=14, fontweight='bold', color='#2c3e50')
        y_pos -= 0.05
        
        if is_significant and lift > 0:
            recommendation = f"""
✓ RECOMMANDATION : Déployer la variante B en production

Le test A/B montre une amélioration significative de {lift:.1f}% du taux de conversion
(p-value = {p_value:.4f} < 0.05). Cette différence est statistiquement valide.

Impact business estimé :
• Si 10,000 visiteurs/mois : +{int(10000 * (conv_b - conv_a))} conversions/mois
• ROI potentiel positif justifiant le déploiement immédiat
            """
        else:
            recommendation = f"""
⚠ RECOMMANDATION : Ne pas déployer la variante B

Le test ne montre pas d'amélioration statistiquement significative
(p-value = {p_value:.4f} >= 0.05). Il est recommandé de :
• Prolonger le test pour collecter plus de données
• Revoir les modifications apportées dans la variante B
• Tester une approche différente
            """
        
        ax.text(0.1, y_pos, recommendation,
                ha='left', va='top', fontsize=10, color='#34495e')
        y_pos -= 0.20
        
        # Recommandation 2
        ax.text(0.1, y_pos, '2. Optimisation du Funnel de Conversion',
                ha='left', va='top', fontsize=14, fontweight='bold', color='#2c3e50')
        y_pos -= 0.05
        
        funnel_rec = """
• Analyser les points de friction dans le parcours utilisateur
• Implémenter des stratégies de réengagement pour les paniers abandonnés
• A/B tester des optimisations du processus de checkout
• Mettre en place des campagnes de retargeting ciblées
        """
        
        ax.text(0.1, y_pos, funnel_rec,
                ha='left', va='top', fontsize=10, color='#34495e')
        y_pos -= 0.15
        
        # Recommandation 3
        ax.text(0.1, y_pos, '3. Segmentation et Personnalisation',
                ha='left', va='top', fontsize=14, fontweight='bold', color='#2c3e50')
        y_pos -= 0.05
        
        segment_rec = """
• Segmenter les utilisateurs par comportement (RFM, engagement)
• Personnaliser l'expérience pour chaque segment
• Tester des recommandations produits ciblées
• Adapter les messages marketing selon le profil utilisateur
        """
        
        ax.text(0.1, y_pos, segment_rec,
                ha='left', va='top', fontsize=10, color='#34495e')
        y_pos -= 0.15
        
        # Recommandation 4
        ax.text(0.1, y_pos, '4. Prochaines Étapes de Testing',
                ha='left', va='top', fontsize=14, fontweight='bold', color='#2c3e50')
        y_pos -= 0.05
        
        next_tests = """
• Tester différentes variantes de call-to-action
• Optimiser les pages produits (images, descriptions, prix)
• Expérimenter avec les stratégies de pricing
• Tester l'impact de l'urgence et de la rareté (stocks limités)
        """
        
        ax.text(0.1, y_pos, next_tests,
                ha='left', va='top', fontsize=10, color='#34495e')
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def create_methodology_page(pdf):
    """Crée la page méthodologie"""
    fig = plt.figure(figsize=(8.5, 11))
    fig.patch.set_facecolor('white')
    ax = fig.add_subplot(111)
    ax.axis('off')
    
    # Titre
    ax.text(0.5, 0.95, 'Méthodologie',
            ha='center', va='top',
            fontsize=22, fontweight='bold', color='#2c3e50')
    
    content = """
SOURCE DES DONNÉES

• Dataset : RetailRocket E-commerce
• Période : Données réelles d'interactions utilisateurs
• Volume : 2.7M+ événements
• Types d'événements : view, addtocart, transaction


APPROCHE ANALYTIQUE

1. Nettoyage et Enrichissement des Données
   - Conversion des timestamps
   - Déduplication
   - Création de features dérivées (métriques de session, comportement utilisateur)

2. Analyse Exploratoire (EDA)
   - Distribution des événements
   - Analyse temporelle (tendances quotidiennes et horaires)
   - Segmentation utilisateurs
   - Performance produits

3. Funnel de Conversion
   - Mapping du parcours utilisateur : View → AddToCart → Transaction
   - Calcul des taux de conversion à chaque étape
   - Identification des points de friction


MÉTHODOLOGIE DES TESTS A/B

• Design : Test à deux groupes (A = contrôle, B = variante)
• Assignment : Randomisation stratifiée des utilisateurs
• Métrique principale : Taux de conversion (AddToCart → Transaction)
• Seuil de significativité : α = 0.05
• Test statistique : Z-test de proportions

Formule du Z-score :
    z = (p_B - p_A) / SE
    où SE = √[p_pooled × (1 - p_pooled) × (1/n_A + 1/n_B)]

• Intervalles de confiance : 95% (z = 1.96)
• Validation : P-value < 0.05 pour significativité


LIMITES ET CONSIDÉRATIONS

• Simulation basée sur données historiques
• Hypothèses d'homogénéité des groupes
• Effets de saisonnalité non pris en compte dans cette analyse
• Recommandations nécessitant validation en environnement de production
    """
    
    ax.text(0.1, 0.88, content,
            ha='left', va='top',
            fontsize=9, color='#34495e',
            family='monospace')
    
    pdf.savefig(fig, bbox_inches='tight')
    plt.close()


def generate_pdf_report(output_filename='Rapport_Analyse_Ecommerce_AB_Test.pdf'):
    """Génère le rapport PDF complet"""
    print(f"\n{'='*70}")
    print(f"GÉNÉRATION DU RAPPORT PDF")
    print(f"{'='*70}\n")
    
    # Charger les données
    events_df, ab_test_df = load_and_analyze_data()
    
    # Créer le PDF
    print(f"📄 Création du fichier PDF: {output_filename}")
    
    with PdfPages(output_filename) as pdf:
        # Page 1: Titre
        print("   → Page de titre...")
        create_title_page(
            pdf,
            title='Analyse E-commerce & Tests A/B',
            subtitle='Rapport détaillé d\'analyse des données et recommandations',
            author='Dashboard Analytics Team',
            date=datetime.now().strftime('%d %B %Y')
        )
        
        # Page 2: Résumé exécutif
        print("   → Résumé exécutif...")
        create_executive_summary(pdf, events_df, ab_test_df)
        
        # Section 1: Analyse des données
        print("   → Section 1: Analyse des données...")
        create_section_page(pdf, 'Analyse des Données', 1)
        
        # Distribution des événements
        print("   → Distribution des événements...")
        create_event_distribution_chart(pdf, events_df)
        
        # Analyse temporelle
        print("   → Analyse temporelle...")
        create_temporal_analysis(pdf, events_df)
        
        # Funnel de conversion
        print("   → Funnel de conversion...")
        create_funnel_analysis(pdf, events_df)
        
        # Section 2: Résultats A/B Test
        print("   → Section 2: Résultats A/B Test...")
        create_section_page(pdf, 'Résultats des Tests A/B', 2)
        create_ab_test_results(pdf, ab_test_df)
        
        # Section 3: Recommandations
        print("   → Section 3: Recommandations...")
        create_section_page(pdf, 'Recommandations Business', 3)
        create_recommendations_page(pdf, ab_test_df)
        
        # Section 4: Méthodologie
        print("   → Section 4: Méthodologie...")
        create_section_page(pdf, 'Méthodologie', 4)
        create_methodology_page(pdf)
        
        # Métadonnées du PDF
        d = pdf.infodict()
        d['Title'] = 'Rapport d\'Analyse E-commerce et Tests A/B'
        d['Author'] = 'Dashboard Analytics'
        d['Subject'] = 'Analyse de données e-commerce et résultats de tests A/B'
        d['Keywords'] = 'E-commerce, A/B Testing, Analytics, Conversion'
        d['CreationDate'] = datetime.now()
    
    print(f"\n✅ Rapport PDF généré avec succès : {output_filename}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    generate_pdf_report()
