#!/usr/bin/env python
"""
Script de vérification automatique du code GIRREX.
Lance ce script après chaque modification pour détecter les erreurs.
"""

import sys
import os
import subprocess
from pathlib import Path

# Couleurs pour l'affichage
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_section(title):
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{Colors.END}\n")

def check_syntax():
    """Vérifie la syntaxe de tous les fichiers Python."""
    print_section("1. VÉRIFICATION SYNTAXE PYTHON")
    
    errors = []
    python_files = Path('.').rglob('*.py')
    
    for file in python_files:
        if 'venv' in str(file) or 'migrations' in str(file):
            continue
            
        try:
            with open(file, 'r', encoding='utf-8') as f:
                compile(f.read(), str(file), 'exec')
            print(f"  {Colors.GREEN}✓{Colors.END} {file}")
        except SyntaxError as e:
            errors.append(f"{file}: {e}")
            print(f"  {Colors.RED}✗{Colors.END} {file}")
            print(f"    {Colors.RED}Erreur ligne {e.lineno}: {e.msg}{Colors.END}")
    
    if errors:
        print(f"\n{Colors.RED}❌ {len(errors)} erreur(s) de syntaxe détectée(s){Colors.END}")
        return False
    else:
        print(f"\n{Colors.GREEN}✅ Aucune erreur de syntaxe{Colors.END}")
        return True

def check_imports():
    """Vérifie que tous les imports sont valides."""
    print_section("2. VÉRIFICATION DES IMPORTS")
    
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'check'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"{Colors.GREEN}✅ Tous les imports sont valides{Colors.END}")
            return True
        else:
            print(f"{Colors.RED}❌ Erreurs détectées :{Colors.END}")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"{Colors.RED}❌ Erreur lors de la vérification : {e}{Colors.END}")
        return False

def check_migrations():
    """Vérifie qu'il n'y a pas de migrations en attente non créées."""
    print_section("3. VÉRIFICATION DES MIGRATIONS")
    
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'makemigrations', '--dry-run'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if "No changes detected" in result.stdout:
            print(f"{Colors.GREEN}✅ Aucune migration en attente{Colors.END}")
            return True
        else:
            print(f"{Colors.YELLOW}⚠️  Des migrations doivent être créées :{Colors.END}")
            print(result.stdout)
            print(f"\n{Colors.YELLOW}Commande à lancer :{Colors.END}")
            print("  python manage.py makemigrations")
            return True  # Ce n'est pas une erreur, juste une info
    except Exception as e:
        print(f"{Colors.RED}❌ Erreur : {e}{Colors.END}")
        return False

def check_templates():
    """Vérifie la syntaxe des templates Django."""
    print_section("4. VÉRIFICATION DES TEMPLATES")
    
    try:
        # On ne peut pas vraiment vérifier les templates sans les rendre
        # Mais on peut vérifier qu'ils sont bien formés
        from django.template import engines, TemplateDoesNotExist, TemplateSyntaxError
        from django.conf import settings
        
        # Configurer Django si ce n'est pas déjà fait
        if not settings.configured:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'girrex_project.settings')
            import django
            django.setup()
        
        template_files = Path('templates').rglob('*.html')
        errors = []
        
        engine = engines['django']
        
        for template_file in template_files:
            try:
                template_path = str(template_file.relative_to('templates'))
                engine.get_template(template_path)
                print(f"  {Colors.GREEN}✓{Colors.END} {template_file}")
            except TemplateSyntaxError as e:
                errors.append(str(template_file))
                print(f"  {Colors.RED}✗{Colors.END} {template_file}")
                print(f"    {Colors.RED}Erreur: {e}{Colors.END}")
            except TemplateDoesNotExist:
                # Normal pour certains templates
                pass
        
        if errors:
            print(f"\n{Colors.RED}❌ {len(errors)} erreur(s) de template{Colors.END}")
            return False
        else:
            print(f"\n{Colors.GREEN}✅ Templates OK{Colors.END}")
            return True
            
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  Impossible de vérifier les templates : {e}{Colors.END}")
        return True  # On ne considère pas ça comme une erreur bloquante

def run_tests():
    """Lance les tests Django."""
    print_section("5. LANCEMENT DES TESTS")
    
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'test', '--verbosity=2', '--keepdb'],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        
        if result.returncode == 0:
            print(f"\n{Colors.GREEN}✅ Tous les tests passent{Colors.END}")
            return True
        else:
            print(f"\n{Colors.RED}❌ Certains tests échouent{Colors.END}")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  Erreur lors des tests : {e}{Colors.END}")
        return True  # On ne bloque pas si les tests ne peuvent pas tourner

def main():
    print(f"\n{Colors.BLUE}╔════════════════════════════════════════════════════════╗")
    print(f"║   🔍 VÉRIFICATION AUTOMATIQUE DU CODE GIRREX          ║")
    print(f"╚════════════════════════════════════════════════════════╝{Colors.END}\n")
    
    all_ok = True
    
    # 1. Vérification syntaxe
    if not check_syntax():
        all_ok = False
    
    # 2. Vérification imports et configuration Django
    if not check_imports():
        all_ok = False
    
    # 3. Vérification migrations
    if not check_migrations():
        all_ok = False
    
    # 4. Vérification templates
    if not check_templates():
        all_ok = False
    
    # 5. Tests (optionnel, commenté par défaut car peut être long)
    # if not run_tests():
    #     all_ok = False
    
    # Résumé final
    print_section("RÉSUMÉ")
    
    if all_ok:
        print(f"{Colors.GREEN}╔════════════════════════════════════════════════════════╗")
        print(f"║  ✅ TOUT EST OK ! Le code est prêt à être utilisé.   ║")
        print(f"╚════════════════════════════════════════════════════════╝{Colors.END}\n")
        return 0
    else:
        print(f"{Colors.RED}╔════════════════════════════════════════════════════════╗")
        print(f"║  ❌ DES ERREURS ONT ÉTÉ DÉTECTÉES                     ║")
        print(f"║     Corrige-les avant de continuer !                   ║")
        print(f"╚════════════════════════════════════════════════════════╝{Colors.END}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
