"""
Script de test rapide pour vérifier l'intégration Dashboard + A/B Tests
========================================================================

Ce script:
1. Lance une simulation A/B test
2. Vérifie que les résultats sont sauvegardés
3. Affiche un résumé pour le dashboard

Auteur: Data Scientist
Date: 2026-01-28
"""

import subprocess
import os
import json

print("="*70)
print("🧪 TEST D'INTÉGRATION DASHBOARD + A/B TESTS")
print("="*70)

# Étape 1: Lancer la simulation A/B
print("\n📊 ÉTAPE 1: Lancement simulation A/B test...")
print("-"*70)

try:
    # Lancer le script de simulation
    result = subprocess.run(
        ['python', 'simulate_ab_test_from_data.py'],
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode == 0:
        print("✅ Simulation A/B terminée avec succès!")
    else:
        print("❌ Erreur lors de la simulation:")
        print(result.stderr)
        exit(1)
        
except subprocess.TimeoutExpired:
    print("⚠️  Timeout - la simulation prend trop de temps")
    exit(1)

# Étape 2: Vérifier les fichiers générés
print("\n📁 ÉTAPE 2: Vérification des fichiers générés...")
print("-"*70)

files_to_check = [
    'ab_test_simulation_results.csv',
    'data/clean/ab_test_results.json',
    'ab_test_results_visualization.png'
]

all_files_exist = True
for file in files_to_check:
    if os.path.exists(file):
        size = os.path.getsize(file)
        print(f"✅ {file} ({size:,} bytes)")
    else:
        print(f"❌ {file} - MANQUANT")
        all_files_exist = False

if not all_files_exist:
    print("\n⚠️  Certains fichiers sont manquants!")
    exit(1)

# Étape 3: Lire et afficher le résumé
print("\n📊 ÉTAPE 3: Résumé des résultats A/B test...")
print("-"*70)

try:
    with open('data/clean/ab_test_results.json', 'r') as f:
        results = json.load(f)
    
    print(f"\n🧪 Test: {results['test_name']}")
    print(f"📅 Date: {results['test_date']}")
    print(f"⏱️  Durée: {results['duration_days']} jours")
    
    print(f"\n📊 RÉSULTATS:")
    print(f"   Groupe A: {results['group_A']['conversion_rate']:.2%} ({results['group_A']['n_users']} users)")
    print(f"   Groupe B: {results['group_B']['conversion_rate']:.2%} ({results['group_B']['n_users']} users)")
    print(f"   Lift: {results['statistics']['relative_lift']:+.1f}%")
    
    if results['statistics']['significant']:
        print(f"\n✅ SIGNIFICATIF (p = {results['statistics']['p_value']:.4f})")
    else:
        print(f"\n⚠️  NON SIGNIFICATIF (p = {results['statistics']['p_value']:.4f})")
    
    print(f"\n💰 IMPACT BUSINESS:")
    print(f"   Revenus additionnels/an: {results['business_impact']['additional_revenue_year']:,.0f}€")
    print(f"   ROI: {results['business_impact']['roi_percent']:.0f}%")
    
except Exception as e:
    print(f"❌ Erreur lors de la lecture du JSON: {e}")
    exit(1)

# Étape 4: Instructions pour le dashboard
print("\n" + "="*70)
print("✅ INTÉGRATION RÉUSSIE!")
print("="*70)
print("\n📌 PROCHAINES ÉTAPES:")
print("\n1. Lancer le dashboard:")
print("   python dashboard_app.py")
print("\n2. Ouvrir votre navigateur:")
print("   http://localhost:8050/abtests")
print("\n3. Vous verrez:")
print("   • Comparaison des groupes A/B")
print("   • Intervalle de confiance")
print("   • Statistiques détaillées")
print("   • Impact business")
print("   • Recommandations automatiques")
print("\n" + "="*70)
print("🎉 Prêt à visualiser vos A/B tests!")
print("="*70 + "\n")
