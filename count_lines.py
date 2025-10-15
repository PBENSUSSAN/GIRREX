#!/usr/bin/env python
"""
Compte les lignes de code du projet GIRREX.
"""

import os
from pathlib import Path
from collections import defaultdict

# Couleurs pour l'affichage
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def count_lines(file_path):
    """Compte les lignes dans un fichier."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            total = len(lines)
            code = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
            comments = sum(1 for line in lines if line.strip().startswith('#'))
            blank = total - code - comments
            return total, code, comments, blank
    except Exception as e:
        return 0, 0, 0, 0

def analyze_project():
    """Analyse le projet GIRREX."""
    
    # Extensions à compter
    extensions = {
        'Python': ['.py'],
        'HTML': ['.html'],
        'CSS': ['.css'],
        'JavaScript': ['.js'],
        'JSON': ['.json'],
        'Markdown': ['.md'],
        'Text': ['.txt'],
    }
    
    # Dossiers à exclure
    exclude_dirs = {'venv', '__pycache__', '.git', 'migrations', 'static', 'media', 'node_modules'}
    
    stats_by_type = defaultdict(lambda: {'files': 0, 'total': 0, 'code': 0, 'comments': 0, 'blank': 0})
    stats_by_app = defaultdict(lambda: {'files': 0, 'total': 0, 'code': 0, 'comments': 0, 'blank': 0})
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}")
    print(f"  📊 ANALYSE DU PROJET GIRREX")
    print(f"{'='*70}{Colors.END}\n")
    
    print("🔍 Analyse en cours...\n")
    
    # Parcourir tous les fichiers
    for root, dirs, files in os.walk('.'):
        # Exclure certains dossiers
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            file_path = Path(root) / file
            file_ext = file_path.suffix
            
            # Déterminer le type de fichier
            file_type = None
            for type_name, exts in extensions.items():
                if file_ext in exts:
                    file_type = type_name
                    break
            
            if not file_type:
                continue
            
            # Compter les lignes
            total, code, comments, blank = count_lines(file_path)
            
            if total == 0:
                continue
            
            # Stats par type
            stats_by_type[file_type]['files'] += 1
            stats_by_type[file_type]['total'] += total
            stats_by_type[file_type]['code'] += code
            stats_by_type[file_type]['comments'] += comments
            stats_by_type[file_type]['blank'] += blank
            
            # Stats par application (uniquement pour Python)
            if file_type == 'Python':
                parts = Path(root).parts
                if len(parts) > 0 and parts[0] != '.':
                    app_name = parts[0]
                    stats_by_app[app_name]['files'] += 1
                    stats_by_app[app_name]['total'] += total
                    stats_by_app[app_name]['code'] += code
                    stats_by_app[app_name]['comments'] += comments
                    stats_by_app[app_name]['blank'] += blank
    
    # Affichage des résultats
    print(f"{Colors.BOLD}{Colors.GREEN}📈 STATISTIQUES PAR TYPE DE FICHIER{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{'Type':<15} {'Fichiers':>10} {'Total':>12} {'Code':>12} {'Commentaires':>12} {'Vides':>12}")
    print(f"{Colors.BLUE}{'-'*70}{Colors.END}")
    
    grand_total_files = 0
    grand_total_lines = 0
    grand_total_code = 0
    grand_total_comments = 0
    grand_total_blank = 0
    
    for file_type in sorted(stats_by_type.keys()):
        stats = stats_by_type[file_type]
        print(f"{file_type:<15} {stats['files']:>10} {stats['total']:>12,} {stats['code']:>12,} {stats['comments']:>12,} {stats['blank']:>12,}")
        grand_total_files += stats['files']
        grand_total_lines += stats['total']
        grand_total_code += stats['code']
        grand_total_comments += stats['comments']
        grand_total_blank += stats['blank']
    
    print(f"{Colors.BLUE}{'-'*70}{Colors.END}")
    print(f"{Colors.BOLD}{'TOTAL':<15} {grand_total_files:>10} {grand_total_lines:>12,} {grand_total_code:>12,} {grand_total_comments:>12,} {grand_total_blank:>12,}{Colors.END}")
    
    # Stats Python par application
    if stats_by_app:
        print(f"\n{Colors.BOLD}{Colors.GREEN}🐍 STATISTIQUES PYTHON PAR APPLICATION{Colors.END}")
        print(f"{Colors.BLUE}{'='*70}{Colors.END}")
        print(f"{'Application':<20} {'Fichiers':>10} {'Total':>12} {'Code':>12}")
        print(f"{Colors.BLUE}{'-'*70}{Colors.END}")
        
        for app_name in sorted(stats_by_app.keys()):
            stats = stats_by_app[app_name]
            print(f"{app_name:<20} {stats['files']:>10} {stats['total']:>12,} {stats['code']:>12,}")
    
    # Résumé final
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{'='*70}")
    print(f"  📊 RÉSUMÉ")
    print(f"{'='*70}{Colors.END}")
    print(f"\n{Colors.BOLD}Total de fichiers :{Colors.END} {Colors.GREEN}{grand_total_files:,}{Colors.END}")
    print(f"{Colors.BOLD}Total de lignes :{Colors.END} {Colors.GREEN}{grand_total_lines:,}{Colors.END}")
    print(f"{Colors.BOLD}Lignes de code :{Colors.END} {Colors.GREEN}{grand_total_code:,}{Colors.END}")
    print(f"{Colors.BOLD}Commentaires :{Colors.END} {Colors.YELLOW}{grand_total_comments:,}{Colors.END}")
    print(f"{Colors.BOLD}Lignes vides :{Colors.END} {Colors.BLUE}{grand_total_blank:,}{Colors.END}")
    
    # Pourcentages
    if grand_total_lines > 0:
        pct_code = (grand_total_code / grand_total_lines) * 100
        pct_comments = (grand_total_comments / grand_total_lines) * 100
        pct_blank = (grand_total_blank / grand_total_lines) * 100
        
        print(f"\n{Colors.BOLD}Répartition :{Colors.END}")
        print(f"  Code : {pct_code:.1f}%")
        print(f"  Commentaires : {pct_comments:.1f}%")
        print(f"  Lignes vides : {pct_blank:.1f}%")
    
    # Estimations
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}")
    print(f"  💡 ESTIMATIONS")
    print(f"{'='*70}{Colors.END}")
    
    # Estimation temps de développement (moyenne: 10 lignes de code par heure)
    hours = grand_total_code / 10
    days = hours / 8
    weeks = days / 5
    
    print(f"\nTemps de développement estimé (10 lignes/heure) :")
    print(f"  {Colors.GREEN}{hours:,.0f}{Colors.END} heures")
    print(f"  {Colors.GREEN}{days:,.0f}{Colors.END} jours (8h/jour)")
    print(f"  {Colors.GREEN}{weeks:,.1f}{Colors.END} semaines (5 jours/semaine)")
    
    # Estimation du coût (si développeur à 50€/heure)
    cost = hours * 50
    print(f"\nValeur estimée du projet (50€/heure) :")
    print(f"  {Colors.GREEN}{cost:,.0f}€{Colors.END}")
    
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}\n")

if __name__ == '__main__':
    analyze_project()
