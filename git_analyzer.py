#!/usr/bin/env python
"""
Script pour analyser l'historique Git du projet GIRREX.
"""

import subprocess
import json
from datetime import datetime

def run_git_command(command):
    """Exécute une commande Git et retourne le résultat."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd='.',
            encoding='utf-8'
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Erreur: {e}"

def get_commit_log(limit=20):
    """Récupère l'historique des commits."""
    print("📜 HISTORIQUE DES COMMITS (20 derniers)\n" + "="*70)
    
    cmd = f'git log --oneline --graph --decorate -n {limit}'
    output = run_git_command(cmd)
    print(output)

def get_branches():
    """Liste toutes les branches."""
    print("\n\n🌿 BRANCHES\n" + "="*70)
    
    # Branches locales
    print("\nBranches locales:")
    cmd = 'git branch -v'
    output = run_git_command(cmd)
    print(output)
    
    # Branches distantes
    print("\nBranches distantes:")
    cmd = 'git branch -r'
    output = run_git_command(cmd)
    print(output)

def get_current_status():
    """Affiche le statut actuel."""
    print("\n\n📊 STATUT ACTUEL\n" + "="*70)
    
    # Branche courante
    branch = run_git_command('git branch --show-current')
    print(f"Branche actuelle : {branch}")
    
    # Dernier commit
    last_commit = run_git_command('git log -1 --oneline')
    print(f"Dernier commit : {last_commit}")
    
    # Statut
    print("\nFichiers modifiés:")
    status = run_git_command('git status --short')
    if status:
        print(status)
    else:
        print("  Aucune modification")
    
    # Fichiers non trackés
    untracked = run_git_command('git ls-files --others --exclude-standard')
    if untracked:
        print("\nFichiers non trackés:")
        for file in untracked.split('\n')[:10]:  # Limite à 10
            print(f"  - {file}")

def get_file_history(filepath):
    """Affiche l'historique d'un fichier spécifique."""
    print(f"\n\n📄 HISTORIQUE DE {filepath}\n" + "="*70)
    
    cmd = f'git log --oneline --follow -- "{filepath}"'
    output = run_git_command(cmd)
    
    if output:
        print(output)
    else:
        print(f"Aucun historique trouvé pour {filepath}")

def compare_branches(branch1, branch2):
    """Compare deux branches."""
    print(f"\n\n🔀 COMPARAISON {branch1} ↔ {branch2}\n" + "="*70)
    
    # Commits différents
    print(f"\nCommits dans {branch1} mais pas dans {branch2}:")
    cmd = f'git log {branch2}..{branch1} --oneline'
    output = run_git_command(cmd)
    if output:
        print(output)
    else:
        print("  Aucun")
    
    print(f"\nCommits dans {branch2} mais pas dans {branch1}:")
    cmd = f'git log {branch1}..{branch2} --oneline'
    output = run_git_command(cmd)
    if output:
        print(output)
    else:
        print("  Aucun")
    
    # Fichiers différents
    print(f"\nFichiers modifiés entre les deux branches:")
    cmd = f'git diff --name-status {branch1}..{branch2}'
    output = run_git_command(cmd)
    if output:
        lines = output.split('\n')[:20]  # Limite à 20 fichiers
        for line in lines:
            print(f"  {line}")
        if len(output.split('\n')) > 20:
            print(f"  ... et {len(output.split('\n')) - 20} autres fichiers")
    else:
        print("  Aucune différence")

def show_commit_details(commit_hash):
    """Affiche les détails d'un commit."""
    print(f"\n\n📝 DÉTAILS DU COMMIT {commit_hash}\n" + "="*70)
    
    cmd = f'git show {commit_hash} --stat'
    output = run_git_command(cmd)
    print(output)

def get_contributors():
    """Liste les contributeurs."""
    print("\n\n👥 CONTRIBUTEURS\n" + "="*70)
    
    cmd = 'git shortlog -sn --all'
    output = run_git_command(cmd)
    print(output)

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║         🔍 ANALYSE GIT DU PROJET GIRREX                     ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Informations générales
    get_current_status()
    get_branches()
    get_commit_log()
    get_contributors()
    
    print("\n\n" + "="*70)
    print("✅ Analyse terminée !")
    print("\nPour des analyses spécifiques, tu peux utiliser :")
    print("  - compare_branches('main', 'dev-feedback')")
    print("  - get_file_history('core/models/rh.py')")
    print("  - show_commit_details('abc1234')")

if __name__ == '__main__':
    main()
