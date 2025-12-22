# populate_db_v2.py — diagnóstico de modelos + população robusta
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sitecor.settings')

import django
django.setup()

from datetime import datetime, timedelta
from django.db import transaction
from django.apps import apps

Sirene = apps.get_model('aplicativo', 'Sirene')
DadosSirene = apps.get_model('aplicativo', 'DadosSirene')
Evento = apps.get_model('aplicativo', 'Evento')
Ocorrencias = apps.get_model('aplicativo', 'Ocorrencias')

def field_specs(Model):
    specs = []
    for f in Model._meta.get_fields():
        if hasattr(f, 'attname'):
            specs.append({
                'name': f.name,
                'type': f.get_internal_type(),
                'null': getattr(f, 'null', False),
                'unique': getattr(f, 'unique', False),
                'primary_key': getattr(f, 'primary_key', False),
            })
    return specs

def index_fields(Model):
    return {f['name']: f for f in field_specs(Model)}

def first_existing_field(fields_set, *candidates):
    for c in candidates:
        if c in fields_set:
            return c
    return None

def try_key(d, *cands, default=None):
    for c in cands:
        if c in d and d[c] is not None:
            return d[c]
    return default

def print_model_info():
    print('\n=== DIAGNÓSTICO DE MODELOS ===')
    for Model in (Sirene, Evento, Ocorrencias):
        print(f'\n[{Model.__name__}]')
        for spec in field_specs(Model):
            print(f" - {spec['name']}: {spec['type']} null={spec['null']} unique={spec['unique']} pk={spec['primary_key']}")

