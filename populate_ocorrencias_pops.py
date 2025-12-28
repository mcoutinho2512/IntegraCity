#!/usr/bin/env python
"""
Script para popular o Sistema de Gerenciamento de Ocorrências
- Cria categorias de ocorrências
- Cria agências responsáveis
- Importa POPs dos arquivos PDF existentes
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sitecor.settings')
sys.path.insert(0, '/home/administrador/integracity')
django.setup()

from aplicativo.models import (
    CategoriaOcorrencia,
    AgenciaResponsavel,
    ProcedimentoOperacional
)


def criar_categorias():
    """Criar categorias de ocorrências"""
    print("\n=== CRIANDO CATEGORIAS ===\n")

    categorias = [
        {
            'nome': 'Transito e Acidentes',
            'descricao': 'Acidentes de transito, enguicos, atropelamentos e outros eventos relacionados a mobilidade urbana.',
            'icone': 'fa-car-crash',
            'cor': '#FF4444',
            'ordem': 1
        },
        {
            'nome': 'Incendios',
            'descricao': 'Incendios em veiculos, imoveis, vegetacao e outras estruturas.',
            'icone': 'fa-fire',
            'cor': '#FF6B00',
            'ordem': 2
        },
        {
            'nome': 'Infraestrutura',
            'descricao': 'Problemas de infraestrutura urbana como queda de arvores, postes, buracos e vazamentos.',
            'icone': 'fa-tools',
            'cor': '#FFB800',
            'ordem': 3
        },
        {
            'nome': 'Emergencias Ambientais',
            'descricao': 'Alagamentos, enchentes, deslizamentos e outros eventos climaticos/ambientais.',
            'icone': 'fa-water',
            'cor': '#00D4FF',
            'ordem': 4
        },
        {
            'nome': 'Animais',
            'descricao': 'Resgate e remocao de animais, animais em locais publicos.',
            'icone': 'fa-paw',
            'cor': '#4CAF50',
            'ordem': 5
        },
        {
            'nome': 'Eventos Especiais',
            'descricao': 'Manifestacoes, operacoes policiais, eventos nao programados e situacoes especiais.',
            'icone': 'fa-exclamation-triangle',
            'cor': '#B537F2',
            'ordem': 6
        },
    ]

    for cat_data in categorias:
        cat, created = CategoriaOcorrencia.objects.get_or_create(
            nome=cat_data['nome'],
            defaults=cat_data
        )
        status = "CRIADA" if created else "JA EXISTE"
        print(f"  [{status}] {cat.nome}")

    print(f"\nTotal de categorias: {CategoriaOcorrencia.objects.count()}")


def criar_agencias():
    """Criar agências responsáveis"""
    print("\n=== CRIANDO AGENCIAS ===\n")

    agencias = [
        {
            'nome': 'Corpo de Bombeiros Militar do Estado do Rio de Janeiro',
            'sigla': 'CBMERJ',
            'descricao': 'Corpo de Bombeiros - Combate a incendios, resgates e emergencias',
            'telefone': '193',
            'icone': 'fa-fire-extinguisher',
            'cor': '#FF4444'
        },
        {
            'nome': 'Policia Militar do Estado do Rio de Janeiro',
            'sigla': 'PMERJ',
            'descricao': 'Policia Militar - Seguranca publica e policiamento ostensivo',
            'telefone': '190',
            'icone': 'fa-shield-alt',
            'cor': '#0066CC'
        },
        {
            'nome': 'Policia Civil do Estado do Rio de Janeiro',
            'sigla': 'PCERJ',
            'descricao': 'Policia Civil - Investigacao criminal',
            'telefone': '197',
            'icone': 'fa-user-shield',
            'cor': '#003366'
        },
        {
            'nome': 'Servico de Atendimento Movel de Urgencia',
            'sigla': 'SAMU',
            'descricao': 'SAMU - Atendimento pre-hospitalar de urgencia',
            'telefone': '192',
            'icone': 'fa-ambulance',
            'cor': '#FF6B00'
        },
        {
            'nome': 'Companhia de Engenharia de Trafego',
            'sigla': 'CET-Rio',
            'descricao': 'CET-Rio - Gerenciamento de trafego e sinalizacao',
            'telefone': '1746',
            'icone': 'fa-traffic-light',
            'cor': '#FFB800'
        },
        {
            'nome': 'Light Servicos de Eletricidade',
            'sigla': 'Light',
            'descricao': 'Light - Distribuicao de energia eletrica',
            'telefone': '0800 282 0120',
            'icone': 'fa-bolt',
            'cor': '#FFCC00'
        },
        {
            'nome': 'Companhia Estadual de Aguas e Esgotos',
            'sigla': 'CEDAE',
            'descricao': 'CEDAE - Abastecimento de agua e tratamento de esgoto',
            'telefone': '0800 282 1195',
            'icone': 'fa-tint',
            'cor': '#00BFFF'
        },
        {
            'nome': 'Companhia Municipal de Limpeza Urbana',
            'sigla': 'COMLURB',
            'descricao': 'COMLURB - Limpeza urbana e coleta de residuos',
            'telefone': '1746',
            'icone': 'fa-trash',
            'cor': '#4CAF50'
        },
        {
            'nome': 'Secretaria de Conservacao',
            'sigla': 'SECONSERVA',
            'descricao': 'SECONSERVA - Conservacao de vias e espacos publicos',
            'telefone': '1746',
            'icone': 'fa-road',
            'cor': '#795548'
        },
        {
            'nome': 'Defesa Civil Municipal',
            'sigla': 'Defesa Civil',
            'descricao': 'Defesa Civil - Prevencao e resposta a desastres',
            'telefone': '199',
            'icone': 'fa-hands-helping',
            'cor': '#FF5722'
        },
        {
            'nome': 'Guarda Municipal do Rio de Janeiro',
            'sigla': 'GM-Rio',
            'descricao': 'Guarda Municipal - Protecao de bens e servicos municipais',
            'telefone': '153',
            'icone': 'fa-user-tie',
            'cor': '#2196F3'
        },
        {
            'nome': 'Centro de Controle de Zoonoses',
            'sigla': 'CCZ',
            'descricao': 'CCZ - Controle de zoonoses e animais',
            'telefone': '1746',
            'icone': 'fa-paw',
            'cor': '#8BC34A'
        },
        {
            'nome': 'Naturgas',
            'sigla': 'Naturgas',
            'descricao': 'Naturgas - Distribuicao de gas natural',
            'telefone': '0800 024 0197',
            'icone': 'fa-fire',
            'cor': '#FF9800'
        },
        {
            'nome': 'Secretaria Municipal de Saude',
            'sigla': 'SMS',
            'descricao': 'Secretaria de Saude - Atendimento de saude publica',
            'telefone': '1746',
            'icone': 'fa-hospital',
            'cor': '#E91E63'
        },
    ]

    for ag_data in agencias:
        ag, created = AgenciaResponsavel.objects.get_or_create(
            sigla=ag_data['sigla'],
            defaults=ag_data
        )
        status = "CRIADA" if created else "JA EXISTE"
        print(f"  [{status}] {ag.sigla} - {ag.nome}")

    print(f"\nTotal de agencias: {AgenciaResponsavel.objects.count()}")


def importar_pops():
    """Importar POPs dos arquivos PDF"""
    print("\n=== IMPORTANDO POPs ===\n")

    # Mapeamento de POPs para categorias
    mapeamento_categorias = {
        # Transito e Acidentes
        'OPE-POP-001': 'Transito e Acidentes',
        'OPE-POP-002': 'Transito e Acidentes',
        'OPE-POP-003': 'Transito e Acidentes',
        'OPE-POP-012': 'Transito e Acidentes',
        'OPE-POP-020': 'Transito e Acidentes',
        'OPE-POP-022': 'Transito e Acidentes',
        'OPE-POP-040': 'Transito e Acidentes',
        'OPE-POP-041': 'Transito e Acidentes',

        # Incendios
        'OPE-POP-004': 'Incendios',
        'OPE-POP-007': 'Incendios',
        'OPE-POP-013': 'Incendios',
        'OPE-POP-014': 'Incendios',
        'OPE-POP-032': 'Incendios',

        # Infraestrutura
        'OPE-POP-008': 'Infraestrutura',
        'OPE-POP-010': 'Infraestrutura',
        'OPE-POP-011': 'Infraestrutura',
        'OPE-POP-015': 'Infraestrutura',
        'OPE-POP-016': 'Infraestrutura',
        'OPE-POP-021': 'Infraestrutura',
        'OPE-POP-023': 'Infraestrutura',
        'OPE-POP-031': 'Infraestrutura',
        'OPE-POP-033': 'Infraestrutura',
        'OPE-POP-034': 'Infraestrutura',
        'OPE-POP-039': 'Infraestrutura',

        # Emergencias Ambientais
        'OPE-POP-005': 'Emergencias Ambientais',
        'OPE-POP-018': 'Emergencias Ambientais',
        'OPE-POP-025': 'Emergencias Ambientais',
        'OPE-POP-027': 'Emergencias Ambientais',
        'OPE-POP-028': 'Emergencias Ambientais',
        'OPE-POP-029': 'Emergencias Ambientais',
        'OPE-POP-030': 'Emergencias Ambientais',

        # Animais
        'OPE-POP-035': 'Animais',
        'OPE-POP-036': 'Animais',
        'OPE-POP-037': 'Animais',
        'OPE-POP-038': 'Animais',

        # Eventos Especiais
        'OPE-POP-006': 'Eventos Especiais',
        'OPE-POP-009': 'Eventos Especiais',
        'OPE-POP-017': 'Eventos Especiais',
        'OPE-POP-019': 'Eventos Especiais',
        'OPE-POP-024': 'Eventos Especiais',
        'OPE-POP-026': 'Eventos Especiais',
        'OPE-POP-042': 'Eventos Especiais',
    }

    # Mapeamento de agencias principais por POP
    mapeamento_agencias = {
        'OPE-POP-001': ['CBMERJ', 'PMERJ', 'CET-Rio'],
        'OPE-POP-002': ['CBMERJ', 'SAMU', 'PMERJ', 'CET-Rio'],
        'OPE-POP-003': ['CBMERJ', 'SAMU', 'PMERJ', 'PCERJ', 'CET-Rio'],
        'OPE-POP-004': ['CBMERJ', 'PMERJ', 'CET-Rio'],
        'OPE-POP-005': ['Defesa Civil', 'CET-Rio', 'COMLURB'],
        'OPE-POP-006': ['PMERJ', 'GM-Rio', 'CET-Rio'],
        'OPE-POP-007': ['CBMERJ', 'PMERJ', 'Light'],
        'OPE-POP-008': ['CET-Rio'],
        'OPE-POP-009': ['PMERJ', 'GM-Rio'],
        'OPE-POP-010': ['COMLURB', 'CET-Rio', 'Light'],
        'OPE-POP-011': ['Light', 'CET-Rio', 'CBMERJ'],
        'OPE-POP-012': ['CBMERJ', 'PMERJ', 'CET-Rio'],
        'OPE-POP-013': ['CBMERJ', 'COMLURB'],
        'OPE-POP-014': ['CBMERJ', 'CET-Rio', 'PMERJ'],
        'OPE-POP-015': ['CEDAE', 'CET-Rio'],
        'OPE-POP-016': ['Light', 'Defesa Civil'],
        'OPE-POP-017': ['CBMERJ', 'PMERJ', 'Defesa Civil'],
        'OPE-POP-018': ['CBMERJ', 'Naturgas', 'PMERJ'],
        'OPE-POP-019': ['PMERJ', 'GM-Rio', 'CET-Rio'],
        'OPE-POP-020': ['SAMU', 'PMERJ', 'CBMERJ'],
        'OPE-POP-021': ['SECONSERVA', 'CET-Rio'],
        'OPE-POP-022': ['CBMERJ', 'PMERJ', 'CET-Rio'],
        'OPE-POP-023': ['SECONSERVA', 'CET-Rio'],
        'OPE-POP-024': ['PMERJ', 'PCERJ'],
        'OPE-POP-025': ['Defesa Civil', 'CBMERJ', 'PMERJ'],
        'OPE-POP-026': ['Defesa Civil'],
        'OPE-POP-027': ['Defesa Civil', 'CET-Rio', 'CBMERJ'],
        'OPE-POP-028': ['Defesa Civil', 'CBMERJ', 'PMERJ'],
        'OPE-POP-029': ['Defesa Civil', 'CET-Rio'],
        'OPE-POP-030': ['CBMERJ', 'Defesa Civil'],
        'OPE-POP-031': ['CEDAE', 'COMLURB', 'CET-Rio'],
        'OPE-POP-032': ['CBMERJ', 'COMLURB'],
        'OPE-POP-033': ['COMLURB', 'Light', 'CET-Rio'],
        'OPE-POP-034': ['COMLURB', 'CET-Rio'],
        'OPE-POP-035': ['CCZ', 'CBMERJ'],
        'OPE-POP-036': ['COMLURB', 'CCZ'],
        'OPE-POP-037': ['CBMERJ', 'CCZ'],
        'OPE-POP-038': ['CCZ', 'GM-Rio'],
        'OPE-POP-039': ['Defesa Civil', 'CBMERJ', 'SECONSERVA'],
        'OPE-POP-040': ['PMERJ', 'CCZ', 'CET-Rio'],
        'OPE-POP-041': ['CCZ', 'GM-Rio'],
        'OPE-POP-042': ['PMERJ', 'CBMERJ', 'Defesa Civil'],
    }

    pops_dir = '/home/administrador/integracity/static/pop/'

    if not os.path.exists(pops_dir):
        print(f"  [ERRO] Diretorio nao encontrado: {pops_dir}")
        return

    pdf_files = [f for f in os.listdir(pops_dir) if f.endswith('.pdf') and 'OPE-POP' in f]
    pdf_files.sort()

    print(f"  Encontrados {len(pdf_files)} arquivos PDF\n")

    for filename in pdf_files:
        # Extrair codigo e titulo do nome do arquivo
        # Formato: OPE-POP-XXX-R00 - Titulo.pdf
        try:
            parts = filename.replace('.pdf', '').split(' - ', 1)
            codigo = parts[0].strip()  # OPE-POP-XXX-R00

            # Extrair codigo base (sem versao)
            codigo_base = '-'.join(codigo.split('-')[:3])  # OPE-POP-XXX

            titulo = parts[1].strip() if len(parts) > 1 else 'Sem titulo'

            # Obter categoria
            categoria_nome = mapeamento_categorias.get(codigo_base, 'Eventos Especiais')
            try:
                categoria = CategoriaOcorrencia.objects.get(nome=categoria_nome)
            except CategoriaOcorrencia.DoesNotExist:
                print(f"  [ERRO] Categoria nao encontrada: {categoria_nome}")
                continue

            # Criar ou atualizar POP
            pop, created = ProcedimentoOperacional.objects.update_or_create(
                codigo=codigo,
                defaults={
                    'titulo': titulo,
                    'categoria': categoria,
                    'arquivo_path': f'pop/{filename}',
                    'versao': codigo.split('-')[-1] if '-R' in codigo else 'R00',
                    'ativo': True
                }
            )

            # Adicionar agencias
            agencias_siglas = mapeamento_agencias.get(codigo_base, [])
            for sigla in agencias_siglas:
                try:
                    agencia = AgenciaResponsavel.objects.get(sigla=sigla)
                    pop.agencias.add(agencia)
                except AgenciaResponsavel.DoesNotExist:
                    pass

            status = "CRIADO" if created else "ATUALIZADO"
            print(f"  [{status}] {codigo} - {titulo[:50]}...")

        except Exception as e:
            print(f"  [ERRO] Arquivo {filename}: {str(e)}")

    print(f"\nTotal de POPs: {ProcedimentoOperacional.objects.count()}")


def main():
    print("=" * 60)
    print("  POPULANDO SISTEMA DE GERENCIAMENTO DE OCORRENCIAS")
    print("  IntegraCity - Command Center")
    print("=" * 60)

    criar_categorias()
    criar_agencias()
    importar_pops()

    print("\n" + "=" * 60)
    print("  IMPORTACAO CONCLUIDA COM SUCESSO!")
    print("=" * 60)

    print("\nResumo:")
    print(f"  - Categorias: {CategoriaOcorrencia.objects.count()}")
    print(f"  - Agencias: {AgenciaResponsavel.objects.count()}")
    print(f"  - POPs: {ProcedimentoOperacional.objects.count()}")
    print("")


if __name__ == '__main__':
    main()