def populate():
    print('\n=== POPULAÇÃO ROBUSTA ===')

    sir_fields = index_fields(Sirene)
    ev_fields  = index_fields(Evento)
    oc_fields  = index_fields(Ocorrencias)

    # Dados de teste
    sirenes_data = [
        {'nome': 'Sirene Rocinha',            'lat': -22.9881, 'lon': -43.2497, 'municipio': 'Rio de Janeiro', 'prior': 'alta'},
        {'nome': 'Sirene Vidigal',            'lat': -22.9925, 'lon': -43.2318, 'municipio': 'Rio de Janeiro', 'prior': 'media'},
        {'nome': 'Sirene Alto da Boa Vista',  'lat': -22.9647, 'lon': -43.2844, 'municipio': 'Rio de Janeiro', 'prior': 'media'},
        {'nome': 'Sirene Morro dos Prazeres', 'lat': -22.9158, 'lon': -43.1842, 'municipio': 'Rio de Janeiro', 'prior': 'muito_alta'},
    ]
    eventos_data = [
        {'nome': 'Carnaval 2025',        'tipo': 'evento', 'lat': -22.9068, 'lon': -43.1729, 'prioridade': 'alta',       'quando': datetime.now() + timedelta(days=30)},
        {'nome': 'Rock in Rio 2025',     'tipo': 'evento', 'lat': -22.9771, 'lon': -43.3951, 'prioridade': 'alta',       'quando': datetime.now() + timedelta(days=60)},
        {'nome': 'Réveillon Copacabana', 'tipo': 'evento', 'lat': -22.9711, 'lon': -43.1822, 'prioridade': 'muito_alta', 'quando': datetime.now() + timedelta(days=90)},
    ]
    ocorrencias_data = [
        {'descricao': 'Alagamento Av. Brasil',  'tipo': 'alagamento',   'lat': -22.8897, 'lon': -43.3144, 'prior': 'alta'},
        {'descricao': 'Queda de árvore Tijuca', 'tipo': 'obstrucao',    'lat': -22.9249, 'lon': -43.2311, 'prior': 'media'},
        {'descricao': 'Deslizamento Rocinha',   'tipo': 'deslizamento', 'lat': -22.9881, 'lon': -43.2497, 'prior': 'muito_alta'},
    ]

    # Descobrir campos reais (nomes podem ser diferentes do legado)
    sset = set(sir_fields.keys());  es = sir_fields
    f_s_nome = first_existing_field(sset, 'nome', 'name', 'titulo', 'descricao', 'label')
    f_s_lat  = first_existing_field(sset, 'lat', 'latitude', 'coord_lat')
    f_s_lon  = first_existing_field(sset, 'lon', 'lng', 'longitude', 'coord_lon')
    f_s_mun  = first_existing_field(sset, 'municipio', 'cidade', 'local', 'bairro')
    f_s_id_e = first_existing_field(sset, 'id_e')  # problemático (unique/not null)

    eset = set(ev_fields.keys());   ee = ev_fields
    f_e_nome = first_existing_field(eset, 'nome', 'name', 'titulo', 'evento', 'descricao')
    f_e_lat  = first_existing_field(eset, 'lat', 'latitude', 'coord_lat')
    f_e_lon  = first_existing_field(eset, 'lon', 'lng', 'longitude', 'coord_lon')
    f_e_tipo = first_existing_field(eset, 'tipo', 'categoria', 'classe')
    f_e_prio = first_existing_field(eset, 'prioridade', 'prior', 'nivel', 'gravidade')
    f_e_data = first_existing_field(eset, 'data', 'quando', 'inicio', 'data_inicio', 'datetime')

    oset = set(oc_fields.keys());    eo = oc_fields
    f_o_desc = first_existing_field(oset, 'descricao', 'descricao_curta', 'titulo', 'name')
    f_o_lat  = first_existing_field(oset, 'lat', 'latitude', 'coord_lat')
    f_o_lon  = first_existing_field(oset, 'lon', 'lng', 'longitude', 'coord_lon')
    f_o_tipo = first_existing_field(oset, 'tipo', 'categoria', 'classe')
    f_o_prio = first_existing_field(oset, 'prioridade', 'prior', 'nivel', 'gravidade')
    f_o_stat = first_existing_field(oset, 'status', 'situacao', 'estado')
    f_o_data = first_existing_field(oset, 'data', 'quando', 'inicio', 'data_inicio', 'datetime')

    print('\n--- Mapeamento detectado ---')
    print('Sirene   :', dict(nome=f_s_nome, lat=f_s_lat, lon=f_s_lon, municipio=f_s_mun, id_e=f_s_id_e))
    print('Evento   :', dict(nome=f_e_nome, lat=f_e_lat, lon=f_e_lon, tipo=f_e_tipo, prioridade=f_e_prio, data=f_e_data))
    print('Ocorrênc.:', dict(desc=f_o_desc, lat=f_o_lat, lon=f_o_lon, tipo=f_o_tipo, prioridade=f_o_prio, status=f_o_stat, data=f_o_data))

    # Limpar dados
    Sirene.objects.all().delete()
    DadosSirene.objects.all().delete()
    Evento.objects.all().delete()
    Ocorrencias.objects.all().delete()

    # Sirenes (gera id_e único se necessário)
    with transaction.atomic():
        seq = 1
        for s in sirenes_data:
            payload = {}
            if f_s_nome: payload[f_s_nome] = s['nome']
            if f_s_lat:  payload[f_s_lat]  = s['lat']
            if f_s_lon:  payload[f_s_lon]  = s['lon']
            if f_s_mun:  payload[f_s_mun]  = s.get('municipio')

            if f_s_id_e:
                fld = es[f_s_id_e]
                if (fld.get('unique') or not fld.get('null')):
                    payload[f_s_id_e] = f'TEST-SIR-{seq:04d}'
                    seq += 1

            obj = Sirene.objects.create(**payload)
            try:
                DadosSirene.objects.create(
                    estacao_id=getattr(obj, 'id', None),
                    status='ativa',
                    tipo=s.get('prior', 'media')
                )
            except Exception:
                pass

    # Eventos
    with transaction.atomic():
        for e in eventos_data:
            payload = {}
            if f_e_nome: payload[f_e_nome] = e['nome']
            if f_e_tipo: payload[f_e_tipo] = e['tipo']
            if f_e_lat:  payload[f_e_lat]  = e['lat']
            if f_e_lon:  payload[f_e_lon]  = e['lon']
            if f_e_prio: payload[f_e_prio] = e['prioridade']
            if f_e_data: payload[f_e_data] = e['quando']
            Evento.objects.create(**payload)

    # Ocorrencias
    with transaction.atomic():
        for o in ocorrencias_data:
            payload = {}
            if f_o_desc: payload[f_o_desc] = o['descricao']
            if f_o_tipo: payload[f_o_tipo] = o['tipo']
            if f_o_lat:  payload[f_o_lat]  = o['lat']
            if f_o_lon:  payload[f_o_lon]  = o['lon']
            if f_o_prio: payload[f_o_prio] = o['prior']
            if f_o_stat: payload[f_o_stat] = 'aberta'
            if f_o_data: payload[f_o_data] = datetime.now()
            Ocorrencias.objects.create(**payload)

    print('\n✅ População concluída!')

if __name__ == '__main__':
    print_model_info()
    populate()
