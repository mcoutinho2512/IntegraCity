from django.db import models
from location_field.models.plain import PlainLocationField
from math import sin, cos, sqrt, atan2, radians
from django.contrib.auth.models import User
import subprocess
from pyfcm import FCMNotification
from datetime import datetime
from datetime import timedelta
from dateutil import tz
import pytz
from django.db import transaction
from djgeojson.fields import GeometryField
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from requests.auth import HTTPBasicAuth
import os, json
from geopy.geocoders import GoogleV3
from django.conf import settings
from django.template.defaultfilters import slugify
#from googletrans import Translator
from deep_translator import GoogleTranslator

class OrgaoBrasil(models.Model):
	nome = models.CharField("Nome", max_length=250,unique=True)

	class Meta:
		verbose_name = "Orgão - Operação Brasil"
		verbose_name_plural = "Orgão - Operação Brasil"

	def __str__(self):
		return self.nome

class LocalBrail(models.Model):
	local = models.ForeignKey(OrgaoBrasil,on_delete=models.CASCADE,verbose_name="Órgão")
	nome = models.CharField("Nome", max_length=250)
	endereco = models.CharField("Endereço", max_length=250, blank=True,null=True,help_text="O endereço deve ser escrito da seguinte maneira: Logradouro,Número,Bairro,Cidade. Exemplo: Avenida Presidente Vargas, 500, Centro, Rio de Janeiro")
	resp = models.CharField("Responsável", max_length=250, blank=True,null=True)
	tel = models.CharField("Telefone", max_length=250, blank=True,null=True)
	email = models.CharField("E-mail", max_length=250, blank=True,null=True)
	location = PlainLocationField(based_fields=['endereco'], zoom=12, blank=True,null=True)

	class Meta:
		verbose_name = "Local do Orgão - Operação Brasil"
		verbose_name_plural = "Local do Orgão - Operação Brasil"

	def __str__(self):
		return ""+str(self.local.nome)+" - "+str(self.nome)


class RecursoBrasil(models.Model):
	local = models.ForeignKey(LocalBrail,on_delete=models.CASCADE,verbose_name="Local do órgão")
	nome = models.CharField("Nome", max_length=250)
	codigo = models.CharField("Placa/Código", max_length=250)
	resp = models.CharField("Responsável", max_length=250, blank=True,null=True)
	tel = models.CharField("Telefone", max_length=250, blank=True,null=True)
	email = models.CharField("E-mail", max_length=250, blank=True,null=True)

	class Meta:
		verbose_name = "Recurso - Operação Brasil"
		verbose_name_plural = "Recurso - Operação Brasil"

	def __str__(self):
		return ""+str(self.local.nome)+" - "+str(self.nome)

class RecursoSituacao(models.Model):
	recurso = models.ForeignKey(RecursoBrasil,on_delete=models.CASCADE,verbose_name="Recurso")
	STATUS_CHOICE = (
		('Ok', 'Ok'),
		('Não Ok', 'Não Ok'),
	)
	status = models.CharField("Situação",max_length=20,choices=STATUS_CHOICE,blank=True,null=True)
	data_i = models.DateTimeField("Data e hora do contato",blank=True,null=True)

	class Meta:
		verbose_name = "Situação dos Recursos - Operação Brasil"
		verbose_name_plural = "Situação dos Recursos - Operação Brasil"

	def __str__(self):
		local_nome = self.recurso.local.nome if self.recurso and self.recurso.local else "Sem local"
		status = self.status or "Sem status"
		return f"{self.recurso.nome} - {local_nome} - {status}"




class Navios(models.Model):
	data_i = models.DateTimeField("Data de atracação", max_length=250, blank=True,null=True)
	data_f = models.DateTimeField("Data de Desatracação", max_length=250, blank=True,null=True)
	origem = models.CharField("Origem", max_length=250)
	destino = models.CharField("Destino", max_length=250)
	nome = models.CharField("Nome", max_length=250)
	capacidade = models.CharField("Capacidade", max_length=250)

	class Meta:
		verbose_name = "Navios"
		verbose_name_plural = "Navios"

	def __str__(self):
		return self.nome

class Pouso(models.Model):
	origem = models.CharField("lat", max_length=250)
	destino = models.CharField("lat", max_length=250)
	tipo = models.CharField("lat", max_length=250)
	idv = models.CharField("lat", max_length=250,unique=True)
	companhia = models.CharField("lat", max_length=250)
	status = models.CharField("lat", max_length=250)
	data = models.DateTimeField("lon", max_length=250, blank=True,null=True)
	data_r = models.DateTimeField("lon", max_length=250, blank=True,null=True)

	class Meta:
		verbose_name = "Pouso"
		verbose_name_plural = "Pouso"

	def __str__(self):
		return self.idv

class Onibus(models.Model):
	id_e = models.CharField("ID Estação", max_length=250,unique=True)
	placa = models.CharField("lat", max_length=250)

	class Meta:
		verbose_name = "Onibus"
		verbose_name_plural = "Onibus"

	def __str__(self):
		return self.id_e

class DadosOnibus(models.Model):
	estacao = models.ForeignKey(Onibus,on_delete=models.CASCADE)
	lat = models.CharField("lat", max_length=250)
	lon = models.CharField("lon", max_length=250)
	linha = models.CharField("lon", max_length=250, blank=True,null=True)
	data = models.DateTimeField("lon", max_length=250, blank=True,null=True)
	velocidade = models.CharField("lon", max_length=250, blank=True,null=True)
	sentido = models.CharField("lon", max_length=250, blank=True,null=True)
	trajeto = models.CharField("lon", max_length=250, blank=True,null=True)
	direcao = models.CharField("lon", max_length=250, blank=True,null=True)
	unico = models.CharField("lon", max_length=250,unique=True)

	class Meta:
		verbose_name = "DadosOnibus"
		verbose_name_plural = "DadosOnibus"


class Scroll(models.Model):
	texto = models.TextField("Texto")

	class Meta:
		verbose_name = "Scroll"
		verbose_name_plural = "Scroll"

	def __str__(self):
		return self.texto

class Link(models.Model):
	link = models.CharField("Link", max_length=250,unique=True)
	nome = models.CharField("Nome", max_length=250)
	foto = models.FileField(upload_to='uploads/',verbose_name="Icone", blank=True,null=True)
	
	class Meta:
		verbose_name = "Link"
		verbose_name_plural = "Link"

	def __str__(self):
		return self.link

class TTCORN(models.Model):
	id_t = models.CharField("ID User", max_length=250,unique=True)
	twitte = models.TextField("ID User")
	tipo = models.CharField("Data",max_length=250)
	data = models.DateTimeField("ID User")
	lingua = models.CharField("Data",max_length=250)

	class Meta:
		verbose_name = "TTCOR"
		verbose_name_plural = "TTCOR"

	def __str__(self):
		return self.id_t


class FogoCalc(models.Model):
	local = models.CharField("Data",max_length=250)
	data = models.CharField("Data",max_length=250)
	datal = models.CharField("Data",max_length=250,unique=True)
	neste = models.CharField("Data",max_length=40)

class Radar(models.Model):
	id_e = models.CharField("ID Estação", max_length=250,unique=True)
	local = models.CharField("lat", max_length=250)
	lats = models.CharField("lat", max_length=250)
	lons = models.CharField("lon", max_length=250)
	elevacoes = models.TextField("Temperatura")

	class Meta:
		verbose_name = "Estacao Met"
		verbose_name_plural = "Estacao Met"

	def __str__(self):
		return self.id_e

class DadosRadar(models.Model):
	estacao = models.ForeignKey(Radar,on_delete=models.CASCADE)
	lat = models.CharField("lat", max_length=250)
	lon = models.CharField("lon", max_length=250)
	unico = models.CharField("lon", max_length=250,unique=True)
	zdr = models.TextField("Temperatura")
	dbz = models.TextField("Temperatura")

	class Meta:
		verbose_name = "DadosRadar"
		verbose_name_plural = "DadosRadar"

class SPPO(models.Model):
	id_e = models.CharField("ID Estação", max_length=250,unique=True)
	
	class Meta:
		verbose_name = "SPPO"
		verbose_name_plural = "SPPO"

	def __str__(self):
		return self.id_e

class DadosSPPO(models.Model):
	estacao = models.ForeignKey(SPPO,on_delete=models.CASCADE)
	rota = models.CharField("Rota", max_length=250)
	mean = models.CharField("lon", max_length=250)
	status = models.CharField("Temperatura", max_length=250)
	actual = models.CharField("Temperatura", max_length=250)

	class Meta:
		verbose_name = "DadosRadar"
		verbose_name_plural = "DadosRadar"


class EstacaoBoi(models.Model):
	lat = models.CharField("Lat", max_length=250, blank=True,null=True)
	lon = models.CharField("Lon", max_length=250, blank=True,null=True)
	nome = models.CharField("Estação", max_length=250, blank=True,null=True)
	municipio = models.CharField("Municipio", max_length=250, blank=True,null=True)
	fonte = models.CharField("Fonte", max_length=250, blank=True,null=True)
	id_e = models.CharField("ID Estação", max_length=250,unique=True)

	class Meta:
		verbose_name = "Estacao Boi"
		verbose_name_plural = "Estacao Boi"

	def __str__(self):
		return self.id_e

class DadosBoi(models.Model):
	estacao = models.ForeignKey(EstacaoBoi,on_delete=models.CASCADE)
	data = models.CharField("data", max_length=250)
	data_u = models.CharField("data única", max_length=250, unique=True)
	tp = models.CharField("Temperatura", max_length=250)
	avg_spre = models.CharField("Temperatura", max_length=250)
	avg_spre_n = models.CharField("Temperatura", max_length=250)
	m_decl = models.CharField("Temperatura", max_length=250)
	tp5 = models.CharField("Temperatura", max_length=250)
	t10 = models.CharField("Temperatura", max_length=250)
	tz = models.CharField("Temperatura", max_length=250)
	tsig = models.CharField("Temperatura", max_length=250)
	hsig = models.CharField("Temperatura", max_length=250)
	hmax = models.CharField("Temperatura", max_length=250)
	avg_w_tmp1 = models.CharField("Temperatura", max_length=250)
	avg_w_tmp2 = models.CharField("Temperatura", max_length=250)
	avg_sal = models.CharField("Temperatura", max_length=250)
	avg_wv_dir = models.CharField("Temperatura", max_length=250)
	avg_wv_dir_n = models.CharField("Temperatura", max_length=250)
	avg_cel1_mag = models.CharField("Temperatura", max_length=250)
	avg_cel1_dir = models.CharField("Temperatura", max_length=250)
	avg_cel1_dir_n = models.CharField("Temperatura", max_length=250)
	m_decl = models.CharField("Temperatura", max_length=250)
	zcn = models.CharField("Temperatura", max_length=250)
	hmo = models.CharField("Temperatura", max_length=250)
	tavg = models.CharField("Temperatura", max_length=250)
	h10 = models.CharField("Temperatura", max_length=250)

	class Meta:
		verbose_name = "Dados Boi"
		verbose_name_plural = "Dados Boi"

	def __str__(self):
		return self.data


class EstacaoPra(models.Model):
	lat = models.CharField("Lat", max_length=250)
	lon = models.CharField("Lon", max_length=250)
	nome = models.CharField("Estação", max_length=250)
	municipio = models.CharField("Municipio", max_length=250)
	fonte = models.CharField("Fonte", max_length=250)
	id_e = models.CharField("ID Estação", max_length=250,unique=True)

	class Meta:
		verbose_name = "Estacao Met"
		verbose_name_plural = "Estacao Met"

	def __str__(self):
		return self.usuario

class DadosPra(models.Model):
	estacao = models.ForeignKey(EstacaoPra,on_delete=models.CASCADE)
	data = models.CharField("data", max_length=250)
	data_u = models.CharField("data única", max_length=250, unique=True)
	situ = models.CharField("Temperatura", max_length=250)

	class Meta:
		verbose_name = "Dados Met"
		verbose_name_plural = "Dados Met"

	def __str__(self):
		return self.usuario

class CamerasPraia(models.Model):
	nome = models.CharField("Nome",max_length=255)
	lat = models.CharField("Nome",max_length=255)
	lon = models.CharField("Nome",max_length=255)
	id_c = models.CharField("Nome",max_length=255,unique=True)
	status = models.CharField("Nome",max_length=255)

	class Meta:
		verbose_name = "Cameras"
		verbose_name_plural = "Cameras"


	def __str__(self):
		return self.nome

class Cameras(models.Model):
	nome = models.CharField("Nome",max_length=255)
	lat = models.CharField("Lat",max_length=255)
	lon = models.CharField("Lon",max_length=255)
	id_c = models.CharField("Id",max_length=255,unique=True)
	angulo = models.CharField("Ângulo",max_length=255, blank=True,null=True)
	status = models.CharField("Status",max_length=255, blank=True,null=True)
	ip = models.CharField("Modelo",max_length=255, blank=True,null=True)
	fabricante = models.CharField("Modelo",max_length=255, blank=True,null=True)
	modelo = models.CharField("Modelo",max_length=255, blank=True,null=True)
	zona = models.CharField("Marca",max_length=255, blank=True,null=True)
	bairro = models.CharField("Marca",max_length=255, blank=True,null=True)
	criar = models.DateField(auto_now=False, blank=True,null=True)
	hd = models.CharField("HD",max_length=255, blank=True,null=True)

	class Meta:
		verbose_name = "Cameras"
		verbose_name_plural = "Cameras"


	def __str__(self):
		return self.id_c+" - "+self.nome

	def save(self, *args, **kwargs):
		lat = str(int(self.lat.replace(".","")))
		lat_novo = lat[0:3]+"."+lat[3:]
		lon = str(int(self.lon.replace(".","")))
		lon_novo = lon[0:3]+"."+lon[3:]
		self.lat = lat_novo
		self.lon = lon_novo
		super(Cameras, self).save(*args, **kwargs)

class DadosCamera(models.Model):
	estacao = models.ForeignKey(Cameras,on_delete=models.CASCADE)
	data = models.DateTimeField(auto_now=False, blank=True,null=True)
	situ = models.CharField("Temperatura", max_length=250)

	class Meta:
		verbose_name = "Dados Câmera"
		verbose_name_plural = "Dados Câmera"

	def __str__(self):
		return self.situ

class CamerasMG(models.Model):
	estacao = models.ForeignKey(Cameras,on_delete=models.CASCADE)
	TIPOS = (
		('1', '1'),
		('2', '2'),
		('3', '3'),
		('4', '4'),
	)
	tipo = models.CharField("Ordem",max_length=60,choices=TIPOS,blank=True,null=True)

	class Meta:
		verbose_name = "Cameras Interesse Telao"
		verbose_name_plural = "Cameras Interesse Telao"


	def __str__(self):
		return self.estacao.nome

class CamerasVA(models.Model):
	estacao = models.ForeignKey(Cameras,on_delete=models.CASCADE)
	TIPOS = (
		('BRT Contagem Pessoas', 'BRT Contagem Pessoas'),
		('Aglomeração', 'Aglomeração'),
	)
	tipo = models.CharField("Tipo",max_length=60,choices=TIPOS,blank=True,null=True)

	class Meta:
		verbose_name = "Cameras Video Analitico"
		verbose_name_plural = "Cameras Video Analitico"


	def __str__(self):
		return self.estacao.nome

class DadosCameraVA(models.Model):
	estacaonovo = models.ForeignKey(CamerasVA,on_delete=models.CASCADE)
	data = models.DateTimeField(auto_now=False, blank=True,null=True)
	qt = models.CharField("Temperatura", max_length=250)
	dado = models.CharField("Temperatura", max_length=250)
	dia = models.CharField("Nivel", max_length=250)
	hora = models.IntegerField("Nivel")
	minuto = models.IntegerField("Nivel")
	hm = models.CharField("Nivel", max_length=250)

	class Meta:
		verbose_name = "Dados Câmera VA"
		verbose_name_plural = "Dados Câmera VA"

	def __str__(self):
		return self.situ

class Procolos(models.Model):
	nome = models.CharField("Nome",max_length=255)
	foto = models.FileField(upload_to='uploads/',verbose_name="Documento", blank=True,null=True)
	resp = models.CharField("Responsável",max_length=200, blank=True,null=True)
	tipo = models.CharField("Tipo",max_length=200, blank=True,null=True)
	class Meta:
		verbose_name = "Documentos e Protocolos"
		verbose_name_plural = "Documentos e Protocolos"


	def __str__(self):
		return self.nome


class Pops(models.Model):
	rua = models.CharField("Pops",max_length=200,unique=True)

	class Meta:
		verbose_name = "POP"
		verbose_name_plural = "POP"

	def __str__(self):
		return self.rua


	def save(self, *args, **kwargs):
		super(Pops, self).save(*args, **kwargs)


class OcorrenciaInterno(models.Model):
	pop = models.ForeignKey(Pops,on_delete=models.CASCADE,verbose_name="Ocorrência")
	rua = models.CharField("Logradouro",max_length=200,blank=True,null=True,help_text="Caso a ocorrência não seja no local que você se encontra, preencha o endereço.")
	numero = models.CharField("Número",max_length=200,blank=True,null=True,help_text="Caso a ocorrência não seja no local que você se encontra, preencha o número.")
	BAIRRO_CHOICE = (
		('Abolição','Abolição'),
		('Acari','Acari'),
		('Água Santa','Água Santa'),
		('Alto da Boa Vista','Alto da Boa Vista'),
		('Anchieta','Anchieta'),
		('Andaraí','Andaraí'),
		('Anil','Anil'),
		('Bancários','Bancários'),
		('Bangu','Bangu'),
		('Barra da Tijuca','Barra da Tijuca'),
		('Barra de Guaratiba','Barra de Guaratiba'),
		('Barros Filho','Barros Filho'),
		('Benfica','Benfica'),
		('Bento Ribeiro','Bento Ribeiro'),
		('Bonsucesso','Bonsucesso'),
		('Botafogo','Botafogo'),
		('Brás de Pina','Brás de Pina'),
		('Cachambi','Cachambi'),
		('Cacuia','Cacuia'),
		('Caju','Caju'),
		('Camorim','Camorim'),
		('Campinho','Campinho'),
		('Campo dos Afonsos','Campo dos Afonsos'),
		('Campo Grande','Campo Grande'),
		('Cascadura','Cascadura'),
		('Catete','Catete'),
		('Catumbi','Catumbi'),
		('Cavalcanti','Cavalcanti'),
		('Centro','Centro'),
		('Cidade de Deus','Cidade de Deus'),
		('Cidade Nova','Cidade Nova'),
		('Cidade Universitária','Cidade Universitária'),
		('Cocotá','Cocotá'),
		('Coelho Neto','Coelho Neto'),
		('Colégio','Colégio'),
		('Complexo do Alemão','Complexo do Alemão'),
		('Copacabana','Copacabana'),
		('Cordovil','Cordovil'),
		('Cosme Velho','Cosme Velho'),
		('Cosmos','Cosmos'),
		('Costa Barros','Costa Barros'),
		('Curicica','Curicica'),
		('Del Castilho','Del Castilho'),
		('Deodoro','Deodoro'),
		('Encantado','Encantado'),
		('Engenheiro Leal','Engenheiro Leal'),
		('Engenho da Rainha','Engenho da Rainha'),
		('Engenho de Dentro','Engenho de Dentro'),
		('Engenho Novo','Engenho Novo'),
		('Estácio','Estácio'),
		('Flamengo','Flamengo'),
		('Freguesia (Ilha do Governador)','Freguesia (Ilha do Governador)'),
		('Freguesia (Jacarepaguá)','Freguesia (Jacarepaguá)'),
		('Galeão','Galeão'),
		('Gamboa','Gamboa'),
		('Gardênia Azul','Gardênia Azul'),
		('Gávea','Gávea'),
		('Gericinó','Gericinó'),
		('Glória','Glória'),
		('Grajaú','Grajaú'),
		('Grumari','Grumari'),
		('Guadalupe','Guadalupe'),
		('Guaratiba','Guaratiba'),
		('Higienópolis','Higienópolis'),
		('Honório Gurgel','Honório Gurgel'),
		('Humaitá','Humaitá'),
		('Inhaúma','Inhaúma'),
		('Inhoaíba','Inhoaíba'),
		('Ipanema','Ipanema'),
		('Irajá','Irajá'),
		('Itanhangá','Itanhangá'),
		('Jacaré','Jacaré'),
		('Jacarepaguá','Jacarepaguá'),
		('Jacarezinho','Jacarezinho'),
		('Jardim América','Jardim América'),
		('Jardim Botânico','Jardim Botânico'),
		('Jardim Carioca','Jardim Carioca'),
		('Jardim Guanabara','Jardim Guanabara'),
		('Jardim Sulacap','Jardim Sulacap'),
		('Joá','Joá'),
		('Lagoa','Lagoa'),
		('Lapa','Lapa'),
		('Laranjeiras','Laranjeiras'),
		('Leblon','Leblon'),
		('Leme','Leme'),
		('Lins de Vasconcelos','Lins de Vasconcelos'),
		('Madureira','Madureira'),
		('Magalhães Bastos','Magalhães Bastos'),
		('Mangueira','Mangueira'),
		('Manguinhos','Manguinhos'),
		('Maracanã','Maracanã'),
		('Maré','Maré'),
		('Marechal Hermes','Marechal Hermes'),
		('Maria da Graça','Maria da Graça'),
		('Méier','Méier'),
		('Moneró','Moneró'),
		('Olaria','Olaria'),
		('Oswaldo Cruz','Oswaldo Cruz'),
		('Paciência','Paciência'),
		('Padre Miguel','Padre Miguel'),
		('Paquetá','Paquetá'),
		('Parada de Lucas','Parada de Lucas'),
		('Parque Anchieta','Parque Anchieta'),
		('Parque Columbia','Parque Columbia'),
		('Pavuna','Pavuna'),
		('Pechincha','Pechincha'),
		('Pedra de Guaratiba','Pedra de Guaratiba'),
		('Penha','Penha'),
		('Penha Circular','Penha Circular'),
		('Piedade','Piedade'),
		('Pilares','Pilares'),
		('Pitangueiras','Pitangueiras'),
		('Portuguesa','Portuguesa'),
		('Praça da Bandeira','Praça da Bandeira'),
		('Praça Seca','Praça Seca'),
		('Praia da Bandeira','Praia da Bandeira'),
		('Quintino Bocaiúva','Quintino Bocaiúva'),
		('Ramos','Ramos'),
		('Realengo','Realengo'),
		('Recreio dos Bandeirantes','Recreio dos Bandeirantes'),
		('Riachuelo','Riachuelo'),
		('Ribeira','Ribeira'),
		('Ricardo de Albuquerque','Ricardo de Albuquerque'),
		('Rio Comprido','Rio Comprido'),
		('Rocha','Rocha'),
		('Rocha Miranda','Rocha Miranda'),
		('Rocinha','Rocinha'),
		('Sampaio','Sampaio'),
		('Santa Cruz','Santa Cruz'),
		('Santa Teresa','Santa Teresa'),
		('Santíssimo','Santíssimo'),
		('Santo Cristo','Santo Cristo'),
		('São Conrado','São Conrado'),
		('São Cristóvão','São Cristóvão'),
		('São Francisco Xavier','São Francisco Xavier'),
		('Saúde','Saúde'),
		('Senador Camará','Senador Camará'),
		('Senador Vasconcelos','Senador Vasconcelos'),
		('Sepetiba','Sepetiba'),
		('Tanque','Tanque'),
		('Taquara','Taquara'),
		('Tauá','Tauá'),
		('Tijuca','Tijuca'),
		('Todos os Santos','Todos os Santos'),
		('Tomás Coelho','Tomás Coelho'),
		('Turiaçu','Turiaçu'),
		('Urca','Urca'),
		('Vargem Grande','Vargem Grande'),
		('Vargem Pequena','Vargem Pequena'),
		('Vasco da Gama','Vasco da Gama'),
		('Vaz Lobo','Vaz Lobo'),
		('Vicente de Carvalho','Vicente de Carvalho'),
		('Vidigal','Vidigal'),
		('Vigário Geral','Vigário Geral'),
		('Vila Cosmos','Vila Cosmos'),
		('Vila da Penha','Vila da Penha'),
		('Vila Isabel','Vila Isabel'),
		('Vila Militar','Vila Militar'),
		('Vila Valqueire','Vila Valqueire'),
		('Vista Alegre','Vista Alegre'),
		('Zumbi','Zumbi'),	
	)
	bairro = models.CharField("Bairro",max_length=30,choices=BAIRRO_CHOICE,blank=True,null=True,help_text="Caso a ocorrência não seja no local que você se encontra, preencha o bairro.")
	cidade = models.CharField("Cidade",max_length=200,blank=True,null=True)
	lat = models.CharField("Latitude",max_length=100,blank=True,null=True)
	lon = models.CharField("Longitude",max_length=100,blank=True,null=True)
	foto = models.FileField(upload_to='uploads/',verbose_name="Foto", blank=True,null=True)
	foto2 = models.ImageField(upload_to='uploads/',verbose_name="Foto", blank=True,null=True)
	link = models.TextField("Link de localização",blank=True,null=True)
	obs = models.TextField("Observações",blank=True,null=True)
	create = models.DateTimeField(auto_now=True)
	pessoa = models.ForeignKey(User,on_delete=models.CASCADE,verbose_name="Usuário")
	desabrigado = models.CharField("Desabrigados",max_length=100,blank=True,null=True)
	desparecido = models.CharField("Desaparecidos",max_length=100,blank=True,null=True)
	PRIORIDADE_CHOICE = (
		('BAIXA', 'BAIXA'),
		('MÉDIA', 'MÉDIA'),
		('ALTA', 'ALTA'),
		('CRÍTICA', 'CRÍTICA'),
	)
	prio = models.CharField("Criticidade",max_length=20,choices=PRIORIDADE_CHOICE,blank=True,null=True)
	FONTE_CHOICE = (
		('Própria', 'Própria'),
		('Terceiros', 'Terceiros'),
	)
	fonte = models.CharField("Fonte",max_length=20,choices=FONTE_CHOICE,blank=True,null=True)
	GRAVIDADE = (
		('Sem Status','Sem Status'),
		('Confirmado','Confirmado'),
		('Em apuração','Em apuração'),
		('Descartado','Descartado'),
		('Encerado','Encerado'),
	)
	status = models.CharField("Situação",max_length=40, choices=GRAVIDADE,blank=True,null=True)

	class Meta:
		verbose_name = "Ocorrências Internas"
		verbose_name_plural = "Ocorrências Internas"


	def save(self, *args, **kwargs):
		geolocator = GoogleV3(api_key="AIzaSyBke5pvPpmPU9EGo1iJj4cCm0dgpeTM-bc")
		if self.rua != None:
			try:
				location = geolocator.geocode(self.rua+", "+self.numero+", "+self.bairro+", Rio de Janeiro, RJ")
			except:
				try:
					location = geolocator.geocode(self.rua+", "+self.bairro+", Rio de Janeiro, RJ")
				except:
					location = geolocator.geocode(self.rua+", Rio de Janeiro, RJ")
					
			self.lat = location.latitude
			self.lon = location.longitude
			self.cidade = "Rio de Janeiro"
		else:
			latlon = self.lat+" , "+self.lon
			locations = geolocator.reverse(latlon)
			numero = ""
			rua = ""
			bairro = ""
			cidade = ""

			x = 0
			while x != len(locations.raw['address_components']):
				lista = ""
				z = 0
				while z != len(locations.raw['address_components'][x]['types']):
					lista += locations.raw['address_components'][x]['types'][z]
					z += 1
				if (lista).find("street_number") != -1:
					numero = (locations.raw['address_components'][x]['long_name'])
				elif (lista).find("route") != -1:
					rua = (locations.raw['address_components'][x]['long_name'])
				elif (lista).find("sublocality_level_1") != -1:
					bairro = (locations.raw['address_components'][x]['long_name'])
				elif (lista).find("administrative_area_level_2") != -1:
					cidade = (locations.raw['address_components'][x]['long_name'])
				x += 1

			self.rua = rua
			self.numero = numero
			self.bairro = bairro
			self.cidade = cidade
		super(OcorrenciaInterno, self).save(*args, **kwargs)

	def __str__(self):
		try:
			a = self.pop + " - " +str(self.id)
		except:
			a = str(self.id)
		return a

class ArquivoEvento(models.Model):
	arquivo = models.FileField(upload_to='uploads/', blank=True,null=True,verbose_name="Arquivo")

	class Meta:
		verbose_name = "Arquivo Evento"
		verbose_name_plural = "Arquivo Eventos"

	def __str__(self):
		return "Arquivo adicionado com sucesso"


	def save(self, *args, **kwargs):
		super(ArquivoEvento, self).save(*args, **kwargs)

		with open("/root/app_cor/media/"+self.arquivo.name) as myfile:
			data_file = myfile.read().replace("\r\n","").split("\n")
		
		x = 5
		while x != len(data_file)-2:
			try:
				nome = data_file[x].split(";")[6]
				
				data_i_c = data_file[x].split(";")[2]+" "+data_file[x].split(";")[4]

				if len(data_i_c) > 11:
					data_i = datetime.strptime(data_i_c, '%d/%m/%Y %H:%M')
				else:
					data_i = datetime.strptime(data_i_c, '%d/%m/%Y ')

				data_f_c = data_file[x].split(";")[3]+" "+data_file[x].split(";")[5]
				if len(data_f_c) > 11:
					data_f = datetime.strptime(data_f_c, '%d/%m/%Y %H:%M')
				else:
					data_f = datetime.strptime(data_f_c, '%d/%m/%Y ')


				local = data_file[x].split(";")[10]
				zona = data_file[x].split(";")[11]
				endereco = data_file[x].split(";")[12]
				qt = data_file[x].split(";")[13]
				tipo = data_file[x].split(";")[16]
				id_e = data_file[x].split(";")[7]
				criti = data_file[x].split(";")[18]
				try:
					with transaction.atomic():
						p = Evento.objects.create(data_inicio=data_i,
							data_fim=data_f,
							nome_evento=nome,
							local=local,
							zona=zona,
							endereco=endereco,
							qt=qt,
							tipo=tipo,
							id_e=id_e,
							criti=criti)
						p.save()
				except:
					pass

			except IndexError:
				pass
			except ValueError:
				pass
			x += 1

def distancia(lat1_r,lon1_r,lat2_r,lon2_r):
	R = 6373.0
	lat1 = radians(lat1_r)
	lon1 = radians(lon1_r)
	lat2 = radians(lat2_r)
	lon2 = radians(lon2_r)
	dlon = lon2 - lon1
	dlat = lat2 - lat1
	a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
	c = 2 * atan2(sqrt(a), sqrt(1 - a))
	distance = R * c
	return distance 

class Local(models.Model):
	local = models.CharField("Nome do local", max_length=250)
	GER_CHOICE = (
		('Zona Norte', 'Zona Norte'),
		('Zona Oeste', 'Zona Oeste'),
		('Centro', 'Centro'),
		('Zona Sul', 'Zona Sul'),
	)
	zona = models.CharField("Zona da Cidade",max_length=20,choices=GER_CHOICE,blank=True,null=True)
	AP_CHOICE = (
		('AP 1', 'AP 1'),
		('AP 2', 'AP 2'),
		('AP 3', 'AP 3'),
		('AP 4', 'AP 4'),
		('AP 5', 'AP 5'),
	)
	ap = models.CharField("AP",max_length=20,choices=AP_CHOICE,blank=True,null=True)
	SUBS_CHOICE = (
		('Barra da Tijuca', 'Barra da Tijuca'),
		('Centro e Centro Histórico', 'Centro e Centro Histórico'),
		('Grande Bangu', 'Grande Bangu'),
		('lhas do Governador/Fundão/Paquetá', 'Ilhas'),
		('Jacarepaguá', 'Jacarepaguá'),
		('Tijuca', 'Tijuca'),
		('Zona Norte', 'Zona Norte'),
		('Zona Oeste I', 'Zona Oeste I'),
		('Zona Oeste II', 'Zona Oeste II'),
		('Zona Oeste III', 'Zona Oeste III'),
		('Zona Sul', 'Zona Sul'),
	)
	subs = models.CharField("SubPrefeitura",max_length=100,choices=SUBS_CHOICE,blank=True,null=True)
	BAIRRO_CHOICE = (
		('Abolição','Abolição'),
		('Acari','Acari'),
		('Água Santa','Água Santa'),
		('Alto da Boa Vista','Alto da Boa Vista'),
		('Anchieta','Anchieta'),
		('Andaraí','Andaraí'),
		('Anil','Anil'),
		('Bancários','Bancários'),
		('Bangu','Bangu'),
		('Barra da Tijuca','Barra da Tijuca'),
		('Barra Olimpica','Barra Olimpica'),
		('Barra de Guaratiba','Barra de Guaratiba'),
		('Barros Filho','Barros Filho'),
		('Benfica','Benfica'),
		('Bento Ribeiro','Bento Ribeiro'),
		('Bonsucesso','Bonsucesso'),
		('Botafogo','Botafogo'),
		('Brás de Pina','Brás de Pina'),
		('Cachambi','Cachambi'),
		('Cacuia','Cacuia'),
		('Caju','Caju'),
		('Camorim','Camorim'),
		('Campinho','Campinho'),
		('Campo dos Afonsos','Campo dos Afonsos'),
		('Campo Grande','Campo Grande'),
		('Cascadura','Cascadura'),
		('Catete','Catete'),
		('Catumbi','Catumbi'),
		('Cavalcanti','Cavalcanti'),
		('Centro','Centro'),
		('Cidade de Deus','Cidade de Deus'),
		('Cidade Nova','Cidade Nova'),
		('Cidade Universitária','Cidade Universitária'),
		('Cocotá','Cocotá'),
		('Coelho Neto','Coelho Neto'),
		('Colégio','Colégio'),
		('Complexo do Alemão','Complexo do Alemão'),
		('Copacabana','Copacabana'),
		('Cordovil','Cordovil'),
		('Cosme Velho','Cosme Velho'),
		('Cosmos','Cosmos'),
		('Costa Barros','Costa Barros'),
		('Curicica','Curicica'),
		('Del Castilho','Del Castilho'),
		('Deodoro','Deodoro'),
		('Encantado','Encantado'),
		('Engenheiro Leal','Engenheiro Leal'),
		('Engenho da Rainha','Engenho da Rainha'),
		('Engenho de Dentro','Engenho de Dentro'),
		('Engenho Novo','Engenho Novo'),
		('Estácio','Estácio'),
		('Flamengo','Flamengo'),
		('Freguesia (Ilha do Governador)','Freguesia (Ilha do Governador)'),
		('Freguesia (Jacarepaguá)','Freguesia (Jacarepaguá)'),
		('Galeão','Galeão'),
		('Gamboa','Gamboa'),
		('Gardênia Azul','Gardênia Azul'),
		('Gávea','Gávea'),
		('Gericinó','Gericinó'),
		('Glória','Glória'),
		('Grajaú','Grajaú'),
		('Grumari','Grumari'),
		('Guadalupe','Guadalupe'),
		('Guaratiba','Guaratiba'),
		('Higienópolis','Higienópolis'),
		('Honório Gurgel','Honório Gurgel'),
		('Humaitá','Humaitá'),
		('Inhaúma','Inhaúma'),
		('Inhoaíba','Inhoaíba'),
		('Ipanema','Ipanema'),
		('Irajá','Irajá'),
		('Itanhangá','Itanhangá'),
		('Jacaré','Jacaré'),
		('Jacarepaguá','Jacarepaguá'),
		('Jacarezinho','Jacarezinho'),
		('Jardim América','Jardim América'),
		('Jardim Botânico','Jardim Botânico'),
		('Jardim Carioca','Jardim Carioca'),
		('Jardim Guanabara','Jardim Guanabara'),
		('Jardim Sulacap','Jardim Sulacap'),
		('Joá','Joá'),
		('Lagoa','Lagoa'),
		('Lapa','Lapa'),
		('Laranjeiras','Laranjeiras'),
		('Leblon','Leblon'),
		('Leme','Leme'),
		('Lins de Vasconcelos','Lins de Vasconcelos'),
		('Madureira','Madureira'),
		('Magalhães Bastos','Magalhães Bastos'),
		('Mangueira','Mangueira'),
		('Manguinhos','Manguinhos'),
		('Maracanã','Maracanã'),
		('Maré','Maré'),
		('Marechal Hermes','Marechal Hermes'),
		('Maria da Graça','Maria da Graça'),
		('Méier','Méier'),
		('Moneró','Moneró'),
		('Olaria','Olaria'),
		('Oswaldo Cruz','Oswaldo Cruz'),
		('Paciência','Paciência'),
		('Padre Miguel','Padre Miguel'),
		('Paquetá','Paquetá'),
		('Parada de Lucas','Parada de Lucas'),
		('Parque Anchieta','Parque Anchieta'),
		('Parque Columbia','Parque Columbia'),
		('Pavuna','Pavuna'),
		('Pechincha','Pechincha'),
		('Pedra de Guaratiba','Pedra de Guaratiba'),
		('Penha','Penha'),
		('Penha Circular','Penha Circular'),
		('Piedade','Piedade'),
		('Pilares','Pilares'),
		('Pitangueiras','Pitangueiras'),
		('Portuguesa','Portuguesa'),
		('Praça da Bandeira','Praça da Bandeira'),
		('Praça Seca','Praça Seca'),
		('Praia da Bandeira','Praia da Bandeira'),
		('Quintino Bocaiúva','Quintino Bocaiúva'),
		('Ramos','Ramos'),
		('Realengo','Realengo'),
		('Recreio dos Bandeirantes','Recreio dos Bandeirantes'),
		('Riachuelo','Riachuelo'),
		('Ribeira','Ribeira'),
		('Ricardo de Albuquerque','Ricardo de Albuquerque'),
		('Rio Comprido','Rio Comprido'),
		('Rocha','Rocha'),
		('Rocha Miranda','Rocha Miranda'),
		('Rocinha','Rocinha'),
		('Sampaio','Sampaio'),
		('Santa Cruz','Santa Cruz'),
		('Santa Teresa','Santa Teresa'),
		('Santíssimo','Santíssimo'),
		('Santo Cristo','Santo Cristo'),
		('São Conrado','São Conrado'),
		('São Cristóvão','São Cristóvão'),
		('São Francisco Xavier','São Francisco Xavier'),
		('Saúde','Saúde'),
		('Senador Camará','Senador Camará'),
		('Senador Vasconcelos','Senador Vasconcelos'),
		('Sepetiba','Sepetiba'),
		('Tanque','Tanque'),
		('Taquara','Taquara'),
		('Tauá','Tauá'),
		('Tijuca','Tijuca'),
		('Todos os Santos','Todos os Santos'),
		('Tomás Coelho','Tomás Coelho'),
		('Turiaçu','Turiaçu'),
		('Urca','Urca'),
		('Vargem Grande','Vargem Grande'),
		('Vargem Pequena','Vargem Pequena'),
		('Vasco da Gama','Vasco da Gama'),
		('Vaz Lobo','Vaz Lobo'),
		('Vicente de Carvalho','Vicente de Carvalho'),
		('Vidigal','Vidigal'),
		('Vigário Geral','Vigário Geral'),
		('Vila Cosmos','Vila Cosmos'),
		('Vila da Penha','Vila da Penha'),
		('Vila Isabel','Vila Isabel'),
		('Vila Militar','Vila Militar'),
		('Vila Valqueire','Vila Valqueire'),
		('Vista Alegre','Vista Alegre'),
		('Zumbi','Zumbi'),	
	)
	bairro = models.CharField("Bairro",max_length=30,choices=BAIRRO_CHOICE,blank=True,null=True)
	end = models.CharField("Endereço", max_length=250)
	location = PlainLocationField(verbose_name="Coordenadas", based_fields=['end'], zoom=7)
	resp = models.CharField("Responsável",max_length=250,blank=True,null=True)
	tel = models.CharField("Telefone",max_length=250,blank=True,null=True)
	class Meta:
		verbose_name = "Local"
		verbose_name_plural = "Locais"

	def __str__(self):
		return self.local

	def save(self, *args, **kwargs):
		import shapefile
		from shapely.geometry import LineString, Point, Polygon
		shape = shapefile.Reader("/home/cocr.servicos/app_cor/Aps/ApsN.shp")
		point = Point(float(self.location.split(",")[1]),float(self.location.split(",")[0]))
		cod = ""
		y = 0
		while y != len(shape.shapeRecords()):
			feature = shape.shapeRecords()[y]
			first = feature.shape.__geo_interface__  
			lista = first['coordinates'][0][0]
			poly2 = Polygon([i for i in lista])
			if (poly2.contains(point)) == True:
				cod = (feature.record['codap'])
				break
			y += 1
		self.ap = "AP "+cod
		super(Local, self).save(*args, **kwargs)

class RecursoEvent(models.Model):
	nome_evento = models.CharField("Nome do Recurso",max_length=255,blank=True,null=True)
	endere = models.ForeignKey(Local,on_delete=models.CASCADE,verbose_name="Local do Evento")
	end = models.CharField("Endereço", max_length=250)
	location = PlainLocationField(verbose_name="Coordenadas", based_fields=['end'], zoom=7)
	tipo = models.CharField("Tipo",max_length=40)
	CRITI_CH = (
		('Baixa','Baixa'),
		('Média','Média'),
		('Alta','Alta'),
		('NA','NA'),
	)
	local_criti = models.CharField("Criticidade",max_length=40, choices=CRITI_CH)

	class Meta:
		verbose_name = "Recurso Evento"
		verbose_name_plural = "Recurso Evento"

	def __str__(self):
		return self.nome_evento


class Evento(models.Model):
	nome_evento = models.CharField("Nome do Evento",max_length=255,blank=True,null=True)
	endere = models.ForeignKey(Local,on_delete=models.CASCADE,verbose_name="Local do Evento")
	estr = models.CharField("Estrutura do evento (Palco, Estrutura metálica, etc)",max_length=255,blank=True,null=True)
	cpe = models.CharField("CPE",max_length=255,blank=True,null=True)
	descri = models.TextField("Descrição",blank=True,null=True)
	qt = models.CharField("Estimativa de público",max_length=255,blank=True,null=True)
	TIPOEVENTO = (
		('Congresso','Congresso'),
		('Cultural','Cultural'),
		('Esportivo','Esportivo'),
		('Feira','Feira'),
		('Musical','Musical'),
		('Manifestação','Manifestação'),
		('Religioso','Religioso'),
		('Réveillon','Réveillon'),
		('Carnaval de bairro','Carnaval de bairro'),
		('Carnaval: Desfiles','Carnaval: Desfiles'),	
		('Carnaval: Ensaios Técnicos','Carnaval: Ensaios Técnicos'),
		('Carnaval: Blocos','Carnaval: Blocos'),
		('Carnaval: Palcos','Carnaval: Palcos'),
		('Blocos não oficiais','Blocos não oficiais'),
		('Simulado','Simulado'),
		('Acadêmicos','Acadêmicos'),
		('G20','G20'),('Outros','Outros'),
		('Corporativo','Corporativo'),
		('Político','Político'),
	)
	tipo = models.CharField("Tipo do evento", choices=TIPOEVENTO,max_length=255,blank=True,null=True)
	RESPEV = (
		('AEGE','AEGE'),
		('CEPEV','CEPEV'),
		('ferj','ferj'),
		('COR','COR'),
		("SMEL","SMEL"),
		("RIOTUR","RIOTUR"),
		("SUBPREFEITURA","SUBPREFEITURA"),
	)
	respeven = models.CharField("Responsável do evento", choices=RESPEV,max_length=255,blank=True,null=True)
	criti = models.CharField("Criticidade",max_length=255,blank=True,null=True)
	GRAVIDADE = (
		('Sim','Sim'),
		('Não','Não'),
	)
	alinha = models.CharField("Houve reunião de alinhamento",max_length=40, choices=GRAVIDADE,blank=True,null=True)
	CRITI_CH = (
		('Normal','Normal'),
		('Média','Média'),
		('Alta','Alta'),
		('NA','NA'),
	)
	local_criti = models.CharField("Criticidade - Local",max_length=40, choices=CRITI_CH)
	data_criti = models.CharField("Criticidade - Data",max_length=40, choices=CRITI_CH)
	hora_criti = models.CharField("Criticidade - Hora",max_length=40, choices=CRITI_CH)
	mobi_criti = models.CharField("Criticidade - Mobilidade",max_length=40, choices=CRITI_CH)
	pub_criti = models.CharField("Criticidade - Público Estimado",max_length=40, choices=CRITI_CH)
	exp_criti = models.CharField("Criticidade - Exposição Midíatica",max_length=40, choices=CRITI_CH)
	fp_criti = models.CharField("Criticidade - Figuras Pública",max_length=40, choices=CRITI_CH)
	efe_criti = models.CharField("Criticidade - Efetivo PCRJ Empregado",max_length=40, choices=CRITI_CH)
	pop_criti = models.CharField("Criticidade - População Impactada",max_length=40, choices=CRITI_CH)
	pt_criti = models.CharField("Criticidade - Potencial de Agravamento",max_length=40, choices=CRITI_CH)
	principal = models.CharField("Principal",max_length=40, choices=GRAVIDADE)
	arquivo = models.FileField(upload_to='capas',blank=True,null=True,verbose_name="Imagem")
	med = models.CharField("Média",max_length=255,blank=True,null=True)
	fonte = models.TextField("Fonte",blank=True,null=True)
	pontos_atencao = models.TextField("Pontos de Atenção",blank=True,null=True)
	ST_CH = (
		('Planejado','Planejado'),
		('Cancelado','Cancelado'),
	)
	status = models.CharField("Status",max_length=40, choices=ST_CH,blank=True,null=True)
	FR_CH = (
		('Parado','Parado'),
		('Com deslocamento','Com deslocamento'),
	)
	forma = models.CharField("Forma de apresentação",max_length=40, choices=FR_CH,blank=True,null=True)
	endereco = models.CharField("Endereço da dispersão",max_length=255,blank=True,null=True)

	tipo_forma = models.CharField(max_length=20, default='circle')
	raio = models.FloatField(null=True, blank=True, default=5000)
	tem_poligono = models.BooleanField(default=False)
	poligono_coords = models.TextField(null=True, blank=True)

	class Meta:
		verbose_name = "Eventos"
		verbose_name_plural = "Eventos"

	def __str__(self):
		return self.nome_evento

	def save(self, *args, **kwargs):
		if len(str(self.criti)) > 0:
			local_criti_qt = int(self.local_criti.replace("NA","1").replace("Normal","1").replace("Média","2").replace("Alta","3"))*2
			data_criti_qt = int(self.data_criti.replace("NA","1").replace("Normal","1").replace("Média","2").replace("Alta","3"))*1
			hora_criti_qt = int(self.hora_criti.replace("NA","1").replace("Normal","1").replace("Média","2").replace("Alta","3"))*1
			mobi_criti_qt = int(self.mobi_criti.replace("NA","1").replace("Normal","1").replace("Média","2").replace("Alta","3"))*1
			pub_criti_qt = int(self.pub_criti.replace("NA","1").replace("Normal","1").replace("Média","2").replace("Alta","3"))*1
			exp_criti_qt = int(self.exp_criti.replace("NA","1").replace("Normal","1").replace("Média","2").replace("Alta","3"))*2
			fp_criti_qt = int(self.fp_criti.replace("NA","1").replace("Normal","1").replace("Média","2").replace("Alta","3"))*1
			efe_criti_qt = int(self.efe_criti.replace("NA","1").replace("Normal","1").replace("Média","2").replace("Alta","3"))*1
			pop_criti_qt = int(self.pop_criti.replace("NA","1").replace("Normal","1").replace("Média","2").replace("Alta","3"))*2
			pt_criti_qt = int(self.pt_criti.replace("NA","1").replace("Normal","1").replace("Média","2").replace("Alta","3"))*2
			soma = (local_criti_qt+data_criti_qt+hora_criti_qt+mobi_criti_qt+pub_criti_qt+exp_criti_qt+fp_criti_qt+efe_criti_qt+pop_criti_qt+pt_criti_qt)
			self.med = soma

			if int(soma) <= 20:
				self.criti = "Normal"
			elif 21 <= int(soma) <= 27:
				self.criti = "Média"
			elif 28 <= int(soma) <= 35:
				self.criti = "Alta"
			elif int(soma) >= 36:
				self.criti = "Alta"
		else:
			pass

		super(Evento, self).save(*args, **kwargs)

		dias = DataEvento.objects.filter(evento_id=self.id)

		for dia in dias:
			chave = str(self.id)+""+str(dia.id)+"SISEVENT"
			try:
				zona = int(self.endere.zona.replace("Zona Norte","82").replace("Zona Sul","81").replace("Zona Oeste","79").replace("Centro","80"))
			except:
				zona = 80

			from_zone = tz.gettz('UTC')
			to_zone = tz.gettz('America/Sao_Paulo')

			utc1 = dia.data_inicio
			utc1 = utc1.replace(tzinfo=from_zone)
			central1 = utc1.astimezone(to_zone)

			utc2 = dia.data_fim
			utc2 = utc2.replace(tzinfo=from_zone)
			central2 = utc2.astimezone(to_zone)

			print(central1,central2)

			if self.respeven == "ferj":
				respeven_id = 100
			elif self.respeven == "CEPEV":
				respeven_id = 99
			elif self.respeven == "COR":
				respeven_id = 23
			elif self.respeven == "RIOTUR":
				respeven_id = 29
			elif self.respeven == "SMEL":
				respeven_id = 23
			else:
				respeven_id = 23
			#b = {"chave":chave,"descricao":"Evento: "+str(self.nome_evento)+" | Local: "+str(self.endere.local)+"\nEstimativa de público: "+str(self.qt),"inicio":central1.strftime('%Y-%m-%d %H:%M'),"fim":central2.strftime('%Y-%m-%d %H:%M'),"maisInformacoes":"","workspace_id":20,"latitude":self.endere.location.split(",")[0],"longitude":self.endere.location.split(",")[1],"endereco":self.endere.end,"regiao_id":zona,"responsavel_id":respeven_id,"tipoAtividade_id":104,"criticidade":self.criti.lower()}
			#print(b)
			#headers = {'Content-type': 'application/json', "Authorization": "Basic aW50ZWdyYWNhbzppbnRlZ3JhY2Fv"}
			#a = requests.post('http://geoportal.cor.rio.gov.br/primus/api/atividade/salvar', headers=headers,json=b)
			#a = requests.post('http://187.111.99.18/primus',json=b)
			#print(a.text)

class DataEvento(models.Model):
	evento = models.ForeignKey(Evento,on_delete=models.CASCADE,verbose_name="Evento")
	data_conce = models.DateTimeField("Horário de Concentração ou abertura dos portões",blank=True,null=True)
	data_inicio = models.DateTimeField("Início do Evento")
	data_fim = models.DateTimeField("Final do evento")
	
	class Meta:
		verbose_name = "Datas dos Eventos"
		verbose_name_plural = "Datas dos Eventos"

	def __str__(self):
		return self.evento.nome_evento+" "+self.data_inicio.strftime('%d/%m/%Y %H:%M')

	def save(self, *args, **kwargs):
		
		super(DataEvento, self).save(*args, **kwargs) 




class SecLocaisEvento(models.Model):
	evento = models.ForeignKey(Evento,on_delete=models.CASCADE,verbose_name="Evento")
	BAIRRO_CHOICE = (
		('Abolição','Abolição'),
		('Acari','Acari'),
		('Água Santa','Água Santa'),
		('Alto da Boa Vista','Alto da Boa Vista'),
		('Anchieta','Anchieta'),
		('Andaraí','Andaraí'),
		('Anil','Anil'),
		('Bancários','Bancários'),
		('Bangu','Bangu'),
		('Barra da Tijuca','Barra da Tijuca'),
		('Barra de Guaratiba','Barra de Guaratiba'),
		('Barros Filho','Barros Filho'),
		('Benfica','Benfica'),
		('Bento Ribeiro','Bento Ribeiro'),
		('Bonsucesso','Bonsucesso'),
		('Botafogo','Botafogo'),
		('Brás de Pina','Brás de Pina'),
		('Cachambi','Cachambi'),
		('Cacuia','Cacuia'),
		('Caju','Caju'),
		('Camorim','Camorim'),
		('Campinho','Campinho'),
		('Campo dos Afonsos','Campo dos Afonsos'),
		('Campo Grande','Campo Grande'),
		('Cascadura','Cascadura'),
		('Catete','Catete'),
		('Catumbi','Catumbi'),
		('Cavalcanti','Cavalcanti'),
		('Centro','Centro'),
		('Cidade de Deus','Cidade de Deus'),
		('Cidade Nova','Cidade Nova'),
		('Cidade Universitária','Cidade Universitária'),
		('Cocotá','Cocotá'),
		('Coelho Neto','Coelho Neto'),
		('Colégio','Colégio'),
		('Complexo do Alemão','Complexo do Alemão'),
		('Copacabana','Copacabana'),
		('Cordovil','Cordovil'),
		('Cosme Velho','Cosme Velho'),
		('Cosmos','Cosmos'),
		('Costa Barros','Costa Barros'),
		('Curicica','Curicica'),
		('Del Castilho','Del Castilho'),
		('Deodoro','Deodoro'),
		('Encantado','Encantado'),
		('Engenheiro Leal','Engenheiro Leal'),
		('Engenho da Rainha','Engenho da Rainha'),
		('Engenho de Dentro','Engenho de Dentro'),
		('Engenho Novo','Engenho Novo'),
		('Estácio','Estácio'),
		('Flamengo','Flamengo'),
		('Freguesia (Ilha do Governador)','Freguesia (Ilha do Governador)'),
		('Freguesia (Jacarepaguá)','Freguesia (Jacarepaguá)'),
		('Galeão','Galeão'),
		('Gamboa','Gamboa'),
		('Gardênia Azul','Gardênia Azul'),
		('Gávea','Gávea'),
		('Gericinó','Gericinó'),
		('Glória','Glória'),
		('Grajaú','Grajaú'),
		('Grumari','Grumari'),
		('Guadalupe','Guadalupe'),
		('Guaratiba','Guaratiba'),
		('Higienópolis','Higienópolis'),
		('Honório Gurgel','Honório Gurgel'),
		('Humaitá','Humaitá'),
		('Inhaúma','Inhaúma'),
		('Inhoaíba','Inhoaíba'),
		('Ipanema','Ipanema'),
		('Irajá','Irajá'),
		('Itanhangá','Itanhangá'),
		('Jacaré','Jacaré'),
		('Jacarepaguá','Jacarepaguá'),
		('Jacarezinho','Jacarezinho'),
		('Jardim América','Jardim América'),
		('Jardim Botânico','Jardim Botânico'),
		('Jardim Carioca','Jardim Carioca'),
		('Jardim Guanabara','Jardim Guanabara'),
		('Jardim Sulacap','Jardim Sulacap'),
		('Joá','Joá'),
		('Lagoa','Lagoa'),
		('Lapa','Lapa'),
		('Laranjeiras','Laranjeiras'),
		('Leblon','Leblon'),
		('Leme','Leme'),
		('Lins de Vasconcelos','Lins de Vasconcelos'),
		('Madureira','Madureira'),
		('Magalhães Bastos','Magalhães Bastos'),
		('Mangueira','Mangueira'),
		('Manguinhos','Manguinhos'),
		('Maracanã','Maracanã'),
		('Maré','Maré'),
		('Marechal Hermes','Marechal Hermes'),
		('Maria da Graça','Maria da Graça'),
		('Méier','Méier'),
		('Moneró','Moneró'),
		('Olaria','Olaria'),
		('Oswaldo Cruz','Oswaldo Cruz'),
		('Paciência','Paciência'),
		('Padre Miguel','Padre Miguel'),
		('Paquetá','Paquetá'),
		('Parada de Lucas','Parada de Lucas'),
		('Parque Anchieta','Parque Anchieta'),
		('Parque Columbia','Parque Columbia'),
		('Pavuna','Pavuna'),
		('Pechincha','Pechincha'),
		('Pedra de Guaratiba','Pedra de Guaratiba'),
		('Penha','Penha'),
		('Penha Circular','Penha Circular'),
		('Piedade','Piedade'),
		('Pilares','Pilares'),
		('Pitangueiras','Pitangueiras'),
		('Portuguesa','Portuguesa'),
		('Praça da Bandeira','Praça da Bandeira'),
		('Praça Seca','Praça Seca'),
		('Praia da Bandeira','Praia da Bandeira'),
		('Quintino Bocaiúva','Quintino Bocaiúva'),
		('Ramos','Ramos'),
		('Realengo','Realengo'),
		('Recreio dos Bandeirantes','Recreio dos Bandeirantes'),
		('Riachuelo','Riachuelo'),
		('Ribeira','Ribeira'),
		('Ricardo de Albuquerque','Ricardo de Albuquerque'),
		('Rio Comprido','Rio Comprido'),
		('Rocha','Rocha'),
		('Rocha Miranda','Rocha Miranda'),
		('Rocinha','Rocinha'),
		('Sampaio','Sampaio'),
		('Santa Cruz','Santa Cruz'),
		('Santa Teresa','Santa Teresa'),
		('Santíssimo','Santíssimo'),
		('Santo Cristo','Santo Cristo'),
		('São Conrado','São Conrado'),
		('São Cristóvão','São Cristóvão'),
		('São Francisco Xavier','São Francisco Xavier'),
		('Saúde','Saúde'),
		('Senador Camará','Senador Camará'),
		('Senador Vasconcelos','Senador Vasconcelos'),
		('Sepetiba','Sepetiba'),
		('Tanque','Tanque'),
		('Taquara','Taquara'),
		('Tauá','Tauá'),
		('Tijuca','Tijuca'),
		('Todos os Santos','Todos os Santos'),
		('Tomás Coelho','Tomás Coelho'),
		('Turiaçu','Turiaçu'),
		('Urca','Urca'),
		('Vargem Grande','Vargem Grande'),
		('Vargem Pequena','Vargem Pequena'),
		('Vasco da Gama','Vasco da Gama'),
		('Vaz Lobo','Vaz Lobo'),
		('Vicente de Carvalho','Vicente de Carvalho'),
		('Vidigal','Vidigal'),
		('Vigário Geral','Vigário Geral'),
		('Vila Cosmos','Vila Cosmos'),
		('Vila da Penha','Vila da Penha'),
		('Vila Isabel','Vila Isabel'),
		('Vila Militar','Vila Militar'),
		('Vila Valqueire','Vila Valqueire'),
		('Vista Alegre','Vista Alegre'),
		('Zumbi','Zumbi'),	
	)
	bairro = models.CharField("Bairro",max_length=30,choices=BAIRRO_CHOICE,blank=True,null=True)
	end = models.CharField("Endereço", max_length=250)
	location = PlainLocationField(verbose_name="Coordenadas", based_fields=['end'], zoom=7)
	
	class Meta:
		verbose_name = "Locais de realização do evento"
		verbose_name_plural = "Locais de realização do evento"

	def __str__(self):
		return self.evento.nome_evento+" "+self.end

	def save(self, *args, **kwargs):
		
		super(SecLocaisEvento, self).save(*args, **kwargs) 

class Previsao(models.Model):
	data = models.CharField("ID User", max_length=250,unique=True)
	nome = models.TextField("ID User")

	class Meta:
		verbose_name = "Previsão"
		verbose_name_plural = "Previsão"

	def __str__(self):
		return self.nome

class ChuvaConsolidado(models.Model):
	nome = models.TextField("ID User")

	class Meta:
		verbose_name = "Previsão"
		verbose_name_plural = "Previsão"

	def __str__(self):
		return self.nome

class TempoConsolidado(models.Model):
	nome = models.TextField("ID User")

	class Meta:
		verbose_name = "Previsão"
		verbose_name_plural = "Previsão"

	def __str__(self):
		return self.nome

class ComandoConsolidado(models.Model):
	nome = models.TextField("ID User")

	class Meta:
		verbose_name = "Previsão"
		verbose_name_plural = "Previsão"

	def __str__(self):
		return self.nome

class ComandoConsolidadoES(models.Model):
	nome = models.TextField("ID User")

	class Meta:
		verbose_name = "Previsão"
		verbose_name_plural = "Previsão"

	def __str__(self):
		return self.nome

class ComandoConsolidadoEN(models.Model):
	nome = models.TextField("ID User")

	class Meta:
		verbose_name = "Previsão"
		verbose_name_plural = "Previsão"

	def __str__(self):
		return self.nome

class ComandoConsolidadoLista(models.Model):
	nome = models.TextField("ID User")

	class Meta:
		verbose_name = "Previsão"
		verbose_name_plural = "Previsão"

	def __str__(self):
		return self.nome

class SireneConsolidado(models.Model):
	nome = models.TextField("ID User")

	class Meta:
		verbose_name = "Previsão"
		verbose_name_plural = "Previsão"

	def __str__(self):
		return self.nome

class TwitterConsolidadoTempo(models.Model):
	nome = models.TextField("ID User")

	class Meta:
		verbose_name = "Previsão"
		verbose_name_plural = "Previsão"

	def __str__(self):
		return self.nome

class TwitterConsolidadoTransito(models.Model):
	nome = models.TextField("ID User")

	class Meta:
		verbose_name = "Previsão"
		verbose_name_plural = "Previsão"

	def __str__(self):
		return self.nome

class Waze(models.Model):
	nome = models.CharField("ID User", max_length=250,unique=True)
	dia_da_semana = models.CharField("ID User", max_length=250)
	data = models.CharField("ID User", max_length=250)
	minuto = models.CharField("ID User", max_length=250)

	class Meta:
		verbose_name = "Waze time"
		verbose_name_plural = "Waze time"

	def __str__(self):
		return self.nome

class TransitoGraficoModificado(models.Model):
	data = models.CharField("ID Waze", max_length=250,unique=True)
	hora = models.CharField("ID Waze", max_length=250)
	historico1 = models.CharField("ID Waze", max_length=250)
	historico2 = models.CharField("ID Waze", max_length=250)
	historico3 = models.CharField("ID Waze", max_length=250)
	historico4 = models.CharField("ID Waze", max_length=250)
	atual1 = models.CharField("ID Waze", max_length=250)
	atual2 = models.CharField("ID Waze", max_length=250)
	atual3 = models.CharField("ID Waze", max_length=250)
	atual4 = models.CharField("ID Waze", max_length=250)
	chuva = models.CharField("ID Waze", max_length=250)
	novamedia = models.CharField("ID Waze", max_length=250,blank=True,null=True)

class TransitoGrafico(models.Model):
	data = models.CharField("ID Waze", max_length=250,unique=True)
	hora = models.CharField("ID Waze", max_length=250)
	historico = models.CharField("ID Waze", max_length=250)
	pandemia = models.CharField("ID Waze", max_length=250)
	atual = models.CharField("ID Waze", max_length=250)
	chuva = models.CharField("ID Waze", max_length=250)
	novamedia = models.CharField("ID Waze", max_length=250,blank=True,null=True)

class LightGrafico(models.Model):
	data = models.CharField("ID Waze", max_length=250,unique=True)
	hora = models.CharField("ID Waze", max_length=250)
	atual = models.CharField("ID Waze", max_length=250)
	chuva = models.CharField("ID Waze", max_length=250)
	camera = models.CharField("ID Waze",max_length=250)


class DataWazeUn(models.Model):
	estacao = models.ForeignKey(Waze,on_delete=models.CASCADE)
	id_ac = models.CharField("ID Waze", max_length=250,unique=True)
	via = models.CharField("Via", max_length=250)
	nivel = models.CharField("Nivel", max_length=250)
	velocidade_reg = models.CharField("Velocidade Registrada", max_length=250)
	velocidade_nor = models.CharField("Velocidade Normal", max_length=250)
	poli = models.TextField("Texto")

	class Meta:
		verbose_name = "DataWazeUn"
		verbose_name_plural = "DataWazeUn"

	def __str__(self):
		return self.id_tt

class TTCOR(models.Model):
	id_t = models.CharField("ID User", max_length=250,unique=True)
	twitte = models.TextField("ID User")
	rt_n = models.CharField("ID User", max_length=250)
	fav_n = models.CharField("ID User", max_length=250)
	data = models.DateTimeField("ID User", max_length=250)

	class Meta:
		verbose_name = "TTCOR"
		verbose_name_plural = "TTCOR"

	def __str__(self):
		return self.id_t

class TTCORTw(models.Model):
	estacao = models.ForeignKey(TTCOR,on_delete=models.CASCADE)
	id_t = models.CharField("ID User", max_length=250,unique=True)
	twitte = models.TextField("ID User")
	rt_n = models.CharField("ID User", max_length=250)
	fav_n = models.CharField("ID User", max_length=250)
	sentimento_d = models.CharField("ID User", max_length=250)
	sentimento_i = models.CharField("ID User", max_length=250)
	data = models.DateTimeField("ID User", max_length=250)
	usuario = models.CharField("ID User", max_length=250)
	imagem = models.CharField("ID User", max_length=250)
	nome = models.CharField("ID User", max_length=250)
	lat = models.CharField("ID User", max_length=250)
	lon = models.CharField("ID User", max_length=250)
	status = models.CharField("ID User", max_length=250)


	class Meta:
		verbose_name = "TTCORTw"
		verbose_name_plural = "TTCORTw"

	def __str__(self):
		return self.id_t


class TTCORTwCT(models.Model):
	id_t = models.CharField("ID User", max_length=250,unique=True)
	twitte = models.TextField("ID User")
	rt_n = models.CharField("ID User", max_length=250)
	fav_n = models.CharField("ID User", max_length=250)
	sentimento_d = models.CharField("ID User", max_length=250)
	sentimento_i = models.CharField("ID User", max_length=250)
	data = models.DateTimeField("ID User", max_length=250)
	usuario = models.CharField("ID User", max_length=250)
	imagem = models.CharField("ID User", max_length=250)
	nome = models.CharField("ID User", max_length=250)
	lat = models.CharField("ID User", max_length=250)
	lon = models.CharField("ID User", max_length=250)
	status = models.CharField("ID User", max_length=250)


	class Meta:
		verbose_name = "TTCORTw"
		verbose_name_plural = "TTCORTw"

	def __str__(self):
		return self.id_t


class Light(models.Model):
	nome = models.CharField("ID User", max_length=250,unique=True)

	class Meta:
		verbose_name = "Light"
		verbose_name_plural = "Light"

	def __str__(self):
		return self.nome

class LighteUn(models.Model):
	estacao = models.ForeignKey(Light,on_delete=models.CASCADE)
	bairro = models.CharField("Temperatura", max_length=250)
	lat = models.CharField("Temperatura", max_length=250)
	lon = models.CharField("Umidade", max_length=250)
	camera = models.TextField("Umidade")
	escolas = models.TextField("ID Waze")
	hospitais = models.TextField("ID Waze")

	class Meta:
		verbose_name = "LighteUn"
		verbose_name_plural = "LighteUn"

	def __str__(self):
		return self.lat


class DataWazeTr(models.Model):
	estacao = models.ForeignKey(Waze,on_delete=models.CASCADE)
	id_t = models.CharField("Via", max_length=250,unique=True)
	via = models.CharField("Via", max_length=250)
	nivel = models.CharField("Nivel", max_length=250)
	tamanho = models.CharField("Nivel", max_length=250)
	velocidade = models.CharField("Velocidade Registrada", max_length=250)
	poli = models.TextField("Texto")

	class Meta:
		verbose_name = "DataWazeUn"
		verbose_name_plural = "DataWazeUn"

	def __str__(self):
		return self.id_tt

class DataWazeTr2(models.Model):
	estacao = models.ForeignKey(Waze,on_delete=models.CASCADE)
	id_t = models.CharField("Via", max_length=250,unique=True)
	via = models.CharField("Via", max_length=250)
	nivel = models.CharField("Nivel", max_length=250)
	tamanho = models.CharField("Nivel", max_length=250)
	velocidade = models.CharField("Velocidade Registrada", max_length=250)
	poli = models.TextField("Texto")
	ap = models.CharField("Nivel", max_length=250)
	bairro = models.CharField("Nivel", max_length=250,blank=True,null=True)

	class Meta:
		verbose_name = "DataWazeUn"
		verbose_name_plural = "DataWazeUn"

	def __str__(self):
		return self.id_tt

class DataWazeAl(models.Model):
	estacao = models.ForeignKey(Waze,on_delete=models.CASCADE)
	id_alert = models.CharField("Via", max_length=250,unique=True)
	reportRating = models.IntegerField("Nivel")
	confidence = models.IntegerField("Nivel")
	reliability = models.IntegerField("Velocidade Registrada")
	tipo = models.CharField("Via", max_length=250)
	tipo_s = models.CharField("Via", max_length=250)
	tipo_v = models.CharField("Via", max_length=250)
	via = models.CharField("Via", max_length=250)
	lat = models.CharField("Temperatura", max_length=250)
	lon = models.CharField("Umidade", max_length=250)
	GRAVIDADE = (
		('Sem Status','Sem Status'),
		('Confirmado','Confirmado'),
		('Em apuração','Em apuração'),
		('Descartado','Descartado'),
		('Encerado','Encerado'),
	)
	status = models.CharField("Situação",max_length=40, choices=GRAVIDADE,blank=True,null=True)
	data = models.DateTimeField("Data", auto_now=True)

	class Meta:
		verbose_name = "DataWazeUn"
		verbose_name_plural = "DataWazeUn"

	def __str__(self):
		return self.id_tt

class GeracaoCora(models.Model):
	data = models.DateTimeField("Início do Evento", auto_now=True)
	caminho2 = models.TextField("ID User")

	class Meta:
		verbose_name = "Cora Video"
		verbose_name_plural = "Cora Video"

	def __str__(self):
		return self.caminho

	def save(self, *args, **kwargs):
		super(GeracaoCora, self).save(*args, **kwargs)

class RotaTag(models.Model):
	nome = models.CharField("Nome", max_length=250)

class Rotas(models.Model):
	tag = models.ForeignKey(RotaTag,on_delete=models.CASCADE)
	nome = models.CharField("Nome da Rota", max_length=250,unique=True)

	class Meta:
		verbose_name = "Rotas"
		verbose_name_plural = "Rotas"

	def __str__(self):
		return self.nome

class PontoRota(models.Model):
	estacao = models.ForeignKey(Rotas,on_delete=models.CASCADE)
	endereco = models.CharField("Endereço", max_length=250, blank=True,null=True,help_text="O endereço deve ser escrito da seguinte maneira: Logradouro,Número,Bairro,Cidade. Exemplo: Avenida Presidente Vargas, 500, Centro, Rio de Janeiro")
	location = PlainLocationField(based_fields=['endereco'], zoom=12, blank=True,null=True)
	
	class Meta:
		verbose_name = "Pontos das Rotas"
		verbose_name_plural = "Pontos das Rotas"

	def __str__(self):
		return self.estacao.nome

class PontoR(models.Model):
	estacao = models.ForeignKey(Rotas,on_delete=models.CASCADE)
	trecho = models.CharField("Nivel", max_length=250)
	data = models.CharField("Nivel", max_length=250)
	dia = models.CharField("Nivel", max_length=250)
	hora = models.CharField("Nivel", max_length=250)
	minuto = models.CharField("Nivel", max_length=250)
	hm = models.CharField("Nivel", max_length=250)
	tempo = models.CharField("Nivel", max_length=250)

	class Meta:
		verbose_name = "Pontos das Rotas"
		verbose_name_plural = "Pontos das Rotas"

	def __str__(self):
		return self.estacao.nome

class PontoRT(models.Model):
	estacao = models.ForeignKey(Rotas,on_delete=models.CASCADE)
	data = models.CharField("Nivel", max_length=250)
	dia = models.CharField("Nivel", max_length=250)
	hora = models.CharField("Nivel", max_length=250)
	minuto = models.CharField("Nivel", max_length=250)
	hm = models.CharField("Nivel", max_length=250)
	tempo = models.CharField("Nivel", max_length=250)

	class Meta:
		verbose_name = "Pontos das Rotas"
		verbose_name_plural = "Pontos das Rotas"

	def __str__(self):
		return self.estacao.nome



class ListaEM(models.Model):
	nome = models.CharField("Nome", max_length=250)
	email = models.EmailField("E-mail",blank=True,null=True)
	GRAVIDADE = (
		('Parceiros','Parceiros'),
		('Imprensa','Imprensa'),
	)
	grav = models.CharField("Fonte",max_length=40, choices=GRAVIDADE,blank=True,null=True)
	class Meta:
		verbose_name = "Lista de E-mails"
		verbose_name_plural =  "Lista de E-mails"

	def __str__(self):
		return self.nome


class Device_User(models.Model):
	nome = models.CharField("ID User", max_length=250,unique=True)
	modelo = models.CharField("Modelo", max_length=250)

	class Meta:
		verbose_name = "Device User"
		verbose_name_plural = "Device User"

	def __str__(self):
		return self.nome


class PontoRelatorio(models.Model):
	nome = models.CharField("ID User", max_length=250,unique=True)

	class Meta:
		verbose_name = "PontoRelatorio"
		verbose_name_plural = "PontoRelatorio"

	def __str__(self):
		return self.nome




class Device_User_Interno(models.Model):
	nome = models.CharField("ID User", max_length=250,unique=True)
	email = models.CharField("Modelo", max_length=250)	
	modelo = models.CharField("Modelo", max_length=250)

	class Meta:
		verbose_name = "Device User"
		verbose_name_plural = "Device User"

	def __str__(self):
		return self.nome

class Pontos_Hidratacao(models.Model):
	nome = models.CharField("Nome", max_length=250, blank=True,null=True)
	place_id = models.CharField(max_length=100)
	GER_CHOICE = (
		('Zona Norte', 'Zona Norte'),
		('Zona Oeste', 'Zona Oeste'),
		('Centro', 'Centro'),
		('Zona Sul', 'Zona Sul'),
	)
	zona = models.CharField("Zona da Cidade",max_length=20,choices=GER_CHOICE,blank=True,null=True)
	BAIRRO_CHOICE = (
		('Abolição','Abolição'),
		('Acari','Acari'),
		('Água Santa','Água Santa'),
		('Alto da Boa Vista','Alto da Boa Vista'),
		('Anchieta','Anchieta'),
		('Andaraí','Andaraí'),
		('Anil','Anil'),
		('Bancários','Bancários'),
		('Bangu','Bangu'),
		('Barra da Tijuca','Barra da Tijuca'),
		('Barra de Guaratiba','Barra de Guaratiba'),
		('Barros Filho','Barros Filho'),
		('Benfica','Benfica'),
		('Bento Ribeiro','Bento Ribeiro'),
		('Bonsucesso','Bonsucesso'),
		('Botafogo','Botafogo'),
		('Brás de Pina','Brás de Pina'),
		('Cachambi','Cachambi'),
		('Cacuia','Cacuia'),
		('Caju','Caju'),
		('Camorim','Camorim'),
		('Campinho','Campinho'),
		('Campo dos Afonsos','Campo dos Afonsos'),
		('Campo Grande','Campo Grande'),
		('Cascadura','Cascadura'),
		('Catete','Catete'),
		('Catumbi','Catumbi'),
		('Cavalcanti','Cavalcanti'),
		('Centro','Centro'),
		('Cidade de Deus','Cidade de Deus'),
		('Cidade Nova','Cidade Nova'),
		('Cidade Universitária','Cidade Universitária'),
		('Cocotá','Cocotá'),
		('Coelho Neto','Coelho Neto'),
		('Colégio','Colégio'),
		('Complexo do Alemão','Complexo do Alemão'),
		('Copacabana','Copacabana'),
		('Cordovil','Cordovil'),
		('Cosme Velho','Cosme Velho'),
		('Cosmos','Cosmos'),
		('Costa Barros','Costa Barros'),
		('Curicica','Curicica'),
		('Del Castilho','Del Castilho'),
		('Deodoro','Deodoro'),
		('Encantado','Encantado'),
		('Engenheiro Leal','Engenheiro Leal'),
		('Engenho da Rainha','Engenho da Rainha'),
		('Engenho de Dentro','Engenho de Dentro'),
		('Engenho Novo','Engenho Novo'),
		('Estácio','Estácio'),
		('Flamengo','Flamengo'),
		('Freguesia (Ilha do Governador)','Freguesia (Ilha do Governador)'),
		('Freguesia (Jacarepaguá)','Freguesia (Jacarepaguá)'),
		('Galeão','Galeão'),
		('Gamboa','Gamboa'),
		('Gardênia Azul','Gardênia Azul'),
		('Gávea','Gávea'),
		('Gericinó','Gericinó'),
		('Glória','Glória'),
		('Grajaú','Grajaú'),
		('Grumari','Grumari'),
		('Guadalupe','Guadalupe'),
		('Guaratiba','Guaratiba'),
		('Higienópolis','Higienópolis'),
		('Honório Gurgel','Honório Gurgel'),
		('Humaitá','Humaitá'),
		('Inhaúma','Inhaúma'),
		('Inhoaíba','Inhoaíba'),
		('Ipanema','Ipanema'),
		('Irajá','Irajá'),
		('Itanhangá','Itanhangá'),
		('Jacaré','Jacaré'),
		('Jacarepaguá','Jacarepaguá'),
		('Jacarezinho','Jacarezinho'),
		('Jardim América','Jardim América'),
		('Jardim Botânico','Jardim Botânico'),
		('Jardim Carioca','Jardim Carioca'),
		('Jardim Guanabara','Jardim Guanabara'),
		('Jardim Sulacap','Jardim Sulacap'),
		('Joá','Joá'),
		('Lagoa','Lagoa'),
		('Lapa','Lapa'),
		('Laranjeiras','Laranjeiras'),
		('Leblon','Leblon'),
		('Leme','Leme'),
		('Lins de Vasconcelos','Lins de Vasconcelos'),
		('Madureira','Madureira'),
		('Magalhães Bastos','Magalhães Bastos'),
		('Mangueira','Mangueira'),
		('Manguinhos','Manguinhos'),
		('Maracanã','Maracanã'),
		('Maré','Maré'),
		('Marechal Hermes','Marechal Hermes'),
		('Maria da Graça','Maria da Graça'),
		('Méier','Méier'),
		('Moneró','Moneró'),
		('Olaria','Olaria'),
		('Oswaldo Cruz','Oswaldo Cruz'),
		('Paciência','Paciência'),
		('Padre Miguel','Padre Miguel'),
		('Paquetá','Paquetá'),
		('Parada de Lucas','Parada de Lucas'),
		('Parque Anchieta','Parque Anchieta'),
		('Parque Columbia','Parque Columbia'),
		('Pavuna','Pavuna'),
		('Pechincha','Pechincha'),
		('Pedra de Guaratiba','Pedra de Guaratiba'),
		('Penha','Penha'),
		('Penha Circular','Penha Circular'),
		('Piedade','Piedade'),
		('Pilares','Pilares'),
		('Pitangueiras','Pitangueiras'),
		('Portuguesa','Portuguesa'),
		('Praça da Bandeira','Praça da Bandeira'),
		('Praça Seca','Praça Seca'),
		('Praia da Bandeira','Praia da Bandeira'),
		('Quintino Bocaiúva','Quintino Bocaiúva'),
		('Ramos','Ramos'),
		('Realengo','Realengo'),
		('Recreio dos Bandeirantes','Recreio dos Bandeirantes'),
		('Riachuelo','Riachuelo'),
		('Ribeira','Ribeira'),
		('Ricardo de Albuquerque','Ricardo de Albuquerque'),
		('Rio Comprido','Rio Comprido'),
		('Rocha','Rocha'),
		('Rocha Miranda','Rocha Miranda'),
		('Rocinha','Rocinha'),
		('Sampaio','Sampaio'),
		('Santa Cruz','Santa Cruz'),
		('Santa Teresa','Santa Teresa'),
		('Santíssimo','Santíssimo'),
		('Santo Cristo','Santo Cristo'),
		('São Conrado','São Conrado'),
		('São Cristóvão','São Cristóvão'),
		('São Francisco Xavier','São Francisco Xavier'),
		('Saúde','Saúde'),
		('Senador Camará','Senador Camará'),
		('Senador Vasconcelos','Senador Vasconcelos'),
		('Sepetiba','Sepetiba'),
		('Tanque','Tanque'),
		('Taquara','Taquara'),
		('Tauá','Tauá'),
		('Tijuca','Tijuca'),
		('Todos os Santos','Todos os Santos'),
		('Tomás Coelho','Tomás Coelho'),
		('Turiaçu','Turiaçu'),
		('Urca','Urca'),
		('Vargem Grande','Vargem Grande'),
		('Vargem Pequena','Vargem Pequena'),
		('Vasco da Gama','Vasco da Gama'),
		('Vaz Lobo','Vaz Lobo'),
		('Vicente de Carvalho','Vicente de Carvalho'),
		('Vidigal','Vidigal'),
		('Vigário Geral','Vigário Geral'),
		('Vila Cosmos','Vila Cosmos'),
		('Vila da Penha','Vila da Penha'),
		('Vila Isabel','Vila Isabel'),
		('Vila Militar','Vila Militar'),
		('Vila Valqueire','Vila Valqueire'),
		('Vista Alegre','Vista Alegre'),
		('Zumbi','Zumbi'),	
	)
	bairro = models.CharField("Bairro",max_length=30,choices=BAIRRO_CHOICE,blank=True,null=True)	
	endereco = models.CharField("Endereço", max_length=250, blank=True,null=True,help_text="O endereço deve ser escrito da seguinte maneira: Logradouro,Número,Bairro,Cidade. Exemplo: Avenida Presidente Vargas, 500, Centro, Rio de Janeiro")
	location = PlainLocationField(based_fields=['endereco'], zoom=12)
	resp = models.CharField("Responsável", max_length=250, blank=True,null=True)
	tel = models.CharField("Telefone", max_length=250, blank=True,null=True)
	email = models.CharField("E-mail", max_length=250, blank=True,null=True)
	loc = models.CharField("Local", max_length=250, blank=True,null=True)
	obs = models.TextField("Observações",blank=True,null=True)

	class Meta:
		verbose_name = "Pontos de resfriamento"
		verbose_name_plural = "Pontos de resfriamento"

	def __str__(self):
		return self.nome

class ResfriamentoData(models.Model):
	resfriamento = models.ForeignKey(Pontos_Hidratacao, on_delete=models.CASCADE, related_name='dados')
	timestamp = models.DateTimeField(auto_now_add=True)
	current_popularity = models.IntegerField(null=True, blank=True, help_text="Ocupação atual")
	historico_popularity = models.IntegerField(null=True, blank=True, help_text="Ocupação atual")

	def _str_(self):
		return f"{self.resfriamento.name} - {self.timestamp:%d/%m/%Y %H:%M}"

class TT(models.Model):
	id_tt = models.CharField("ID TT", max_length=250,unique=True)
	nome = models.TextField("Texto")
	arroba = models.CharField("Usuario", max_length=250)
	data = models.CharField("Data", max_length=250)

	class Meta:
		verbose_name = "Device User"
		verbose_name_plural = "Device User"

	def __str__(self):
		return self.id_tt

class CarroCom(models.Model):
	idvec = models.CharField("Estação", max_length=250,unique=True)
	placa = models.CharField("Fonte", max_length=250)
	vec = models.CharField("Fonte", max_length=250)
	frota = models.CharField("Fonte", max_length=250)
	modelo = models.CharField("Fonte", max_length=250)
	cliente = models.CharField("Fonte", max_length=250)
	empresa = models.CharField("Fonte", max_length=250)

	class Meta:
		verbose_name = "CarroCom"
		verbose_name_plural = "CarroCom"

	def __str__(self):
		return self.idvec

class DadosCarroCom(models.Model):
	estacao = models.ForeignKey(CarroCom,on_delete=models.CASCADE)
	data = models.CharField("Data", max_length=250)
	data_u = models.CharField("Data Única", max_length=250, unique=True)
	lat = models.CharField("Temperatura", max_length=250)
	lon = models.CharField("Umidade", max_length=250)
	vel = models.CharField("Umidade", max_length=250)
	rpm = models.CharField("Umidade", max_length=250)
	nome = models.CharField("Umidade", max_length=250)
	matricula = models.CharField("Umidade", max_length=250)

	class Meta:
		verbose_name = "DadosCarroCom"
		verbose_name_plural = "DadosCarroCom"

	def __str__(self):
		return self.data

class Carro(models.Model):
	placa = models.CharField("Estação", max_length=250,unique=True)
	fonte = models.CharField("Fonte", max_length=250)

	class Meta:
		verbose_name = "Frota"
		verbose_name_plural = "Frota"

	def __str__(self):
		return self.usuario

class DadosCarro(models.Model):
	estacao = models.ForeignKey(Carro,on_delete=models.CASCADE)
	data = models.CharField("Data", max_length=250)
	data_u = models.CharField("Data Única", max_length=250, unique=True)
	lat = models.CharField("Temperatura", max_length=250)
	lon = models.CharField("Umidade", max_length=250)
	vel = models.CharField("Umidade", max_length=250)

	class Meta:
		verbose_name = "Dados Carro"
		verbose_name_plural = "Dados Carro"

	def __str__(self):
		return self.usuario

class CarroCet(models.Model):
	placa = models.CharField("Estação", max_length=250,unique=True)
	fonte = models.CharField("Fonte", max_length=250)
	tipo = models.CharField("Fonte", max_length=250)

	class Meta:
		verbose_name = "Frota"
		verbose_name_plural = "Frota"

	def __str__(self):
		return self.usuario

class DadosCarroCet(models.Model):
	estacao = models.ForeignKey(CarroCet,on_delete=models.CASCADE)
	data = models.DateTimeField("Data", max_length=250)
	data_u = models.CharField("Data Única", max_length=250, unique=True)
	lat = models.CharField("Temperatura", max_length=250)
	lon = models.CharField("Umidade", max_length=250)
	vel = models.CharField("Umidade", max_length=250)

	class Meta:
		verbose_name = "Dados Carro"
		verbose_name_plural = "Dados Carro"

	def __str__(self):
		return self.usuario

class EstacaoMet(models.Model):
	lat = models.CharField("Lat", max_length=250)
	lon = models.CharField("Lon", max_length=250)
	nome = models.CharField("Estação", max_length=250)
	municipio = models.CharField("Municipio", max_length=250)
	fonte = models.CharField("Fonte", max_length=250)
	id_e = models.CharField("ID Estação", max_length=250,unique=True)

	class Meta:
		verbose_name = "Estacao Met"
		verbose_name_plural = "Estacao Met"

	def __str__(self):
		return self.usuario

class DadosMet(models.Model):
	estacao = models.ForeignKey(EstacaoMet,on_delete=models.CASCADE)
	data = models.CharField("data", max_length=250)
	data_u = models.CharField("data única", max_length=250, unique=True)
	temp = models.CharField("Temperatura", max_length=250,blank=True,null=True)
	umd = models.CharField("Umidade", max_length=250,blank=True,null=True)
	dire = models.CharField("Direção do Vento", max_length=250,blank=True,null=True)
	vel = models.CharField("Velocidade do Vento", max_length=250,blank=True,null=True)
	pre = models.CharField("Pressão", max_length=250,blank=True,null=True)
	raja = models.CharField("Velocidade do Vento", max_length=250,blank=True,null=True)
	data_aj = models.CharField("data", max_length=250,blank=True,null=True)

	class Meta:
		verbose_name = "Dados Met"
		verbose_name_plural = "Dados Met"

	def __str__(self):
		return self.usuario

class DadosMetCeu(models.Model):
	estacao = models.ForeignKey(EstacaoMet,on_delete=models.CASCADE)
	data = models.CharField("data", max_length=250)
	data_u = models.CharField("data única", max_length=250, unique=True)
	ceu = models.CharField("Temperatura", max_length=250,blank=True,null=True)

	class Meta:
		verbose_name = "Dados Met"
		verbose_name_plural = "Dados Met"

class DadosAr(models.Model):
	estacao = models.ForeignKey(EstacaoMet,on_delete=models.CASCADE)
	data = models.CharField("data", max_length=250)
	data_u = models.CharField("data única", max_length=250, unique=True)
	mp10 = models.CharField("Temperatura", max_length=250,blank=True,null=True)
	mp25 = models.CharField("Umidade", max_length=250,blank=True,null=True)
	o3 = models.CharField("Direção do Vento", max_length=250,blank=True,null=True)
	co = models.CharField("Velocidade do Vento", max_length=250,blank=True,null=True)
	no2 = models.CharField("Pressão", max_length=250,blank=True,null=True)
	so2 = models.CharField("Velocidade do Vento", max_length=250,blank=True,null=True)
	iqar_valor = models.CharField("Velocidade do Vento", max_length=250,blank=True,null=True)
	iqar_nivel = models.CharField("Velocidade do Vento", max_length=250,blank=True,null=True)

	class Meta:
		verbose_name = "Dados Met"
		verbose_name_plural = "Dados Met"

	def __str__(self):
		return self.usuario

class Sirene(models.Model):
	lat = models.CharField("Latitude", max_length=250)
	lon = models.CharField("Longitude", max_length=250)
	nome = models.CharField("Estação", max_length=250)
	endereco = models.CharField("Endereço", max_length=250, blank=True,null=True,help_text="O endereço deve ser escrito da seguinte maneira: Logradouro,Número,Bairro,Cidade. Exemplo: Avenida Presidente Vargas, 500, Centro, Rio de Janeiro")
	location = PlainLocationField(based_fields=['endereco'], zoom=12, blank=True,null=True)
	comunidade = models.CharField("Comunidade", max_length=250,blank=True,null=True)
	municipio = models.CharField("Municipio", max_length=250)
	fonte = models.CharField("Fonte", max_length=250)
	id_e = models.CharField("ID Estação", max_length=250,unique=True)

	class Meta:
		verbose_name = "Sirenes"
		verbose_name_plural = "Sirenes"

	def __str__(self):
		return self.nome

class DadosSirene(models.Model):
	estacao = models.ForeignKey(Sirene,on_delete=models.CASCADE)
	data = models.CharField("data", max_length=250)
	data_u = models.CharField("data única", max_length=250, unique=True)
	status = models.CharField("Status", max_length=250)
	tipo = models.CharField("Situação", max_length=250)
	data_t = models.DateTimeField("Data", auto_now=False, blank=True,null=True)

	class Meta:
		verbose_name = "Ocorrências Sirenes"
		verbose_name_plural = "Ocorrências Sirenes"

	def __str__(self):
		return self.estacao.nome

class DadosApp(models.Model):
	usos = models.CharField("Chuva 96h", max_length=250, blank=True,null=True)
	downloads = models.CharField("Chuva 30d", max_length=250, blank=True,null=True)
	data = models.DateTimeField("Data", auto_now=False, unique=True)

	class Meta:
		verbose_name = "Dados APP"
		verbose_name_plural = "Dados APP"

	def __str__(self):
		return self.data

class BairroApp(models.Model):
	down = models.CharField("Chuva 96h", max_length=250, blank=True,null=True)
	bairro = models.CharField("Chuva 30d", max_length=250, blank=True,null=True)
	estacao = models.ForeignKey(DadosApp,on_delete=models.CASCADE)

	class Meta:
		verbose_name = "Bairro APP"
		verbose_name_plural = "Bairro APP"

	def __str__(self):
		return self.bairro

class EstacaoPlv(models.Model):
	lat = models.CharField("Lat", max_length=250)
	lon = models.CharField("Lon", max_length=250)
	nome = models.CharField("Estação", max_length=250)
	municipio = models.CharField("Municipio", max_length=250)
	fonte = models.CharField("Fonte", max_length=250)
	id_e = models.CharField("ID Estação", max_length=250,unique=True)

	class Meta:
		verbose_name = "Estacao Plv"
		verbose_name_plural = "Estacao Plv"

	def __str__(self):
		return self.usuario

class DadosPlv(models.Model):
	estacao = models.ForeignKey(EstacaoPlv,on_delete=models.CASCADE)
	data = models.CharField("data", max_length=250)
	data_u = models.CharField("data única", max_length=250, unique=True)
	chuva_i = models.CharField("Chuva I", max_length=250, blank=True,null=True)
	chuva_1 = models.CharField("Chuva 1h", max_length=250, blank=True,null=True)
	chuva_4 = models.CharField("Chuva 4h", max_length=250, blank=True,null=True)
	chuva_24 = models.CharField("Chuva 24h", max_length=250, blank=True,null=True)
	chuva_96 = models.CharField("Chuva 96h", max_length=250, blank=True,null=True)
	chuva_30 = models.CharField("Chuva 30d", max_length=250, blank=True,null=True)
	data_t = models.DateTimeField("Data", auto_now=False)
	
	class Meta:
		verbose_name = "Dados Plv"
		verbose_name_plural = "Dados Plv"

	def __str__(self):
		return self.usuario

class EstacaoFlu(models.Model):
	lat = models.CharField("Lat", max_length=250)
	lon = models.CharField("Lon", max_length=250)
	nome = models.CharField("Estação", max_length=250)
	municipio = models.CharField("Municipio", max_length=250)
	fonte = models.CharField("Fonte", max_length=250)
	rio = models.CharField("Rio", max_length=250)
	id_e = models.CharField("ID Estação", max_length=250,unique=True)

	class Meta:
		verbose_name = "Estacao Flu"
		verbose_name_plural = "Estacao Flu"

	def __str__(self):
		return self.nome

class DadosFlu(models.Model):
	estacao = models.ForeignKey(EstacaoFlu,on_delete=models.CASCADE)
	data = models.CharField("data", max_length=250)
	data_u = models.CharField("data única", max_length=250, unique=True)
	nivel_i = models.CharField("Chuva I", max_length=250, blank=True,null=True)

	class Meta:
		verbose_name = "Dados Flu"
		verbose_name_plural = "Dados Flu"

	def __str__(self):
		return self.nivel_i

class Localizacao(models.Model):
	usuario = models.ForeignKey(Device_User,on_delete=models.CASCADE)
	lat = models.CharField("E-mail", max_length=250, blank=True,null=True)
	lon = models.CharField("Local", max_length=250, blank=True,null=True)
	data = models.CharField("Data", max_length=250, blank=True,null=True)
	vel = models.CharField("Local", max_length=250, blank=True,null=True)

	class Meta:
		verbose_name = "Localizacao Usuário"
		verbose_name_plural = "Localizacao Usuário"

	def __str__(self):
		return self.usuario

class Bairros(models.Model):
	usuario = models.ForeignKey(Device_User,on_delete=models.CASCADE)
	bairro = models.CharField("E-mail", max_length=250, blank=True,null=True)

	class Meta:
		verbose_name = "Bairros Usuário"
		verbose_name_plural = "Bairros Usuário"

	def __str__(self):
		return self.usuario



class Report(models.Model):
	nome = models.CharField("Nome", max_length=250, blank=True,null=True)
	usuario = models.ForeignKey(Device_User,on_delete=models.CASCADE)
	lat = models.CharField("E-mail", max_length=250, blank=True,null=True)
	lon = models.CharField("Local", max_length=250, blank=True,null=True)
	data = models.CharField("Data", max_length=250, blank=True,null=True)
	rua = models.CharField("Logradouro",max_length=200,blank=True,null=True)
	numero = models.CharField("Número",max_length=200,blank=True,null=True)
	bairro = models.CharField("Bairro",max_length=200,blank=True,null=True)
	cidade = models.CharField("Cidade",max_length=200,blank=True,null=True)
	status = models.CharField("Cidade",max_length=200,blank=True,null=True)

	class Meta:
		verbose_name = "Report Usuário"
		verbose_name_plural = "Report Usuário"

	def __str__(self):
		return self.nome

class ReportLinha(models.Model):
	id_c = models.CharField("Nome", max_length=250, unique=True)
	nome = models.CharField("Nome", max_length=250, blank=True,null=True)
	tipo = models.CharField("Nome", max_length=250, blank=True,null=True)
	descr = models.CharField("Nome", max_length=250, blank=True,null=True)
	lat = models.CharField("E-mail", max_length=250, blank=True,null=True)
	lon = models.CharField("Local", max_length=250, blank=True,null=True)
	data = models.CharField("Data", max_length=250, blank=True,null=True)
	rua = models.CharField("Logradouro",max_length=200,blank=True,null=True)
	numero = models.CharField("Número",max_length=200,blank=True,null=True)
	bairro = models.CharField("Bairro",max_length=200,blank=True,null=True)
	cidade = models.CharField("Cidade",max_length=200,blank=True,null=True)
	status = models.CharField("Cidade",max_length=200,blank=True,null=True)

	class Meta:
		verbose_name = "ReportLinha"
		verbose_name_plural = "ReportLinha"

	def __str__(self):
		return self.nome


class Comunidade(models.Model):
	nome = models.CharField("Nome", max_length=250)

	class Meta:
		verbose_name = "Comunidade"
		verbose_name_plural = "Comunidade"

	def __str__(self):
		return self.nome

class RodadaMar(models.Model):
	boia = models.CharField("Estação", max_length=250)
	data_rod = models.CharField("ID Estação", max_length=250,unique=True)

	class Meta:
		verbose_name = "Rodada Mar"
		verbose_name_plural = "Rodada Mar"

	def __str__(self):
		return self.usuario

class DadosMar(models.Model):
	estacao = models.ForeignKey(RodadaMar,on_delete=models.CASCADE)
	data = models.CharField("data", max_length=250)
	data_u = models.CharField("Estação", max_length=250)
	onda = models.CharField("Temperatura", max_length=250)

	class Meta:
		verbose_name = "Dados Mar"
		verbose_name_plural = "Dados Mar"

	def __str__(self):
		return self.usuario

class Guarda(models.Model):
	nome = models.CharField("Estação", max_length=250)
	id_g = models.CharField("Device", max_length=250,unique=True)
	matr = models.CharField("Matricula", max_length=250)
	escala = models.CharField("Escala", max_length=250)
	nivel = models.CharField("Nível", max_length=250)
	lotacao = models.CharField("Lotação", max_length=250,blank=True,null=True)
	posto = models.CharField("Posto", max_length=250,blank=True,null=True)
	telefone = models.CharField("Telefone", max_length=250,blank=True,null=True)

	class Meta:
		verbose_name = "Guarda"
		verbose_name_plural = "Guarda"

	def __str__(self):
		return self.device

class Posicao(models.Model):
	estacao = models.ForeignKey(Guarda,on_delete=models.CASCADE)
	data = models.CharField("data", max_length=250)
	data_u = models.CharField("Estação", max_length=250,unique=True)
	lat = models.CharField("Temperatura", max_length=250)
	lon = models.CharField("Temperatura", max_length=250)
	tipo = models.CharField("Temperatura", max_length=250)

	class Meta:
		verbose_name = "Posição Guarda"
		verbose_name_plural = "Posição Guarda"

	def __str__(self):
		return self.data

class NoahEstacao(models.Model):
	nome = models.CharField("Estação", max_length=250)
	device = models.CharField("Device", max_length=250,unique=True)
	lat = models.CharField("Lat", max_length=250)
	lon = models.CharField("Lon", max_length=250)
	ende = models.CharField("End", max_length=250)
	cotas = models.CharField("End", max_length=250,blank=True,null=True)

	class Meta:
		verbose_name = "NOAH"
		verbose_name_plural = "NOAH"

	def __str__(self):
		return self.device

class NoahDados(models.Model):
	estacao = models.ForeignKey(NoahEstacao,on_delete=models.CASCADE)
	data = models.CharField("data", max_length=250)
	data_u = models.CharField("Estação", max_length=250,unique=True)
	distancia = models.CharField("Temperatura", max_length=250)
	chuva = models.CharField("Temperatura", max_length=250)
	temp = models.CharField("Temperatura", max_length=250)
	umd = models.CharField("Temperatura", max_length=250)
	class Meta:
		verbose_name = "Dados Mar"
		verbose_name_plural = "Dados Mar"

	def __str__(self):
		return self.data

class NoahREstacao(models.Model):
	nome = models.CharField("Estação", max_length=250)
	device = models.CharField("Device", max_length=250,unique=True)
	lat = models.CharField("Lat", max_length=250)
	lon = models.CharField("Lon", max_length=250)
	ende = models.CharField("End", max_length=250)
	atencao = models.CharField("Atenção", max_length=250)
	alerta = models.CharField("Alerta", max_length=250)

	class Meta:
		verbose_name = "NoahREstacao"
		verbose_name_plural = "NoahREstacao"

	def __str__(self):
		return self.device

class NoahRDados(models.Model):
	estacao = models.ForeignKey(NoahREstacao,on_delete=models.CASCADE)
	data = models.CharField("data", max_length=250)
	data_u = models.CharField("Estação", max_length=250,unique=True)
	distancia = models.CharField("Temperatura", max_length=250)
	chuva = models.CharField("Temperatura", max_length=250)
	temp = models.CharField("Temperatura", max_length=250)
	umd = models.CharField("Temperatura", max_length=250)

	class Meta:
		verbose_name = "Dados Mar"
		verbose_name_plural = "Dados Mar"

	def __str__(self):
		return self.data


class DiaNoite(models.Model):
	data_u = models.CharField("Estação", max_length=250,unique=True)
	nascer = models.CharField("Temperatura", max_length=250)
	por = models.CharField("Temperatura", max_length=250)

	class Meta:
		verbose_name = "DiaNoite"
		verbose_name_plural = "DiaNoite"


class Flash(models.Model):
	resumo = models.TextField("Resumo")

	class Meta:
		verbose_name = "Flash Briefing"
		verbose_name_plural = "Flash Briefing"



class InterdicoesSite(models.Model):
        resumo = models.TextField("Resumo")
        data_u = models.CharField("Estação", max_length=250,unique=True)

        class Meta:
                verbose_name = "Flash Briefing"
                verbose_name_plural = "Flash Briefing"

class Modal(models.Model):
	Yes_or_no = (
		('BRT','BRT'),
		('VLT','VLT'),
		('Metro','Metro'),
		('Trem','Trem'),
		('Barcas','Barcas'),
		('Bonde','Bonde'),
	)
	tranp = models.CharField("Modal",max_length=40, choices=Yes_or_no,blank=True,null=True)
	conce = models.CharField("Concessionária",max_length=200,blank=True,null=True)
	linha = models.CharField("Linha/Ramal",max_length=200,blank=True,null=True)
	estacao = models.CharField("Estação",max_length=200,blank=True,null=True)
	end = models.CharField("Estação",max_length=200,blank=True,null=True)
	lat = models.CharField("Latitude",max_length=100,blank=True,null=True)
	lon = models.CharField("Longitude",max_length=100,blank=True,null=True)

	class Meta:
		verbose_name = "Modais de transporte"
		verbose_name_plural = "Modais de transporte"

	def __str__(self):
		return self.tranp+" - "+self.conce+" - "+self.linha+" - "+self.estacao

class OcorrenciaModal(models.Model):
	estacao = models.ForeignKey(Modal,on_delete=models.CASCADE)
	GRAVIDADE = (
		('Normal','Normal'),
		('Em atenção','Em atenção'),
		('Fechado','Fechado'),
		('Encerrado','Encerrado'),
	)
	grav = models.CharField("Situação",max_length=40, choices=GRAVIDADE,blank=True,null=True)
	mensagem = models.TextField("Observações", blank=True,null=True)
	data = models.DateTimeField("Data", auto_now=False)

	class Meta:
		verbose_name = "Ocorrências nos modais"
		verbose_name_plural = "Ocorrências nos modais"

	def __str__(self):
		return self.estacao+" - "+self.data

class SIMU(models.Model):
	Yes_or_no = (
		('BRT','BRT'),
		('VLT','VLT'),
		('Metro','Metro'),
		('Trem','Trem'),
		('Barcas','Barcas'),
		('SDU','SDU'),
		('GIG','GIG'),
	)
	tranp = models.CharField("Modal",max_length=40, choices=Yes_or_no,blank=True,null=True)
	GRAVIDADE = (
		('Normal','Normal'),
		('Em atenção','Em atenção'),
		('Fechado','Fechado'),
		('Encerrado','Encerrado'),
	)
	grav = models.CharField("Situação",max_length=40, choices=GRAVIDADE,blank=True,null=True)
	mensagem = models.TextField("Observações", blank=True,null=True)
	data = models.DateTimeField("Data", auto_now=False)

	class Meta:
		verbose_name = "CIMU"
		verbose_name_plural = "CIMU"

	def save(self, *args, **kwargs):
		tz = pytz.timezone('America/Sao_Paulo')
		self.data = datetime.now(tz)
		super(SIMU, self).save(*args, **kwargs) 
   
	def __str__(self):
		return self.mensagem


class Avisos(models.Model):
	nome = models.CharField("Titulo", max_length=250, blank=True,null=True)
	mensagem = models.TextField("Mensagem", blank=True,null=True)
	Yes_or_no = (
		('Tempo','Tempo'),
		('Trânsito','Trânsito'),
		('Evento','Evento'),
		('Sirenes','Sirenes'),
		('Carnaval - Desfiles','Carnaval - Desfiles'),
	)
	caus = models.CharField("Causador",max_length=40, choices=Yes_or_no,blank=True,null=True)
	GRAVIDADE = (
		('Baixo','Baixo'),
		('Médio','Médio'),
		('Alto','Alto'),
		('Crítico','Crítico'),
	)
	grav = models.CharField("Risco",max_length=40, choices=GRAVIDADE,blank=True,null=True)
	PXS = (
		('Sim', 'Sim'),
		('Não', 'Não'),
	)    
	valid = models.CharField("Aviso válido?",max_length=30,choices=PXS)
	data = models.DateTimeField("Data inicial", auto_now=True)
	nome_es = models.CharField("Titulo ES", max_length=250, blank=True,null=True)
	mensagem_es = models.TextField("Mensagem ES", blank=True,null=True)
	nome_en = models.CharField("Titulo EN", max_length=250, blank=True,null=True)
	mensagem_en = models.TextField("Mensagem EN", blank=True,null=True)
	
	class Meta:
		verbose_name = "Emissão de Avisos"
		verbose_name_plural = "Emissão de Avisos"

	def save(self, *args, **kwargs):
		translator = Translator()

		self.mensagem_es = translator.translate(self.mensagem,dest='es').text
		self.nome_es = translator.translate(self.nome,dest='es').text
		self.mensagem_en = translator.translate(self.mensagem,dest='en').text
		self.nome_en = translator.translate(self.nome,dest='en').text
		super(Avisos, self).save(*args, **kwargs) 
   
	def __str__(self):
		return self.mensagem

class Calor(models.Model):
        STATUS = (
                ('Nivel de calor 1', 'Nivel de calor 1'),
                ('Nivel de calor 2', 'Nivel de calor 2'),
                ('Nivel de calor 3', 'Nivel de calor 3'),
                ('Nivel de calor 4', 'Nivel de calor 4'),
                ('Nivel de calor 5', 'Nivel de calor 5'),
        )
        alive = models.CharField("Nivel de Calor",max_length=30,choices=STATUS, blank=True,null=True)
        data_i = models.DateField("Data inicial", auto_now=False, blank=True,null=True)
        data_f = models.DateField("Data final", auto_now=False, blank=True,null=True)

        class Meta:
                verbose_name = "Nível de Calor"
                verbose_name_plural = "Nível de Calor"

        def __str__(self):
                return self.alive

class Estagio(models.Model):
	STATUS = (
		('Normalidade', 'Normalidade'),
		('Mobilização', 'Mobilização'),
		('Atenção', 'Atenção'),
		('Alerta', 'Alerta'),
		('Crise', 'Crise'),
	)    
	esta = models.CharField("Estágio",max_length=30,choices=STATUS, blank=True,null=True)	
	data_i = models.DateTimeField("Data inicial", auto_now=False, blank=True,null=True)
	data_f = models.DateTimeField("Data final", auto_now=False, blank=True,null=True)
	men = models.TextField("Nota E-mail",blank=True,null=True)
	redes = models.TextField("Redes Sociais",blank=True,null=True)
	geo = models.TextField("Mensagem Status",blank=True,null=True)
	geo2 = models.TextField("Mensagem Status Segunda Linha",blank=True,null=True)
	ju = models.TextField("Tendência da chuva",blank=True,null=True)

	class Meta:
		verbose_name = "Estágio do Município"
		verbose_name_plural = "Estágio do Município"

	def __str__(self):
		return self.esta

	def save(self, *args, **kwargs):

		super(Estagio, self).save(*args, **kwargs)

		normalidade = ["Comunicar CEO (via grupo de comunicação por mensagem), Coordenador Operacional e Assessor Operacional via telefone respeitando os horários estabelecidos, sendo: Coordenador Operacional - 03:00 às 15:00h. Assessor Operacional - 15:00 às 03:00h.","Solicitar a presença do AlertaRio para informar status do tempo. Quando necessário, atividade poderá ser delegada ao apoio.","Verificar critérios para tendência de mudança de estágio junto ao respectivo órgãos competentes. Em caso de chuva, recomenda-se alinhamento com AlertaRio.","Informar mudança de regime nos seguintes grupos de mensagem: Interno, Sala de Situação, Subprefeitura e EGR.","Informar atualizações sobre ocorrências (resumo BOT) e tendência de agravamento do cenário nos seguintes grupos de mensagem: Gerenciamento de Risco, Subprefeituras, Interno, Operações e Sala de Situação. ","Em caso de previsão de chuva, divulgar relatório nos grupos de mensagem (AlertaRio, Interno, Subprefeitura, EGR, Operações, Sala de Situação, Concessionárias e CIMU) marcando o CEO, Coordenador Operacional e Assessor Operacional. Em caso de previsão de evolução de cenário atualizar/informar imediatamente aos citados acima.","Em caso de chuva, entrar em contato com meteorologista para realizar um briefing sobre a tendêcia para as próximas horas.","Informar no sistema de som do prédio sobre a mudança de regime ou estágio.","Divulgar pelos grupos de comunicação Interno e EGR a informação disponibilizada pelo AlertaRio sobre vias protocolares. ","Buscar atualizações periódicas com equipe de meteorologia ou com equipe responsável pela mudança de estágio para análise de tendência.","Acompanhar protocolos de interdições de vias protocolares por índices pluviométricos e ventos integrados pelo Centro de Operações."]
		mobilizacao = ["Comunicar CEO (via grupo de comunicação por mensagem), Coordenador Operacional e Assessor Operacional via telefone respeitando os horários estabelecidos, sendo: Coordenador Operacional - 03:00 às 15:00h. Assessor Operacional - 15:00 às 03:00h.","Solicitar a presença do AlertaRio para informar status do tempo. Quando necessário, atividade poderá ser delegada ao apoio.","Acionar o layout do videowall para o estágio, solicitando à TI para reproduzir no videowall, a depender das caracteristicas da mudança de regime (locais impactados ou com previsão de maior impacto). Quando necessário, atividade poderá ser delegada ao apoio.","Alterar a imagem do grupo (EGR) e informar mudança de estágio nos seguintes grupos de mensagem: Gerenciamento de Risco, Subprefeituras, Interno, Operações, Concessionárias, Sala de Situação, CIMU e CICC. Quando necessário, atividade poderá ser delegada ao apoio.","Ativar EGR.","Informar atualizações sobre ocorrências (resumo BOT) e tendência de agravamento do cenário nos seguintes grupos de mensagem: Gerenciamento de Risco, Subprefeituras, Interno, Operações e Sala de Situação. ","Enviar informativo para os seguintes grupos de mensagem: Concessionárias e CIMU. ","Em caso de previsão de chuva, divulgar relatório nos grupos de mensagem (AlertaRio, Interno, Subprefeitura, EGR, Operações, Sala de Situação, Concessionárias e CIMU) marcando o CEO, Coordenador Operacional e Assessor Operacional. Em caso de previsão de evolução de cenário atualizar/informar imediatamente aos citados acima.","Em caso de chuva, entrar em contato com meteorologista para realizar um briefing sobre a tendêcia para as próximas horas.","Solicitar informação sobre os recursos disponíveis por órgão, caso ainda não tenham sido informados.","Informar nos demais grupos operacionais de mensagens, inclusive grupos temporários para realização de eventos culturais na cidade em andamento ou que irão iniciar nas próximas horas.","Informar no sistema de som do prédio sobre a mudança de regime ou estágio.","Divulgar pelos grupos de comunicação Interno e EGR a informação disponibilizada pelo AlertaRio sobre vias protocolares. ","Buscar atualizações periódicas com equipe de meteorologia ou com equipe responsável pela mudança de estágio para análise de tendência.","Acompanhar protocolos de interdições de vias protocolares por índices pluviométricos e ventos integrados pelo Centro de Operações.","Quando houver tendência de aumento pluviométrico, a cada 15 minutos, divulgar nos grupos de mensagem os índices pluviométricos. Em caso de tendência de redução, atualizar a cada 30 minutos. Para tendência de chuva inferior a 1mm, realizar último informe e deixar de comunicar. ","Se necessário, mobilizar alguns colaboradores da Sala de Situação por meio de briefing operacional especial na Sala de Briefing.","Em caso de entrada em estágios sem antes passar por seus respectivos regimes, garantir a execução das atividades contidas no regime anterior."]
		atencao = ["Comunicar CEO (via grupo de comunicação por mensagem), Coordenador Operacional e Assessor Operacional via telefone respeitando os horários estabelecidos, sendo: Coordenador Operacional - 03:00 às 15:00h. Assessor Operacional - 15:00 às 03:00h.","Solicitar a presença do AlertaRio para informar status do tempo. Quando necessário, atividade poderá ser delegada ao apoio.","Acionar o layout do videowall para o estágio, solicitando à TI para reproduzir no videowall, a depender das caracteristicas da mudança de regime (locais impactados ou com previsão de maior impacto). Quando necessário, atividade poderá ser delegada ao apoio.","Verificar critérios para tendência de mudança de estágio junto ao respectivo órgãos competentes. Em caso de chuva, recomenda-se alinhamento com AlertaRio.","Alterar a imagem do grupo (EGR) e informar mudança de estágio nos seguintes grupos de mensagem: Gerenciamento de Risco, Subprefeituras, Interno, Operações, Concessionárias, Sala de Situação, CIMU e CICC. Quando necessário, atividade poderá ser delegada ao apoio.","Informar atualizações sobre ocorrências (resumo BOT) e tendência de agravamento do cenário nos seguintes grupos de mensagem: Gerenciamento de Risco, Subprefeituras, Interno, Operações e Sala de Situação. ","Enviar informativo para os seguintes grupos de mensagem: Concessionárias e CIMU. ","Em caso de previsão de chuva, divulgar relatório nos grupos de mensagem (AlertaRio, Interno, Subprefeitura, EGR, Operações, Sala de Situação, Concessionárias e CIMU) marcando o CEO, Coordenador Operacional e Assessor Operacional. Em caso de previsão de evolução de cenário atualizar/informar imediatamente aos citados acima.","Em caso de chuva, entrar em contato com meteorologista para realizar um briefing sobre a tendêcia para as próximas horas.","Solicitar informação sobre os recursos disponíveis por órgão, caso ainda não tenham sido informados.","Informar nos demais grupos operacionais de mensagens, inclusive grupos temporários para realização de eventos culturais na cidade em andamento ou que irão iniciar nas próximas horas.","Informar no sistema de som do prédio sobre a mudança de regime ou estágio.","Divulgar pelos grupos de comunicação Interno e EGR a informação disponibilizada pelo AlertaRio sobre vias protocolares. ","Buscar atualizações periódicas com equipe de meteorologia ou com equipe responsável pela mudança de estágio para análise de tendência.","Acompanhar protocolos de interdições de vias protocolares por índices pluviométricos e ventos integrados pelo Centro de Operações.","Se necessário, mobilizar alguns colaboradores da Sala de Situação por meio de briefing operacional especial na Sala de Briefing.","Realizar follow up periódico com Alerta Rio sobre situação tendência de chuva.","Realizar briefing através do sistema de áudio da Sala de Situação com representante do órgão principal frente à atuação no cenário.","Em caso de entrada em estágios sem antes passar por seus respectivos regimes, garantir a execução das atividades contidas no regime anterior."]
		alerta = ["Comunicar CEO (via grupo de comunicação por mensagem), Coordenador Operacional e Assessor Operacional via telefone respeitando os horários estabelecidos, sendo:Coordenador Operacional - 03:00 às 15:00h.Assessor Operacional - 15:00 às 03:00h.","Solicitar a presença do AlertaRio para informar status do tempo. Quando necessário, atividade poderá ser delegada ao apoio.","Acionar o layout do videowall para o estágio, solicitando à TI para reproduzir no videowall, a depender das caracteristicas da mudança de regime (locais impactados ou com previsão de maior impacto). Quando necessário, atividade poderá ser delegada ao apoio.","Verificar critérios para tendência de mudança de estágio junto ao respectivo órgãos competentes. Em caso de chuva, recomenda-se alinhamento com AlertaRio.","Alterar a imagem do grupo (EGR) e informar mudança de estágio nos seguintes grupos de mensagem: Gerenciamento de Risco, Subprefeituras, Interno, Operações, Concessionárias, Sala de Situação, CIMU e CICC. Quando necessário, atividade poderá ser delegada ao apoio.","Informar atualizações sobre ocorrências (resumo BOT) e tendência de agravamento do cenário nos seguintes grupos de mensagem: Gerenciamento de Risco, Subprefeituras, Interno, Operações e Sala de Situação. ","Enviar informativo para os seguintes grupos de mensagem: Concessionárias e CIMU. ","Em caso de previsão de chuva, divulgar relatório nos grupos de mensagem (AlertaRio, Interno, Subprefeitura, EGR, Operações, Sala de Situação, Concessionárias e CIMU) marcando o CEO, Coordenador Operacional e Assessor Operacional. Em caso de previsão de evolução de cenário atualizar/informar imediatamente aos citados acima.","Em caso de chuva, entrar em contato com meteorologista para realizar um briefing sobre a tendêcia para as próximas horas.","Solicitar informação sobre os recursos disponíveis por órgão, caso ainda não tenham sido informados.","Informar nos demais grupos operacionais de mensagens, inclusive grupos temporários para realização de eventos culturais na cidade em andamento ou que irão iniciar nas próximas horas.","Informar no sistema de som do prédio sobre a mudança de regime ou estágio.","Divulgar pelos grupos de comunicação Interno e EGR a informação disponibilizada pelo AlertaRio sobre vias protocolares. ","Buscar atualizações periódicas com equipe de meteorologia ou com equipe responsável pela mudança de estágio para análise de tendência.","Acompanhar protocolos de interdições de vias protocolares por índices pluviométricos e ventos integrados pelo Centro de Operações.","Se necessário, mobilizar alguns colaboradores da Sala de Situação por meio de briefing operacional especial na Sala de Briefing.","Realizar follow up periódico com Alerta Rio sobre situação tendência de chuva.","Realizar briefing através do sistema de áudio da Sala de Situação com representante do órgão principal frente à atuação no cenário."]
		crise = ["Comunicar CEO (via grupo de comunicação por mensagem), Coordenador Operacional e Assessor Operacional via telefone respeitando os horários estabelecidos, sendo: Coordenador Operacional - 03:00 às 15:00h. Assessor Operacional - 15:00 às 03:00h.","Solicitar a presença do AlertaRio para informar status do tempo. Quando necessário, atividade poderá ser delegada ao apoio.","Acionar o layout do videowall para o estágio, solicitando à TI para reproduzir no videowall, a depender das caracteristicas da mudança de regime (locais impactados ou com previsão de maior impacto). Quando necessário, atividade poderá ser delegada ao apoio.","Alterar a imagem do grupo (EGR) e informar mudança de estágio nos seguintes grupos de mensagem: Gerenciamento de Risco, Subprefeituras, Interno, Operações, Concessionárias, Sala de Situação, CIMU e CICC. Quando necessário, atividade poderá ser delegada ao apoio.","Informar atualizações sobre ocorrências (resumo BOT) e tendência de agravamento do cenário nos seguintes grupos de mensagem: Gerenciamento de Risco, Subprefeituras, Interno, Operações e Sala de Situação. ","Enviar informativo para os seguintes grupos de mensagem: Concessionárias e CIMU. ","Em caso de previsão de chuva, divulgar relatório nos grupos de mensagem (AlertaRio, Interno, Subprefeitura, EGR, Operações, Sala de Situação, Concessionárias e CIMU) marcando o CEO, Coordenador Operacional e Assessor Operacional. Em caso de previsão de evolução de cenário atualizar/informar imediatamente aos citados acima.","Em caso de chuva, entrar em contato com meteorologista para realizar um briefing sobre a tendêcia para as próximas horas.","Solicitar informação sobre os recursos disponíveis por órgão, caso ainda não tenham sido informados.","Informar nos demais grupos operacionais de mensagens, inclusive grupos temporários para realização de eventos culturais na cidade em andamento ou que irão iniciar nas próximas horas.","Informar no sistema de som do prédio sobre a mudança de regime ou estágio.","Divulgar pelos grupos de comunicação Interno e EGR a informação disponibilizada pelo AlertaRio sobre vias protocolares. ","Buscar atualizações periódicas com equipe de meteorologia ou com equipe responsável pela mudança de estágio para análise de tendência.","Acompanhar protocolos de interdições de vias protocolares por índices pluviométricos e ventos integrados pelo Centro de Operações.","Se necessário, mobilizar alguns colaboradores da Sala de Situação por meio de briefing operacional especial na Sala de Briefing.","Realizar follow up periódico com Alerta Rio sobre situação tendência de chuva.","Realizar briefing através do sistema de áudio da Sala de Situação com representante do órgão principal frente à atuação no cenário."]

		foo_instance = Pessoa.objects.all()
		for x in foo_instance:
			p = ConfirmacaoEstagio.objects.create(estagio_id=self.id,pessoa_id=x.id,alive="Não")
			p.save()

		if self.esta == "Normalidade":
			color = "#94c842"
			for i in normalidade:
				Atividades.objects.create(data_i=datetime.now(),data_fi=datetime.now(),tipo="Operação",criti="Baixa",descr=i,resp_id=1)
		elif self.esta == "Mobilização":
			color = "#b1b1b3"
			for i in mobilizacao:
				Atividades.objects.create(data_i=datetime.now(),data_fi=datetime.now(),tipo="Operação",criti="Baixa",descr=i,resp_id=1)
		elif self.esta == "Atenção":
			color = "#f7ce12"
			for i in atencao:
				Atividades.objects.create(data_i=datetime.now(),data_fi=datetime.now(),tipo="Operação",criti="Média",descr=i,resp_id=1)
		elif self.esta == "Alerta":
			color = "#d72d2e"
			for i in alerta:
				Atividades.objects.create(data_i=datetime.now(),data_fi=datetime.now(),tipo="Operação",criti="Alta",descr=i,resp_id=1)
		elif self.esta == "Crise":
			color = "#a155a0"
			for i in crise:
				Atividades.objects.create(data_i=datetime.now(),data_fi=datetime.now(),tipo="Operação",criti="Muito Alta",descr=i,resp_id=1)

		headers = {'Content-type': 'application/json', "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjY5MDcwODkwLCJqdGkiOiI1OGVlY2U4MGYwOTQ0MTA0YWI0MzgxODQyMWExNzkzMiIsImlkX3VzdWFyaW8iOjE4MTQyLCJwZXJmaXMiOlt7ImlkX3BlcmZpbCI6MTQsImlkX2FudW5jaWFudGUiOm51bGwsImlkX21vdG9yaXN0YSI6bnVsbCwiaWRfbG9jYWRvciI6bnVsbH1dLCJ1c3VhcmlvIjp7ImlkX3VzdWFyaW8iOjE4MTQyLCJwZXJmaXMiOlt7ImlkX3BlcmZpbCI6MTQsImlkX2FudW5jaWFudGUiOm51bGwsImlkX21vdG9yaXN0YSI6bnVsbCwiaWRfbG9jYWRvciI6bnVsbH1dfSwidXNlcmFkbWluIjoiQ09SX1JJTyIsImF1dGhUayI6IjM1MzgzNDM4MzU2MTMzMzUzMDM2MzI2MjM4MzA2NjYxMzIzMTM2MzA2NjMzNjM2MzM0NjIzMjMwMzc2NDM4MzY2MzYxMzQzODY1Mzc2NDYyNjYzNzM1NjIzNDM5MzAzOTY0MzUzNDM1MzUzNTYzNjMzNTYxMzc2NjMzNjEzNjM1In0.Ig6srzkGhqPxDMW5cZ8-1hISqpFxbuC9DcvoPKNwcPU"}
		data = {'cor': color, 'estagio': self.esta, 'mensagem': self.geo, 'mensagem2': self.geo, 'id': 1, 'inicio': self.data_i.strftime('%Y-%m-%dT%H:%M:%SZ')}
		a = requests.post('https://api.mobees.com.br/cor/estagio_api', headers=headers,data=json.dumps(data))
		print(a.text)


		
		super(Estagio, self).save(*args, **kwargs) 




class Alertas(models.Model):
	nome = models.CharField("Nome", max_length=250, blank=True,null=True)
	geom = GeometryField(blank=True,null=True)
	obs = models.TextField("Mensagem",blank=True,null=True)
	
	STATUS = (
		('Sem alarme', 'Sem alarme'),
		('Sirene', 'Sirene'),
		('Ocorrência Grave', 'Ocorrência Grave'),
	)    
	sonoro = models.CharField("Alarme Sonoro",max_length=30,choices=STATUS, blank=True,null=True)
	PXS = (
		('Sim', 'Sim'),
		('Não', 'Não'),
	)    
	pushe = models.CharField("Enviar Push?",max_length=30,choices=PXS, blank=True,null=True)
	valid = models.CharField("Alerta válido?",max_length=30,choices=PXS)
	cidade_int = models.CharField("Todos os usuários?",max_length=30,choices=PXS, blank=True,null=True)
	arquivo = models.FileField(upload_to='mp3/',blank=True,null=True,verbose_name="Arquivo de áudio")
	data = models.DateTimeField("Data",auto_now=True)
	
	nome_es = models.CharField("Titulo ES", max_length=250, blank=True,null=True)
	obs_es = models.TextField("Mensagem ES",blank=True,null=True)

	nome_en = models.CharField("Titulo EN", max_length=250, blank=True,null=True)
	obs_en = models.TextField("Mensagem EN",blank=True,null=True)
	
	nome_fr = models.CharField("Titulo FR", max_length=250, blank=True,null=True)
	obs_fr = models.TextField("Mensagem FR",blank=True,null=True)

	nome_ch = models.CharField("Titulo CH", max_length=250, blank=True,null=True)
	obs_ch = models.TextField("Mensagem CH",blank=True,null=True)


	class Meta:
		verbose_name = "Alertas"
		verbose_name_plural = "Alertas"

	def __str__(self):
		return self.nome

	def save(self, *args, **kwargs):
		super(Alertas, self).save(*args, **kwargs)
		

		#try:
		self.obs_es = GoogleTranslator(source='auto', target='es').translate(self.obs) #translator.translate(self.obs,dest='es').text
		#except:
		#	pass

		#try:
		self.nome_es = GoogleTranslator(source='auto', target='es').translate(self.nome) #translator.translate(self.nome,dest='es').text
		#except:
		#	pass



		#try:
		self.obs_en = GoogleTranslator(source='auto', target='en').translate(self.obs)#translator.translate(self.obs,dest='en').text
		#except:
		#	pass

		#try:
		self.nome_en = GoogleTranslator(source='auto', target='en').translate(self.nome) #translator.translate(self.nome,dest='en').text
		#except:
		#	pass

		#try:
		self.nome_fr = GoogleTranslator(source='auto', target='fr').translate(self.nome) #translator.translate(self.nome,dest='fr').text
		#except:
		#	pass
		self.nome_ch = self.nome_en
		self.obs_ch = self.obs_en
		#try:
		#self.nome_ch = GoogleTranslator(source='auto', target='zh-CN').translate(self.nome) #translator.translate(self.nome,dest='zh-CN').text
		#except:
		#	pass

		#try:
		self.obs_fr = GoogleTranslator(source='auto', target='fr').translate(self.obs)#translator.translate(self.obs,dest='fr').text
		#except:
		#	pass

		#try:
		#self.obs_ch = GoogleTranslator(source='auto', target='zh-CN').translate(self.obs)#translator.translate(self.obs,dest='zh-CN').text
		#except:
		#	pass

		try:
			os.system("/home/cocr.servicos/.local/bin/ftransc -f mp3 /home/cocr.servicos/app_cor/"+str(self.arquivo.url))
			os.system("cp /home/cocr.servicos/app_cor/"+str(self.arquivo.url)[:-4]+".mp3 /var/www/media/mp3/")
		except:
			pass
		#if self.pushe == "Sim":
		#	subprocess.call('nohup python3.6 /home/cocr.servicos/app_cor/mandar_alerta.py "'+str(self.id)+'" &', shell=True)
		#	subprocess.call('nohup python3.6 /home/cocr.servicos/app_cor/mandar_alerta_2.py "'+str(self.id)+'" &', shell=True)
		#	subprocess.call('nohup python3.6 /home/cocr.servicos/app_cor/mandar_alerta_3.py "'+str(self.id)+'" &', shell=True)
		#	subprocess.call('nohup python3.6 /home/cocr.servicos/app_cor/mandar_alerta_4.py "'+str(self.id)+'" &', shell=True)
		#if self.cidade_int == "Sim":
		#	if self.pushe == "Sim":
		#		foo_instance = Device_User.objects.all()
		#		for x in foo_instance:
		#			p = Receber.objects.create(alerta_id=self.id,usuario_id=x.id,status="Não enviado")
		#			p.save()
		#elif self.cidade_int == "Não" and self.pushe == "Não":
		#	pass
		#else:
			#if (self.geom['type'] == "Polygon"):
				#lats = []
				#lons = []


				#x = 0
				#while x != len(self.geom['coordinates'][0]):
				#	lats.append(self.geom['coordinates'][0][x][1])
				#	lons.append(self.geom['coordinates'][0][x][0])
				#	x += 1

				#minimo_lat = min(lats)
				#minimo_lon = min(lons)
				#maximo_lat = max(lats)
				#maximo_lon = max(lons)

				#if self.pushe == "Sim":
					#ids = []
					#if self.sonoro == "Sirene":
					#	foo_instance = Device_User.objects.all()
					#	for x in foo_instance:
					#		#try:
					#		if 1 == 1:
					#			ultimo = Localizacao.objects.filter(usuario_id=x.id).latest("id")
					#			lat_2 = float(ultimo.lat)
					#			lon_2 = float(ultimo.lon)
					#			if minimo_lat < lat_2 < maximo_lat:
					#				if minimo_lon < lon_2 < maximo_lon:
					#					p = Receber.objects.create(alerta_id=self.id,usuario_id=x.id,status="Não enviado")
					#					p.save()
							#except TypeError:
							#	pass
							#except AttributeError:
							#	pass
							#except:
							#	pass
					#else:
					#	pass
						#cmd = ' '.join(["nohup", settings.CRAWL_SH_ABS_PATH, "db_profiles_spider", "ids", ids, '&'])
					#	subprocess.call('nohup python3.6 /home/cocr.servicos/app_cor/mandar_alerta.py "'+str(self.id)+'" &', shell=True)
							#push_service = FCMNotification(api_key="AAAAjHO5ryo:APA91bHh0Q_I3vw9Q64HlCNtBQDsGT2oD00yyrmXs2a9mbKcKxJZY25DZfM5zK23ko-PzORMQUe31nV2BfvUG3J36I7xfQwLrIRzpcLVHuI1myPXfOl4Ft8a1zYhv1ANk9G0xhBn1U0F")
							#foo_instance = Device_User.objects.all()
							#for x in foo_instance:
							#	try:
							#		ultimo = Localizacao.objects.filter(usuario_id=x.id).latest("id")
							#		lat_2 = float(ultimo.lat)
							#		lon_2 = float(ultimo.lon)
							#		if minimo_lat < lat_2 < maximo_lat:
							#			if minimo_lon < lon_2 < maximo_lon:
							#				p = Receber.objects.create(alerta_id=self.id,usuario_id=x.id,status="Não enviado")
							#				p.save()							
							#	except Localizacao.DoesNotExist:
							#		pass
							#	except ValueError:
							#		pass
							#	except:
							#		pass
			
		#self.pushe = "Não"
		super(Alertas, self).save(*args, **kwargs) 

class Receber(models.Model):
	usuario = models.ForeignKey(Device_User,on_delete=models.CASCADE)
	alerta = models.ForeignKey(Alertas,on_delete=models.CASCADE)
	status = models.CharField("Status", max_length=250, blank=True,null=True)

	class Meta:
		verbose_name = "Receber Alertas"
		verbose_name_plural = "Receber Alertas"


class Pontos_de_Apoio(models.Model):
	nome = models.CharField("Nome", max_length=250, blank=True,null=True)
	GER_CHOICE = (
		('Zona Norte', 'Zona Norte'),
		('Zona Oeste', 'Zona Oeste'),
		('Centro', 'Centro'),
		('Zona Sul', 'Zona Sul'),
	)
	zona = models.CharField("Zona da Cidade",max_length=20,choices=GER_CHOICE,blank=True,null=True)
	BAIRRO_CHOICE = (
		('Abolição','Abolição'),
		('Acari','Acari'),
		('Água Santa','Água Santa'),
		('Alto da Boa Vista','Alto da Boa Vista'),
		('Anchieta','Anchieta'),
		('Andaraí','Andaraí'),
		('Anil','Anil'),
		('Bancários','Bancários'),
		('Bangu','Bangu'),
		('Barra da Tijuca','Barra da Tijuca'),
		('Barra de Guaratiba','Barra de Guaratiba'),
		('Barros Filho','Barros Filho'),
		('Benfica','Benfica'),
		('Bento Ribeiro','Bento Ribeiro'),
		('Bonsucesso','Bonsucesso'),
		('Botafogo','Botafogo'),
		('Brás de Pina','Brás de Pina'),
		('Cachambi','Cachambi'),
		('Cacuia','Cacuia'),
		('Caju','Caju'),
		('Camorim','Camorim'),
		('Campinho','Campinho'),
		('Campo dos Afonsos','Campo dos Afonsos'),
		('Campo Grande','Campo Grande'),
		('Cascadura','Cascadura'),
		('Catete','Catete'),
		('Catumbi','Catumbi'),
		('Cavalcanti','Cavalcanti'),
		('Centro','Centro'),
		('Cidade de Deus','Cidade de Deus'),
		('Cidade Nova','Cidade Nova'),
		('Cidade Universitária','Cidade Universitária'),
		('Cocotá','Cocotá'),
		('Coelho Neto','Coelho Neto'),
		('Colégio','Colégio'),
		('Complexo do Alemão','Complexo do Alemão'),
		('Copacabana','Copacabana'),
		('Cordovil','Cordovil'),
		('Cosme Velho','Cosme Velho'),
		('Cosmos','Cosmos'),
		('Costa Barros','Costa Barros'),
		('Curicica','Curicica'),
		('Del Castilho','Del Castilho'),
		('Deodoro','Deodoro'),
		('Encantado','Encantado'),
		('Engenheiro Leal','Engenheiro Leal'),
		('Engenho da Rainha','Engenho da Rainha'),
		('Engenho de Dentro','Engenho de Dentro'),
		('Engenho Novo','Engenho Novo'),
		('Estácio','Estácio'),
		('Flamengo','Flamengo'),
		('Freguesia (Ilha do Governador)','Freguesia (Ilha do Governador)'),
		('Freguesia (Jacarepaguá)','Freguesia (Jacarepaguá)'),
		('Galeão','Galeão'),
		('Gamboa','Gamboa'),
		('Gardênia Azul','Gardênia Azul'),
		('Gávea','Gávea'),
		('Gericinó','Gericinó'),
		('Glória','Glória'),
		('Grajaú','Grajaú'),
		('Grumari','Grumari'),
		('Guadalupe','Guadalupe'),
		('Guaratiba','Guaratiba'),
		('Higienópolis','Higienópolis'),
		('Honório Gurgel','Honório Gurgel'),
		('Humaitá','Humaitá'),
		('Inhaúma','Inhaúma'),
		('Inhoaíba','Inhoaíba'),
		('Ipanema','Ipanema'),
		('Irajá','Irajá'),
		('Itanhangá','Itanhangá'),
		('Jacaré','Jacaré'),
		('Jacarepaguá','Jacarepaguá'),
		('Jacarezinho','Jacarezinho'),
		('Jardim América','Jardim América'),
		('Jardim Botânico','Jardim Botânico'),
		('Jardim Carioca','Jardim Carioca'),
		('Jardim Guanabara','Jardim Guanabara'),
		('Jardim Sulacap','Jardim Sulacap'),
		('Joá','Joá'),
		('Lagoa','Lagoa'),
		('Lapa','Lapa'),
		('Laranjeiras','Laranjeiras'),
		('Leblon','Leblon'),
		('Leme','Leme'),
		('Lins de Vasconcelos','Lins de Vasconcelos'),
		('Madureira','Madureira'),
		('Magalhães Bastos','Magalhães Bastos'),
		('Mangueira','Mangueira'),
		('Manguinhos','Manguinhos'),
		('Maracanã','Maracanã'),
		('Maré','Maré'),
		('Marechal Hermes','Marechal Hermes'),
		('Maria da Graça','Maria da Graça'),
		('Méier','Méier'),
		('Moneró','Moneró'),
		('Olaria','Olaria'),
		('Oswaldo Cruz','Oswaldo Cruz'),
		('Paciência','Paciência'),
		('Padre Miguel','Padre Miguel'),
		('Paquetá','Paquetá'),
		('Parada de Lucas','Parada de Lucas'),
		('Parque Anchieta','Parque Anchieta'),
		('Parque Columbia','Parque Columbia'),
		('Pavuna','Pavuna'),
		('Pechincha','Pechincha'),
		('Pedra de Guaratiba','Pedra de Guaratiba'),
		('Penha','Penha'),
		('Penha Circular','Penha Circular'),
		('Piedade','Piedade'),
		('Pilares','Pilares'),
		('Pitangueiras','Pitangueiras'),
		('Portuguesa','Portuguesa'),
		('Praça da Bandeira','Praça da Bandeira'),
		('Praça Seca','Praça Seca'),
		('Praia da Bandeira','Praia da Bandeira'),
		('Quintino Bocaiúva','Quintino Bocaiúva'),
		('Ramos','Ramos'),
		('Realengo','Realengo'),
		('Recreio dos Bandeirantes','Recreio dos Bandeirantes'),
		('Riachuelo','Riachuelo'),
		('Ribeira','Ribeira'),
		('Ricardo de Albuquerque','Ricardo de Albuquerque'),
		('Rio Comprido','Rio Comprido'),
		('Rocha','Rocha'),
		('Rocha Miranda','Rocha Miranda'),
		('Rocinha','Rocinha'),
		('Sampaio','Sampaio'),
		('Santa Cruz','Santa Cruz'),
		('Santa Teresa','Santa Teresa'),
		('Santíssimo','Santíssimo'),
		('Santo Cristo','Santo Cristo'),
		('São Conrado','São Conrado'),
		('São Cristóvão','São Cristóvão'),
		('São Francisco Xavier','São Francisco Xavier'),
		('Saúde','Saúde'),
		('Senador Camará','Senador Camará'),
		('Senador Vasconcelos','Senador Vasconcelos'),
		('Sepetiba','Sepetiba'),
		('Tanque','Tanque'),
		('Taquara','Taquara'),
		('Tauá','Tauá'),
		('Tijuca','Tijuca'),
		('Todos os Santos','Todos os Santos'),
		('Tomás Coelho','Tomás Coelho'),
		('Turiaçu','Turiaçu'),
		('Urca','Urca'),
		('Vargem Grande','Vargem Grande'),
		('Vargem Pequena','Vargem Pequena'),
		('Vasco da Gama','Vasco da Gama'),
		('Vaz Lobo','Vaz Lobo'),
		('Vicente de Carvalho','Vicente de Carvalho'),
		('Vidigal','Vidigal'),
		('Vigário Geral','Vigário Geral'),
		('Vila Cosmos','Vila Cosmos'),
		('Vila da Penha','Vila da Penha'),
		('Vila Isabel','Vila Isabel'),
		('Vila Militar','Vila Militar'),
		('Vila Valqueire','Vila Valqueire'),
		('Vista Alegre','Vista Alegre'),
		('Zumbi','Zumbi'),	
	)
	bairro = models.CharField("Bairro",max_length=30,choices=BAIRRO_CHOICE,blank=True,null=True)	
	endereco = models.CharField("Endereço", max_length=250, blank=True,null=True,help_text="O endereço deve ser escrito da seguinte maneira: Logradouro,Número,Bairro,Cidade. Exemplo: Avenida Presidente Vargas, 500, Centro, Rio de Janeiro")
	location = PlainLocationField(based_fields=['endereco'], zoom=12)
	resp = models.CharField("Responsável", max_length=250, blank=True,null=True)
	tel = models.CharField("Telefone", max_length=250, blank=True,null=True)
	email = models.CharField("E-mail", max_length=250, blank=True,null=True)
	loc = models.CharField("Local", max_length=250, blank=True,null=True)
	obs = models.TextField("Observações",blank=True,null=True)

	class Meta:
		verbose_name = "Pontos de Apoio"
		verbose_name_plural = "Pontos de Apoio"

	def __str__(self):
		return self.nome



class Bolsao(models.Model):
	
	origem = models.CharField("Origem",max_length=250,blank=True,null=True)
	posicao = models.CharField("Posição nos Top 50",max_length=250,blank=True,null=True)
	dia = models.CharField("Diagnóstico",max_length=250,blank=True,null=True)
	Acio_CHOICE = (
		('Comlumbr', 'Comlumbr'),
		('Seconserva', 'Seconserva'),
		('Ambas', 'Ambas'),
	)
	acionamento = models.CharField("Quem acionar na chuva?",max_length=20,choices=Acio_CHOICE,blank=True,null=True)
	ap = models.CharField("AP",max_length=20,blank=True,null=True)
	BAIRRO_CHOICE = (
		('Abolição','Abolição'),
		('Acari','Acari'),
		('Água Santa','Água Santa'),
		('Alto da Boa Vista','Alto da Boa Vista'),
		('Anchieta','Anchieta'),
		('Andaraí','Andaraí'),
		('Anil','Anil'),
		('Bancários','Bancários'),
		('Bangu','Bangu'),
		('Barra da Tijuca','Barra da Tijuca'),
		('Barra de Guaratiba','Barra de Guaratiba'),
		('Barros Filho','Barros Filho'),
		('Benfica','Benfica'),
		('Bento Ribeiro','Bento Ribeiro'),
		('Bonsucesso','Bonsucesso'),
		('Botafogo','Botafogo'),
		('Brás de Pina','Brás de Pina'),
		('Cachambi','Cachambi'),
		('Cacuia','Cacuia'),
		('Caju','Caju'),
		('Camorim','Camorim'),
		('Campinho','Campinho'),
		('Campo dos Afonsos','Campo dos Afonsos'),
		('Campo Grande','Campo Grande'),
		('Cascadura','Cascadura'),
		('Catete','Catete'),
		('Catumbi','Catumbi'),
		('Cavalcanti','Cavalcanti'),
		('Centro','Centro'),
		('Cidade de Deus','Cidade de Deus'),
		('Cidade Nova','Cidade Nova'),
		('Cidade Universitária','Cidade Universitária'),
		('Cocotá','Cocotá'),
		('Coelho Neto','Coelho Neto'),
		('Colégio','Colégio'),
		('Complexo do Alemão','Complexo do Alemão'),
		('Copacabana','Copacabana'),
		('Cordovil','Cordovil'),
		('Cosme Velho','Cosme Velho'),
		('Cosmos','Cosmos'),
		('Costa Barros','Costa Barros'),
		('Curicica','Curicica'),
		('Del Castilho','Del Castilho'),
		('Deodoro','Deodoro'),
		('Encantado','Encantado'),
		('Engenheiro Leal','Engenheiro Leal'),
		('Engenho da Rainha','Engenho da Rainha'),
		('Engenho de Dentro','Engenho de Dentro'),
		('Engenho Novo','Engenho Novo'),
		('Estácio','Estácio'),
		('Flamengo','Flamengo'),
		('Freguesia (Ilha do Governador)','Freguesia (Ilha do Governador)'),
		('Freguesia (Jacarepaguá)','Freguesia (Jacarepaguá)'),
		('Galeão','Galeão'),
		('Gamboa','Gamboa'),
		('Gardênia Azul','Gardênia Azul'),
		('Gávea','Gávea'),
		('Gericinó','Gericinó'),
		('Glória','Glória'),
		('Grajaú','Grajaú'),
		('Grumari','Grumari'),
		('Guadalupe','Guadalupe'),
		('Guaratiba','Guaratiba'),
		('Higienópolis','Higienópolis'),
		('Honório Gurgel','Honório Gurgel'),
		('Humaitá','Humaitá'),
		('Inhaúma','Inhaúma'),
		('Inhoaíba','Inhoaíba'),
		('Ipanema','Ipanema'),
		('Irajá','Irajá'),
		('Itanhangá','Itanhangá'),
		('Jacaré','Jacaré'),
		('Jacarepaguá','Jacarepaguá'),
		('Jacarezinho','Jacarezinho'),
		('Jardim América','Jardim América'),
		('Jardim Botânico','Jardim Botânico'),
		('Jardim Carioca','Jardim Carioca'),
		('Jardim Guanabara','Jardim Guanabara'),
		('Jardim Sulacap','Jardim Sulacap'),
		('Joá','Joá'),
		('Lagoa','Lagoa'),
		('Lapa','Lapa'),
		('Laranjeiras','Laranjeiras'),
		('Leblon','Leblon'),
		('Leme','Leme'),
		('Lins de Vasconcelos','Lins de Vasconcelos'),
		('Madureira','Madureira'),
		('Magalhães Bastos','Magalhães Bastos'),
		('Mangueira','Mangueira'),
		('Manguinhos','Manguinhos'),
		('Maracanã','Maracanã'),
		('Maré','Maré'),
		('Marechal Hermes','Marechal Hermes'),
		('Maria da Graça','Maria da Graça'),
		('Méier','Méier'),
		('Moneró','Moneró'),
		('Olaria','Olaria'),
		('Oswaldo Cruz','Oswaldo Cruz'),
		('Paciência','Paciência'),
		('Padre Miguel','Padre Miguel'),
		('Paquetá','Paquetá'),
		('Parada de Lucas','Parada de Lucas'),
		('Parque Anchieta','Parque Anchieta'),
		('Parque Columbia','Parque Columbia'),
		('Pavuna','Pavuna'),
		('Pechincha','Pechincha'),
		('Pedra de Guaratiba','Pedra de Guaratiba'),
		('Penha','Penha'),
		('Penha Circular','Penha Circular'),
		('Piedade','Piedade'),
		('Pilares','Pilares'),
		('Pitangueiras','Pitangueiras'),
		('Portuguesa','Portuguesa'),
		('Praça da Bandeira','Praça da Bandeira'),
		('Praça Seca','Praça Seca'),
		('Praia da Bandeira','Praia da Bandeira'),
		('Quintino Bocaiúva','Quintino Bocaiúva'),
		('Ramos','Ramos'),
		('Realengo','Realengo'),
		('Recreio dos Bandeirantes','Recreio dos Bandeirantes'),
		('Riachuelo','Riachuelo'),
		('Ribeira','Ribeira'),
		('Ricardo de Albuquerque','Ricardo de Albuquerque'),
		('Rio Comprido','Rio Comprido'),
		('Rocha','Rocha'),
		('Rocha Miranda','Rocha Miranda'),
		('Rocinha','Rocinha'),
		('Sampaio','Sampaio'),
		('Santa Cruz','Santa Cruz'),
		('Santa Teresa','Santa Teresa'),
		('Santíssimo','Santíssimo'),
		('Santo Cristo','Santo Cristo'),
		('São Conrado','São Conrado'),
		('São Cristóvão','São Cristóvão'),
		('São Francisco Xavier','São Francisco Xavier'),
		('Saúde','Saúde'),
		('Senador Camará','Senador Camará'),
		('Senador Vasconcelos','Senador Vasconcelos'),
		('Sepetiba','Sepetiba'),
		('Tanque','Tanque'),
		('Taquara','Taquara'),
		('Tauá','Tauá'),
		('Tijuca','Tijuca'),
		('Todos os Santos','Todos os Santos'),
		('Tomás Coelho','Tomás Coelho'),
		('Turiaçu','Turiaçu'),
		('Urca','Urca'),
		('Vargem Grande','Vargem Grande'),
		('Vargem Pequena','Vargem Pequena'),
		('Vasco da Gama','Vasco da Gama'),
		('Vaz Lobo','Vaz Lobo'),
		('Vicente de Carvalho','Vicente de Carvalho'),
		('Vidigal','Vidigal'),
		('Vigário Geral','Vigário Geral'),
		('Vila Cosmos','Vila Cosmos'),
		('Vila da Penha','Vila da Penha'),
		('Vila Isabel','Vila Isabel'),
		('Vila Militar','Vila Militar'),
		('Vila Valqueire','Vila Valqueire'),
		('Vista Alegre','Vista Alegre'),
		('Zumbi','Zumbi'),	
	)
	bairro = models.CharField("Bairro",max_length=30,choices=BAIRRO_CHOICE,blank=True,null=True)
	respo = models.CharField("Responsável",max_length=120,blank=True,null=True)	
	pa = models.ForeignKey(Pontos_de_Apoio,on_delete=models.CASCADE,blank=True,null=True)
	endereco = models.CharField("Endereço", max_length=250, blank=True,null=True,help_text="O endereço deve ser escrito da seguinte maneira: Logradouro,Número,Bairro,Cidade. Exemplo: Avenida Presidente Vargas, 500, Centro, Rio de Janeiro")
	location = PlainLocationField(based_fields=['endereco'], zoom=12)
	tempo = models.CharField("Tempo de escoamento",max_length=10,blank=True,null=True,help_text="O formato deverá ser hh:mm:ss")		
	desc = models.TextField("Descrição",blank=True,null=True)
	obs = models.TextField("Observações",blank=True,null=True)
	fonte = models.CharField("Fonte",max_length=30,blank=True,null=True)

	class Meta:
		verbose_name = "Bolsão"
		verbose_name_plural = "Bolsão"

	def __str__(self):
		return self.endereco

class BolsaoFechamento(models.Model):
	pa = models.ForeignKey(Bolsao,on_delete=models.CASCADE)
	Tipo_fe = (
		('Desvio','Desvio'),
		('Interdição','Interdição'),
	)
	tipo = models.CharField("Tipo do ponto",max_length=40, choices=Tipo_fe,blank=True,null=True)
	endereco = models.CharField("Endereço", max_length=250, blank=True,null=True,help_text="O endereço deve ser escrito da seguinte maneira: Logradouro,Número,Bairro,Cidade. Exemplo: Avenida Presidente Vargas, 500, Centro, Rio de Janeiro")
	location = PlainLocationField(based_fields=['endereco'], zoom=12)
	resp = models.CharField("Responsável", max_length=250, blank=True,null=True)

	class Meta:
		verbose_name = "Ponto de bloqueio"
		verbose_name_plural = "Ponto de bloqueio"

	def __str__(self):
		return self.endereco


class ViasFechamento(models.Model):
	via = models.CharField("Via de interdição", max_length=250, blank=True,null=True,help_text="O nome da via deve ser escrito da seguinte maneira: Logradouro,Número,Bairro,Cidade. Exemplo: Avenida Presidente Vargas, 500, Centro, Rio de Janeiro")
	Tipo_fe = (
		('Desvio','Desvio'),
		('Interdição','Interdição'),
	)
	tipo = models.CharField("Tipo do ponto",max_length=40, choices=Tipo_fe,blank=True,null=True)
	location = PlainLocationField(based_fields=['endereco'], zoom=12)
	resp = models.CharField("Responsável", max_length=250, blank=True,null=True)
	
	class Meta:
		verbose_name = "Ponto de bloqueio"
		verbose_name_plural = "Ponto de bloqueio"

	def __str__(self):
		return self.via

class StatusPA(models.Model):
    pa = models.ForeignKey(Pontos_de_Apoio, on_delete=models.CASCADE)
    Yes_or_no = (
        ('Aberto', 'Aberto'),
        ('Fechado', 'Fechado'),
    )
    oper = models.CharField("Status do Ponto de Apoio",
                            max_length=40, choices=Yes_or_no, blank=True, null=True)
    data = models.DateTimeField("Data", auto_now=True)
    data_abertura = models.DateTimeField("Data abertura", auto_now=False)

    class Meta:
        verbose_name = "Status do Ponto de Apoio"
        verbose_name_plural = "Status do Ponto de Apoio"

    def __str__(self):
        return self.oper

class Ocorrencias(models.Model):
	data = models.DateTimeField("Data",unique=True)
	data_f = models.DateTimeField("Data Fechamento",blank=True,null=True)
	GER_CHOICE = (
		('Zona Norte', 'Zona Norte'),
		('Zona Oeste', 'Zona Oeste'),
		('Centro', 'Centro'),
		('Zona Sul', 'Zona Sul'),
		('Toda a Cidade', 'Toda a Cidade'),
	)
	gerencia = models.CharField("Zona da Cidade",max_length=20,choices=GER_CHOICE,blank=True,null=True)
	BAIRRO_CHOICE = (
		('Abolição','Abolição'),
		('Acari','Acari'),
		('Água Santa','Água Santa'),
		('Alto da Boa Vista','Alto da Boa Vista'),
		('Anchieta','Anchieta'),
		('Andaraí','Andaraí'),
		('Anil','Anil'),
		('Bancários','Bancários'),
		('Bangu','Bangu'),
		('Barra da Tijuca','Barra da Tijuca'),
		('Barra de Guaratiba','Barra de Guaratiba'),
		('Barros Filho','Barros Filho'),
		('Benfica','Benfica'),
		('Bento Ribeiro','Bento Ribeiro'),
		('Bonsucesso','Bonsucesso'),
		('Botafogo','Botafogo'),
		('Brás de Pina','Brás de Pina'),
		('Cachambi','Cachambi'),
		('Cacuia','Cacuia'),
		('Caju','Caju'),
		('Camorim','Camorim'),
		('Campinho','Campinho'),
		('Campo dos Afonsos','Campo dos Afonsos'),
		('Campo Grande','Campo Grande'),
		('Cascadura','Cascadura'),
		('Catete','Catete'),
		('Catumbi','Catumbi'),
		('Cavalcanti','Cavalcanti'),
		('Centro','Centro'),
		('Cidade de Deus','Cidade de Deus'),
		('Cidade Nova','Cidade Nova'),
		('Cidade Universitária','Cidade Universitária'),
		('Cocotá','Cocotá'),
		('Coelho Neto','Coelho Neto'),
		('Colégio','Colégio'),
		('Complexo do Alemão','Complexo do Alemão'),
		('Copacabana','Copacabana'),
		('Cordovil','Cordovil'),
		('Cosme Velho','Cosme Velho'),
		('Cosmos','Cosmos'),
		('Costa Barros','Costa Barros'),
		('Curicica','Curicica'),
		('Del Castilho','Del Castilho'),
		('Deodoro','Deodoro'),
		('Encantado','Encantado'),
		('Engenheiro Leal','Engenheiro Leal'),
		('Engenho da Rainha','Engenho da Rainha'),
		('Engenho de Dentro','Engenho de Dentro'),
		('Engenho Novo','Engenho Novo'),
		('Estácio','Estácio'),
		('Flamengo','Flamengo'),
		('Freguesia (Ilha do Governador)','Freguesia (Ilha do Governador)'),
		('Freguesia (Jacarepaguá)','Freguesia (Jacarepaguá)'),
		('Galeão','Galeão'),
		('Gamboa','Gamboa'),
		('Gardênia Azul','Gardênia Azul'),
		('Gávea','Gávea'),
		('Gericinó','Gericinó'),
		('Glória','Glória'),
		('Grajaú','Grajaú'),
		('Grumari','Grumari'),
		('Guadalupe','Guadalupe'),
		('Guaratiba','Guaratiba'),
		('Higienópolis','Higienópolis'),
		('Honório Gurgel','Honório Gurgel'),
		('Humaitá','Humaitá'),
		('Inhaúma','Inhaúma'),
		('Inhoaíba','Inhoaíba'),
		('Ipanema','Ipanema'),
		('Irajá','Irajá'),
		('Itanhangá','Itanhangá'),
		('Jacaré','Jacaré'),
		('Jacarepaguá','Jacarepaguá'),
		('Jacarezinho','Jacarezinho'),
		('Jardim América','Jardim América'),
		('Jardim Botânico','Jardim Botânico'),
		('Jardim Carioca','Jardim Carioca'),
		('Jardim Guanabara','Jardim Guanabara'),
		('Jardim Sulacap','Jardim Sulacap'),
		('Joá','Joá'),
		('Lagoa','Lagoa'),
		('Lapa','Lapa'),
		('Laranjeiras','Laranjeiras'),
		('Leblon','Leblon'),
		('Leme','Leme'),
		('Lins de Vasconcelos','Lins de Vasconcelos'),
		('Madureira','Madureira'),
		('Magalhães Bastos','Magalhães Bastos'),
		('Mangueira','Mangueira'),
		('Manguinhos','Manguinhos'),
		('Maracanã','Maracanã'),
		('Maré','Maré'),
		('Marechal Hermes','Marechal Hermes'),
		('Maria da Graça','Maria da Graça'),
		('Méier','Méier'),
		('Moneró','Moneró'),
		('Olaria','Olaria'),
		('Oswaldo Cruz','Oswaldo Cruz'),
		('Paciência','Paciência'),
		('Padre Miguel','Padre Miguel'),
		('Paquetá','Paquetá'),
		('Parada de Lucas','Parada de Lucas'),
		('Parque Anchieta','Parque Anchieta'),
		('Parque Columbia','Parque Columbia'),
		('Pavuna','Pavuna'),
		('Pechincha','Pechincha'),
		('Pedra de Guaratiba','Pedra de Guaratiba'),
		('Penha','Penha'),
		('Penha Circular','Penha Circular'),
		('Piedade','Piedade'),
		('Pilares','Pilares'),
		('Pitangueiras','Pitangueiras'),
		('Portuguesa','Portuguesa'),
		('Praça da Bandeira','Praça da Bandeira'),
		('Praça Seca','Praça Seca'),
		('Praia da Bandeira','Praia da Bandeira'),
		('Quintino Bocaiúva','Quintino Bocaiúva'),
		('Ramos','Ramos'),
		('Realengo','Realengo'),
		('Recreio dos Bandeirantes','Recreio dos Bandeirantes'),
		('Riachuelo','Riachuelo'),
		('Ribeira','Ribeira'),
		('Ricardo de Albuquerque','Ricardo de Albuquerque'),
		('Rio Comprido','Rio Comprido'),
		('Rocha','Rocha'),
		('Rocha Miranda','Rocha Miranda'),
		('Rocinha','Rocinha'),
		('Sampaio','Sampaio'),
		('Santa Cruz','Santa Cruz'),
		('Santa Teresa','Santa Teresa'),
		('Santíssimo','Santíssimo'),
		('Santo Cristo','Santo Cristo'),
		('São Conrado','São Conrado'),
		('São Cristóvão','São Cristóvão'),
		('São Francisco Xavier','São Francisco Xavier'),
		('Saúde','Saúde'),
		('Senador Camará','Senador Camará'),
		('Senador Vasconcelos','Senador Vasconcelos'),
		('Sepetiba','Sepetiba'),
		('Tanque','Tanque'),
		('Taquara','Taquara'),
		('Tauá','Tauá'),
		('Tijuca','Tijuca'),
		('Todos os Santos','Todos os Santos'),
		('Tomás Coelho','Tomás Coelho'),
		('Turiaçu','Turiaçu'),
		('Urca','Urca'),
		('Vargem Grande','Vargem Grande'),
		('Vargem Pequena','Vargem Pequena'),
		('Vasco da Gama','Vasco da Gama'),
		('Vaz Lobo','Vaz Lobo'),
		('Vicente de Carvalho','Vicente de Carvalho'),
		('Vidigal','Vidigal'),
		('Vigário Geral','Vigário Geral'),
		('Vila Cosmos','Vila Cosmos'),
		('Vila da Penha','Vila da Penha'),
		('Vila Isabel','Vila Isabel'),
		('Vila Militar','Vila Militar'),
		('Vila Valqueire','Vila Valqueire'),
		('Vista Alegre','Vista Alegre'),
		('Zumbi','Zumbi'),	
	)
	bairro = models.CharField("Bairro",max_length=30,choices=BAIRRO_CHOICE,blank=True,null=True)
	log = models.CharField("Logradouro",max_length=250,blank=True,null=True)
	id_c = models.CharField("Id do comando",max_length=250,blank=True,null=True)
	location = PlainLocationField(based_fields=['log'], zoom=7,blank=True,null=True)
	incidente = models.CharField("Tipo de incidente",max_length=100,blank=True,null=True)
	obs = models.TextField("Observações",blank=True,null=True)
	STATUS_CHOICE = (
		('Concluído', 'Concluído'),
		('Em atendimento', 'Em atendimento'),
		('Acionado', 'Acionado'),
	)
	status = models.CharField("Status",max_length=20,choices=STATUS_CHOICE,blank=True,null=True)
	PRIORIDADE_CHOICE = (
		('SECUNDÁRIO', 'SECUNDÁRIO'),
		('BAIXO', 'BAIXO'),
		('MEDIO', 'MEDIO'),
		('ALTO', 'ALTO'),
		('CRITICO', 'CRITICO'),
	)
	prio = models.CharField("Criticidade",max_length=20,choices=PRIORIDADE_CHOICE,blank=True,null=True)
	tipo_forma = models.CharField(max_length=50, default='circle')  # circle ou polygon
	raio = models.FloatField(null=True, blank=True)
	lat = models.FloatField(null=True, blank=True)
	lon = models.FloatField(null=True, blank=True)
	poligono_coords = models.TextField(null=True, blank=True) 
	class Meta:
		verbose_name = "Ocorrências"
		verbose_name_plural = "Ocorrências"

	def __str__(self):
		return self.incidente+" "+self.log

class OcorrenciasSec(models.Model):
	data = models.DateTimeField("Data",unique=True)
	GER_CHOICE = (
		('Zona Norte', 'Zona Norte'),
		('Zona Oeste', 'Zona Oeste'),
		('Centro', 'Centro'),
		('Zona Sul', 'Zona Sul'),
		('Toda a Cidade', 'Toda a Cidade'),
	)
	gerencia = models.CharField("Zona da Cidade",max_length=20,choices=GER_CHOICE,blank=True,null=True)
	BAIRRO_CHOICE = (
		('Abolição','Abolição'),
		('Acari','Acari'),
		('Água Santa','Água Santa'),
		('Alto da Boa Vista','Alto da Boa Vista'),
		('Anchieta','Anchieta'),
		('Andaraí','Andaraí'),
		('Anil','Anil'),
		('Bancários','Bancários'),
		('Bangu','Bangu'),
		('Barra da Tijuca','Barra da Tijuca'),
		('Barra de Guaratiba','Barra de Guaratiba'),
		('Barros Filho','Barros Filho'),
		('Benfica','Benfica'),
		('Bento Ribeiro','Bento Ribeiro'),
		('Bonsucesso','Bonsucesso'),
		('Botafogo','Botafogo'),
		('Brás de Pina','Brás de Pina'),
		('Cachambi','Cachambi'),
		('Cacuia','Cacuia'),
		('Caju','Caju'),
		('Camorim','Camorim'),
		('Campinho','Campinho'),
		('Campo dos Afonsos','Campo dos Afonsos'),
		('Campo Grande','Campo Grande'),
		('Cascadura','Cascadura'),
		('Catete','Catete'),
		('Catumbi','Catumbi'),
		('Cavalcanti','Cavalcanti'),
		('Centro','Centro'),
		('Cidade de Deus','Cidade de Deus'),
		('Cidade Nova','Cidade Nova'),
		('Cidade Universitária','Cidade Universitária'),
		('Cocotá','Cocotá'),
		('Coelho Neto','Coelho Neto'),
		('Colégio','Colégio'),
		('Complexo do Alemão','Complexo do Alemão'),
		('Copacabana','Copacabana'),
		('Cordovil','Cordovil'),
		('Cosme Velho','Cosme Velho'),
		('Cosmos','Cosmos'),
		('Costa Barros','Costa Barros'),
		('Curicica','Curicica'),
		('Del Castilho','Del Castilho'),
		('Deodoro','Deodoro'),
		('Encantado','Encantado'),
		('Engenheiro Leal','Engenheiro Leal'),
		('Engenho da Rainha','Engenho da Rainha'),
		('Engenho de Dentro','Engenho de Dentro'),
		('Engenho Novo','Engenho Novo'),
		('Estácio','Estácio'),
		('Flamengo','Flamengo'),
		('Freguesia (Ilha do Governador)','Freguesia (Ilha do Governador)'),
		('Freguesia (Jacarepaguá)','Freguesia (Jacarepaguá)'),
		('Galeão','Galeão'),
		('Gamboa','Gamboa'),
		('Gardênia Azul','Gardênia Azul'),
		('Gávea','Gávea'),
		('Gericinó','Gericinó'),
		('Glória','Glória'),
		('Grajaú','Grajaú'),
		('Grumari','Grumari'),
		('Guadalupe','Guadalupe'),
		('Guaratiba','Guaratiba'),
		('Higienópolis','Higienópolis'),
		('Honório Gurgel','Honório Gurgel'),
		('Humaitá','Humaitá'),
		('Inhaúma','Inhaúma'),
		('Inhoaíba','Inhoaíba'),
		('Ipanema','Ipanema'),
		('Irajá','Irajá'),
		('Itanhangá','Itanhangá'),
		('Jacaré','Jacaré'),
		('Jacarepaguá','Jacarepaguá'),
		('Jacarezinho','Jacarezinho'),
		('Jardim América','Jardim América'),
		('Jardim Botânico','Jardim Botânico'),
		('Jardim Carioca','Jardim Carioca'),
		('Jardim Guanabara','Jardim Guanabara'),
		('Jardim Sulacap','Jardim Sulacap'),
		('Joá','Joá'),
		('Lagoa','Lagoa'),
		('Lapa','Lapa'),
		('Laranjeiras','Laranjeiras'),
		('Leblon','Leblon'),
		('Leme','Leme'),
		('Lins de Vasconcelos','Lins de Vasconcelos'),
		('Madureira','Madureira'),
		('Magalhães Bastos','Magalhães Bastos'),
		('Mangueira','Mangueira'),
		('Manguinhos','Manguinhos'),
		('Maracanã','Maracanã'),
		('Maré','Maré'),
		('Marechal Hermes','Marechal Hermes'),
		('Maria da Graça','Maria da Graça'),
		('Méier','Méier'),
		('Moneró','Moneró'),
		('Olaria','Olaria'),
		('Oswaldo Cruz','Oswaldo Cruz'),
		('Paciência','Paciência'),
		('Padre Miguel','Padre Miguel'),
		('Paquetá','Paquetá'),
		('Parada de Lucas','Parada de Lucas'),
		('Parque Anchieta','Parque Anchieta'),
		('Parque Columbia','Parque Columbia'),
		('Pavuna','Pavuna'),
		('Pechincha','Pechincha'),
		('Pedra de Guaratiba','Pedra de Guaratiba'),
		('Penha','Penha'),
		('Penha Circular','Penha Circular'),
		('Piedade','Piedade'),
		('Pilares','Pilares'),
		('Pitangueiras','Pitangueiras'),
		('Portuguesa','Portuguesa'),
		('Praça da Bandeira','Praça da Bandeira'),
		('Praça Seca','Praça Seca'),
		('Praia da Bandeira','Praia da Bandeira'),
		('Quintino Bocaiúva','Quintino Bocaiúva'),
		('Ramos','Ramos'),
		('Realengo','Realengo'),
		('Recreio dos Bandeirantes','Recreio dos Bandeirantes'),
		('Riachuelo','Riachuelo'),
		('Ribeira','Ribeira'),
		('Ricardo de Albuquerque','Ricardo de Albuquerque'),
		('Rio Comprido','Rio Comprido'),
		('Rocha','Rocha'),
		('Rocha Miranda','Rocha Miranda'),
		('Rocinha','Rocinha'),
		('Sampaio','Sampaio'),
		('Santa Cruz','Santa Cruz'),
		('Santa Teresa','Santa Teresa'),
		('Santíssimo','Santíssimo'),
		('Santo Cristo','Santo Cristo'),
		('São Conrado','São Conrado'),
		('São Cristóvão','São Cristóvão'),
		('São Francisco Xavier','São Francisco Xavier'),
		('Saúde','Saúde'),
		('Senador Camará','Senador Camará'),
		('Senador Vasconcelos','Senador Vasconcelos'),
		('Sepetiba','Sepetiba'),
		('Tanque','Tanque'),
		('Taquara','Taquara'),
		('Tauá','Tauá'),
		('Tijuca','Tijuca'),
		('Todos os Santos','Todos os Santos'),
		('Tomás Coelho','Tomás Coelho'),
		('Turiaçu','Turiaçu'),
		('Urca','Urca'),
		('Vargem Grande','Vargem Grande'),
		('Vargem Pequena','Vargem Pequena'),
		('Vasco da Gama','Vasco da Gama'),
		('Vaz Lobo','Vaz Lobo'),
		('Vicente de Carvalho','Vicente de Carvalho'),
		('Vidigal','Vidigal'),
		('Vigário Geral','Vigário Geral'),
		('Vila Cosmos','Vila Cosmos'),
		('Vila da Penha','Vila da Penha'),
		('Vila Isabel','Vila Isabel'),
		('Vila Militar','Vila Militar'),
		('Vila Valqueire','Vila Valqueire'),
		('Vista Alegre','Vista Alegre'),
		('Zumbi','Zumbi'),	
	)
	bairro = models.CharField("Bairro",max_length=30,choices=BAIRRO_CHOICE,blank=True,null=True)
	log = models.CharField("Logradouro",max_length=250,blank=True,null=True)
	location = PlainLocationField(based_fields=['log'], zoom=7,blank=True,null=True)
	incidente = models.CharField("Tipo de incidente",max_length=100,blank=True,null=True)
	obs = models.TextField("Observações",blank=True,null=True)
	STATUS_CHOICE = (
		('Concluído', 'Concluído'),
		('Em atendimento', 'Em atendimento'),
		('Acionado', 'Acionado'),
	)
	status = models.CharField("Status",max_length=20,choices=STATUS_CHOICE,blank=True,null=True)
	PRIORIDADE_CHOICE = (
		('BAIXO', 'BAIXO'),
		('MEDIO', 'MEDIO'),
		('ALTO', 'ALTO'),
		('CRITICO', 'CRITICO'),
	)
	prio = models.CharField("Criticidade",max_length=20,choices=PRIORIDADE_CHOICE,blank=True,null=True)
	class Meta:
		verbose_name = "Ocorrência Secundária"
		verbose_name_plural = "Ocorrência Secundária"

	def __str__(self):
		return self.incidente+" "+self.log

class OcorrenciasSecAtu(models.Model):
	estacao = models.ForeignKey(OcorrenciasSec,on_delete=models.CASCADE)
	men = models.TextField("Mensagem",blank=True,null=True)

	class Meta:
		verbose_name = "Atualização de Ocorrência Secundária"
		verbose_name_plural = "Atualizações de Ocorrências Secundárias"

	def __str__(self):
		return self.nome

	def save(self, *args, **kwargs):
		super(OcorrenciasSecAtu, self).save(*args, **kwargs) 


class OcorrenciasFoto(models.Model):
	estacao = models.ForeignKey(Ocorrencias,on_delete=models.CASCADE)
	foto = models.CharField("Foto",unique=True,max_length=250)



class Metrica(models.Model):
	estacao = models.ForeignKey(Alertas,on_delete=models.CASCADE)
	total = models.CharField(max_length=20,blank=True,null=True)
	lido = models.CharField(max_length=20,blank=True,null=True)
	

class Chegada(models.Model):
	id_c = models.CharField("Lat", max_length=250)
	email = models.CharField("ID Estação", max_length=250)
	data = models.CharField("ID Estação", max_length=250)
	lat = models.CharField("ID Estação", max_length=250)
	lon = models.CharField("ID Estação", max_length=250)
	cc = models.CharField("ID Estação", max_length=250,unique=True)

	class Meta:
		verbose_name = "Chegada"
		verbose_name_plural = "Chegada"

	def __str__(self):
		return self.cc

class Encerrada(models.Model):
	id_c = models.CharField("Lat", max_length=250)
	email = models.CharField("ID Estação", max_length=250)
	foto2 = models.ImageField(upload_to='uploads/',verbose_name="Foto", blank=True,null=True)

	class Meta:
		verbose_name = "Chegada"
		verbose_name_plural = "Chegada"

	def __str__(self):
		return self.cc

class Orgao(models.Model):
	nome = models.CharField("Nome", max_length=250,unique=True)

	class Meta:
		verbose_name = "Orgão"
		verbose_name_plural = "Orgão"

	def __str__(self):
		return self.nome

class Local2(models.Model):
	local = models.ForeignKey(Orgao,on_delete=models.CASCADE,verbose_name="Órgão")
	nome = models.CharField("Nome", max_length=250)
	endereco = models.CharField("Endereço", max_length=250, blank=True,null=True,help_text="O endereço deve ser escrito da seguinte maneira: Logradouro,Número,Bairro,Cidade. Exemplo: Avenida Presidente Vargas, 500, Centro, Rio de Janeiro")
	resp = models.CharField("Responsável", max_length=250, blank=True,null=True)
	tel = models.CharField("Telefone", max_length=250, blank=True,null=True)
	email = models.CharField("E-mail", max_length=250, blank=True,null=True)
	location = PlainLocationField(based_fields=['endereco'], zoom=12, blank=True,null=True)

	class Meta:
		verbose_name = "Local do Orgão"
		verbose_name_plural = "Local do Orgão"

	def __str__(self):
		return ""+str(self.local.nome)+" - "+str(self.nome)


class Recurso(models.Model):
	local = models.ForeignKey(Local2,on_delete=models.CASCADE,verbose_name="Local do órgão")
	nome = models.CharField("Nome", max_length=250)
	quantidade = models.IntegerField("Quantiade do recurso")
	resp = models.CharField("Responsável", max_length=250, blank=True,null=True)
	tel = models.CharField("Telefone", max_length=250, blank=True,null=True)
	email = models.CharField("E-mail", max_length=250, blank=True,null=True)

	class Meta:
		verbose_name = "Recurso"
		verbose_name_plural = "Recurso"

	def __str__(self):
		return ""+str(self.local.nome)+" - "+str(self.nome)


class MobilizarRecurso(models.Model):
	recurso = models.ForeignKey(Recurso,on_delete=models.CASCADE,verbose_name="Recurso")
	local = models.ForeignKey(Local2,on_delete=models.CASCADE,verbose_name="Local de destino do recurso")
	quantidade = models.IntegerField("Quantiade do recurso")
	STATUS_CHOICE = (
		('Mobilizado', 'Mobilizado'),
		('Desmobilizado', 'Desmobilizado'),
	)
	status = models.CharField("Situação",max_length=20,choices=STATUS_CHOICE,blank=True,null=True)
	data_i = models.TimeField("Hora inicial",blank=True,null=True)
	data_f = models.TimeField("Hora final",blank=True,null=True)
	DIA_CHOICE = (
		('Dias úteis', 'Dias úteis'),
		('Sábado', 'Sábado'),
		('Domingo', 'Domingo'),
		('Feriado', 'Feriado'),
		('Todos os dias', 'Todos os dias'),
	)
	dia = models.CharField("Situação",max_length=20,choices=DIA_CHOICE,blank=True,null=True)

	class Meta:
		verbose_name = "Mobilizar Recurso"
		verbose_name_plural = "Mobilizar Recurso"

	def __str__(self):
		return str(self.recurso.nome)+" - "+str(self.local.nome)+" - "+str(self.quantidade)

class AlocarRecurso(models.Model):
	recurso = models.ForeignKey(Recurso,on_delete=models.CASCADE,verbose_name="Recurso")
	ocorrencia = models.ForeignKey(Ocorrencias,limit_choices_to={'status': "ABERTO"},on_delete=models.CASCADE,verbose_name="Ocorrência")
	STATUS_CHOICE = (
		('Mobilizado', 'Mobilizado'),
		('Desmobilizado', 'Desmobilizado'),
	)
	status = models.CharField("Situação",max_length=20,choices=STATUS_CHOICE,blank=True,null=True)
	quantidade = models.IntegerField("Quantiade do recurso")
	camera = models.CharField("Câmera",max_length=20,blank=True,null=True)

	class Meta:
		verbose_name = "Alocar Recurso"
		verbose_name_plural = "Alocar Recurso"

	def __str__(self):
		return str(self.recurso.nome)+" - "+str(self.ocorrencia.log)+" - "+str(self.quantidade)

class CeTInterdicao(models.Model):
	interdicao = models.TextField("Interdição")
	GRAVIDADE = (
		('Baixa','Baixa'),
		('Média','Média'),
		('Alta','Alta'),
	)
	titulo = models.CharField("Titulo",max_length=240,blank=True,null=True)
	status = models.CharField("Risco",max_length=40, choices=GRAVIDADE,blank=True,null=True)
	data_inicial = models.DateTimeField("Data de início", auto_now=False,blank=True,null=True)
	data_final = models.DateTimeField("Data de fim", auto_now=False,blank=True,null=True)
	endere = models.ForeignKey(DataEvento,on_delete=models.CASCADE,verbose_name="Evento Associado",blank=True,null=True)
	motivo = models.CharField("Motivo",max_length=40, blank=True,null=True)
	class Meta:
		verbose_name = "Interdição Cet Rio"
		verbose_name_plural = "Interdição Cet Rio"

	def __str__(self):
		return self.interdicao

class CeTInterdicaoRua(models.Model):
	recurso = models.ForeignKey(CeTInterdicao,on_delete=models.CASCADE,verbose_name="Interdição")
	data_inicial = models.DateTimeField("Data de início", auto_now=False,blank=True,null=True)
	data_final = models.DateTimeField("Data de fim", auto_now=False,blank=True,null=True)
	rua = models.CharField("Rua",max_length=200, blank=True,null=True)
	endereco = models.CharField("Endereço",max_length=200, blank=True,null=True)
	lat1 = models.CharField("Lat",max_length=200, blank=True,null=True)
	lon1 = models.CharField("Lon",max_length=200, blank=True,null=True)
	lat2 = models.CharField("Lat",max_length=200, blank=True,null=True)
	lon2 = models.CharField("Lon",max_length=200, blank=True,null=True)
	poly = models.TextField("Interdição", blank=True,null=True)
	bairro = models.CharField("Rua",max_length=200, blank=True,null=True)
class TransitoGraficoAp(models.Model):
	data = models.CharField("ID Waze", max_length=250)
	hora = models.CharField("ID Waze", max_length=250)
	dataap = models.CharField("ID Waze", max_length=250,unique=True)
	historico = models.CharField("ID Waze", max_length=250)
	pandemia = models.CharField("ID Waze", max_length=250)
	atual = models.CharField("ID Waze", max_length=250)
	chuva = models.CharField("ID Waze", max_length=250)
	ap = models.CharField("ID Waze", max_length=250)

class RiscoBairroR(models.Model):
	data = models.CharField("ID Waze", max_length=250)

class RiscoBairro(models.Model):
	recurso = models.ForeignKey(RiscoBairroR,on_delete=models.CASCADE,verbose_name="Recurso")
	data = models.CharField("ID Waze", max_length=250)
	bairro = models.CharField("ID Waze", max_length=250)
	tag = models.CharField("ID Waze", max_length=250,unique=True)
	risco_u = models.CharField("ID Waze", max_length=250)
	fator_u = models.CharField("ID Waze", max_length=250)
	risco_c = models.CharField("ID Waze", max_length=250)
	fator_c = models.CharField("ID Waze", max_length=250)

class Poligono(models.Model):
	nome = models.CharField("Nome", max_length=250, blank=True,null=True)
	geom = GeometryField(blank=True,null=True)
	data = models.DateTimeField("Data",auto_now=True)

	class Meta:
		verbose_name = "Zona de interesse"
		verbose_name_plural = "Zona de interesse"

	def __str__(self):
		return self.nome

	def save(self, *args, **kwargs):
		super(Poligono, self).save(*args, **kwargs) 

class PoligonoChuva(models.Model):
	nome = models.CharField("Nome", max_length=250, blank=True,null=True)
	geom = GeometryField(blank=True,null=True)
	data_i = models.DateTimeField("Data Inicial",auto_now=False)
	data_f = models.DateTimeField("Data Final",auto_now=False)

	class Meta:
		verbose_name = "Zona de interesse - Chuva"
		verbose_name_plural = "Zona de interesse - Chuva"

	def __str__(self):
		return self.nome

	def save(self, *args, **kwargs):
		super(PoligonoChuva, self).save(*args, **kwargs) 

class RiscoPoliR(models.Model):
	data = models.CharField("ID Waze", max_length=250)

class RiscoPoli(models.Model):
	recurso = models.ForeignKey(RiscoPoliR,on_delete=models.CASCADE,verbose_name="Recurso")
	data = models.CharField("ID Waze", max_length=250)
	bairro = models.CharField("ID Waze", max_length=250)
	tag = models.CharField("ID Waze", max_length=250,unique=True)
	risco_u = models.CharField("ID Waze", max_length=250)
	fator_u = models.CharField("ID Waze", max_length=250)

class TTDD(models.Model):
	id_t = models.CharField("ID User", max_length=250,unique=True)
	twitte = models.TextField("ID User")
	rt_n = models.CharField("ID User", max_length=250)
	fav_n = models.CharField("ID User", max_length=250)
	data = models.DateTimeField("ID User", max_length=250)

	class Meta:
		verbose_name = "TTCOR"
		verbose_name_plural = "TTCOR"

	def __str__(self):
		return self.id_t

class TTDDTw(models.Model):
	estacao = models.ForeignKey(TTDD,on_delete=models.CASCADE)
	id_t = models.CharField("ID User", max_length=250,unique=True)
	twitte = models.TextField("ID User")
	rt_n = models.CharField("ID User", max_length=250)
	fav_n = models.CharField("ID User", max_length=250)
	sentimento_d = models.CharField("ID User", max_length=250)
	sentimento_i = models.CharField("ID User", max_length=250)
	data = models.DateTimeField("ID User", max_length=250)
	usuario = models.CharField("ID User", max_length=250)
	imagem = models.CharField("ID User", max_length=250)
	nome = models.CharField("ID User", max_length=250)
	lat = models.CharField("ID User", max_length=250)
	lon = models.CharField("ID User", max_length=250)
	status = models.CharField("ID User", max_length=250)


	class Meta:
		verbose_name = "TTCORTw"
		verbose_name_plural = "TTCORTw"

	def __str__(self):
		return self.id_t


class TTDDTwCT(models.Model):
	id_t = models.CharField("ID User", max_length=250,unique=True)
	twitte = models.TextField("ID User")
	rt_n = models.CharField("ID User", max_length=250)
	fav_n = models.CharField("ID User", max_length=250)
	sentimento_d = models.CharField("ID User", max_length=250)
	sentimento_i = models.CharField("ID User", max_length=250)
	data = models.DateTimeField("ID User", max_length=250)
	usuario = models.CharField("ID User", max_length=250)
	imagem = models.CharField("ID User", max_length=250)
	nome = models.CharField("ID User", max_length=250)
	lat = models.CharField("ID User", max_length=250)
	lon = models.CharField("ID User", max_length=250)
	status = models.CharField("ID User", max_length=250)


	class Meta:
		verbose_name = "TTCORTw"
		verbose_name_plural = "TTCORTw"

	def __str__(self):
		return self.id_t

class TTI(models.Model):
	termo = models.CharField("Termo",max_length=250,blank=True,null=True)
	STATUS_CHOICE = (
		('Usuário', 'Usuário'),
		('Palavra-Chave', 'Palavra-Chave'),
	)
	status = models.CharField("Tipo",max_length=20,choices=STATUS_CHOICE,blank=True,null=True)

	class Meta:
		verbose_name = "Busca de termos Twitter"
		verbose_name_plural = "Busca de termos Twitter"

	def __str__(self):
		return str(self.termo)

class TTFl(models.Model):
	estacao = models.ForeignKey(TTI,on_delete=models.CASCADE)
	id_t = models.CharField("ID User", max_length=250,unique=True)
	twitte = models.TextField("ID User")
	rt_n = models.CharField("ID User", max_length=250)
	fav_n = models.CharField("ID User", max_length=250)
	data = models.DateTimeField("ID User", max_length=250)

	class Meta:
		verbose_name = "TTCOR"
		verbose_name_plural = "TTCOR"

	def __str__(self):
		return self.id_t

class TTFlTw(models.Model):
	estacao = models.ForeignKey(TTFl,on_delete=models.CASCADE)
	id_t = models.CharField("ID User", max_length=250,unique=True)
	twitte = models.TextField("ID User")
	rt_n = models.CharField("ID User", max_length=250)
	fav_n = models.CharField("ID User", max_length=250)
	sentimento_d = models.CharField("ID User", max_length=250)
	sentimento_i = models.CharField("ID User", max_length=250)
	data = models.DateTimeField("ID User", max_length=250)
	usuario = models.CharField("ID User", max_length=250)
	imagem = models.CharField("ID User", max_length=250)
	nome = models.CharField("ID User", max_length=250)
	lat = models.CharField("ID User", max_length=250)
	lon = models.CharField("ID User", max_length=250)
	status = models.CharField("ID User", max_length=250)


	class Meta:
		verbose_name = "TTCORTw"
		verbose_name_plural = "TTCORTw"

	def __str__(self):
		return self.id_t

#---

class Mensageria(models.Model):
	identificador = models.CharField("ID User", max_length=250)
	data_i = models.DateTimeField("Data Inicial")
	data_f = models.DateTimeField("Data Final",blank=True,null=True)
	lat = models.CharField("ID User", max_length=250)
	lon = models.CharField("ID User", max_length=250)
	status = models.CharField("ID User", max_length=250)
	critidade = models.FloatField("ID User")
	critidade_nivel = models.CharField("ID User", max_length=250)
	estacao = models.CharField("ID User", max_length=250)
	estacao_id = models.CharField("ID User", max_length=250)
	fonte = models.CharField("ID User", max_length=250)
	operador = models.CharField("ID User", max_length=250,blank=True,null=True)
	data_b = models.DateTimeField("Data Final",blank=True,null=True)

	class Meta:
		verbose_name = "Mensageria"
		verbose_name_plural = "Mensageria"

	def __str__(self):
		return self.lat

class KML(models.Model):
	nome = models.CharField("Nome do arquivo", max_length=250)
	slug = models.SlugField(max_length=100, blank=True,null=True)
	arquivo = models.FileField(upload_to='uploads/',verbose_name="Arquivo", blank=True,null=True)
	
	class Meta:
		verbose_name = "KML"
		verbose_name_plural = "KML"

	def __str__(self):
		return self.nome

	def save(self, *args, **kwargs):
		self.slug = slugify(self.nome).replace("-","_")
		super(KML, self).save(*args, **kwargs)

class MinutoMinuto(models.Model):
	endere = models.ForeignKey(DataEvento,on_delete=models.CASCADE,verbose_name="Evento")
	data_i = models.DateTimeField("Data Inicial Estimada")
	data_ir = models.DateTimeField("Data Inicial Real",blank=True,null=True)
	author_in = models.ForeignKey(User, on_delete=models.CASCADE,blank=True,null=True, related_name="author_in")
	data_fr = models.DateTimeField("Data Final Real",blank=True,null=True)
	data_fi = models.DateTimeField("Data Final Estimada")
	author_fe = models.ForeignKey(User, on_delete=models.CASCADE,blank=True,null=True, related_name="author_fe")
	TIPOEVENTO = (
		('Operação','Operação'),
		('Eventos','Eventos'),
		('Planejamento','Planejamento'),
	)
	tipo = models.CharField("Tipo da atividade", choices=TIPOEVENTO,max_length=255,blank=True,null=True)
	CRITI_CH = (
		('Baixa','Baixa'),
		('Média','Média'),
		('Alta','Alta'),
		('Muito Alta','Muito Alta'),
	)
	criti = models.CharField("Criticidade",max_length=40, choices=CRITI_CH)
	descr = models.TextField("Descrição")
	infos = models.TextField("Mais informações",blank=True,null=True)
	resp = models.ForeignKey(Orgao,on_delete=models.CASCADE,verbose_name="Responsável")
	contato = models.TextField("Contato",blank=True,null=True)
	arquivo = models.FileField(upload_to='uploads/',verbose_name="Arquivo", blank=True,null=True)	
	class Meta:
		verbose_name = "Minuto Minuto"
		verbose_name_plural = "Minuto Minuto"

	def __str__(self):
		return self.descr

class RotasEventos(models.Model):
	endere = models.ForeignKey(DataEvento,on_delete=models.CASCADE,verbose_name="Evento")
	rotas = models.ForeignKey(Rotas,on_delete=models.CASCADE,verbose_name="Rota")
	ROTAS_CH = (
		('Primária','Primária'),
		('Secundária','Secundária'),
		('Emergência','Emergência'),
	)
	tipo = models.CharField("Tipo da Rota",max_length=40, choices=ROTAS_CH,blank=True,null=True)
	
	class Meta:
		verbose_name = "Rotas - Evento"
		verbose_name_plural = "Rotas - Evento"

	def __str__(self):
		return self.descr

class PoligonoEvento(models.Model):
	endere = models.ForeignKey(DataEvento,on_delete=models.CASCADE,verbose_name="Evento")
	nome = models.CharField("Nome do Local", max_length=250, blank=True,null=True)
	geom = GeometryField(blank=True,null=True)
	data = models.DateTimeField("Data",auto_now=True)

	class Meta:
		verbose_name = "Zona de interesse - Evento"
		verbose_name_plural = "Zona de interesse - Evento"

	def __str__(self):
		return self.nome

	def save(self, *args, **kwargs):
		super(PoligonoEvento, self).save(*args, **kwargs) 


class Atividades(models.Model):
	data_i = models.DateTimeField("Data Inicial Estimada")
	data_ir = models.DateTimeField("Data Inicial Real",blank=True,null=True)
	author_in = models.ForeignKey(User, on_delete=models.CASCADE,blank=True,null=True, related_name="author_in_a")
	data_fr = models.DateTimeField("Data Final Real",blank=True,null=True)
	data_fi = models.DateTimeField("Data Final Estimada")
	author_fe = models.ForeignKey(User, on_delete=models.CASCADE,blank=True,null=True, related_name="author_fe_a")
	TIPOEVENTO = (
		('Operação','Operação'),
		('Eventos','Eventos'),
		('Planejamento','Planejamento'),
		('Passagem de turno','Passagem de turno'),
	)
	tipo = models.CharField("Tipo da atividade", choices=TIPOEVENTO,max_length=255,blank=True,null=True)
	CRITI_CH = (
		('Baixa','Baixa'),
		('Média','Média'),
		('Alta','Alta'),
		('Muito Alta','Muito Alta'),
	)
	criti = models.CharField("Criticidade",max_length=40, choices=CRITI_CH,blank=True,null=True)
	descr = models.TextField("Descrição")
	infos = models.TextField("Mais informações",blank=True,null=True)
	resp = models.ForeignKey(Orgao,on_delete=models.CASCADE,verbose_name="Responsável")
	contato = models.TextField("Contato",blank=True,null=True)
	
	class Meta:
		verbose_name = "Atividade"
		verbose_name_plural = "Atividade"

	def __str__(self):
		return self.descr

class MudancaTurno(models.Model):
	data_inicio = models.DateTimeField("Data da mudança")
	author_in_mt = models.ForeignKey(User, on_delete=models.CASCADE,blank=True,null=True, related_name="author_in_mt")
	CRITI_CH = (
		('Sim','Sim'),
		('Não','Não'),
	)
	criti = models.CharField("Visto?",max_length=40, choices=CRITI_CH,blank=True,null=True)	
	author_fe_mt = models.ForeignKey(User, on_delete=models.CASCADE,blank=True,null=True, related_name="author_fe_mt")

	class Meta:
		verbose_name = "Mudança de turno"
		verbose_name_plural = "Mudança de turno"

	def __str__(self):
		return self.data_inicio.strftime('%d/%m/%Y %H:%M')

	def save(self, *args, **kwargs):
		
		super(MudancaTurno, self).save(*args, **kwargs) 

class AtividadesMudanca(models.Model):
	mudanca = models.ForeignKey(MudancaTurno,on_delete=models.CASCADE,verbose_name="Mudança de turno")
	author_in_mt_at = models.ForeignKey(User, on_delete=models.CASCADE,blank=True,null=True, related_name="author_in_mt_at")
	CRITI_CH = (
		('Baixa','Baixa'),
		('Média','Média'),
		('Alta','Alta'),
		('Muito Alta','Muito Alta'),
	)
	criti = models.CharField("Criticidade",max_length=40, choices=CRITI_CH)
	descr = models.TextField("Descrição")
	infos = models.TextField("Mais informações",blank=True,null=True)
	
	class Meta:
		verbose_name = "Atividade Mudança de turno"
		verbose_name_plural = "Atividade Mudança de turno"

	def __str__(self):
		return self.descr

class CadastroOpera(models.Model):
	endere = models.ForeignKey(DataEvento,on_delete=models.CASCADE,verbose_name="Evento")
	end = models.CharField("Endereço", max_length=250)
	location = PlainLocationField(verbose_name="Coordenadas", based_fields=['end'], zoom=7)
	identificador = models.CharField("Órgão", max_length=250)
	item = models.CharField("Item", max_length=250)
	contato = models.TextField("Contato")

	class Meta:
		verbose_name = "Cadastro Operação"
		verbose_name_plural = "Cadastro Operação"

	def __str__(self):
		return self.identificador+" "+self.item


class KMLEve(models.Model):
	endere = models.ForeignKey(DataEvento,on_delete=models.CASCADE,verbose_name="Evento")
	nome = models.CharField("Nome do arquivo", max_length=250)
	slug = models.SlugField(max_length=100, blank=True,null=True)
	arquivo = models.FileField(upload_to='uploads/',verbose_name="Arquivo", blank=True,null=True)
	contato = models.TextField("Contato")

	class Meta:
		verbose_name = "KML Evento"
		verbose_name_plural = "KML Evento"

	def __str__(self):
		return self.nome

	def save(self, *args, **kwargs):
		self.slug = slugify(self.nome).replace("-","_")
		super(KMLEve, self).save(*args, **kwargs)

class ArquivoDataEvento(models.Model):
	endere = models.ForeignKey(DataEvento,on_delete=models.CASCADE,verbose_name="Evento")
	nome = models.CharField("Nome do arquivo", max_length=250)
	slug = models.SlugField(max_length=100, blank=True,null=True)
	arquivo = models.FileField(upload_to='uploads/',verbose_name="Arquivo", blank=True,null=True)

	class Meta:
		verbose_name = "Arquivos Câmeras"
		verbose_name_plural = "Arquivos Câmeras"

	def __str__(self):
		return self.nome

	def save(self, *args, **kwargs):
		self.slug = slugify(self.nome).replace("-","_")
		super(ArquivoDataEvento, self).save(*args, **kwargs)

class EscolasMunicipais(models.Model):
    x = models.CharField(max_length=20, null=True, blank=True)
    y = models.CharField(max_length=20, null=True, blank=True)
    objectid = models.CharField(max_length=10, null=True, blank=True)
    designacao = models.CharField(max_length=20, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    nome = models.CharField(max_length=255, null=True, blank=True)
    endereco = models.CharField(max_length=255, null=True, blank=True)
    cre = models.CharField(max_length=20, null=True, blank=True)
    cod_atividade = models.CharField(max_length=20, null=True, blank=True)
    telefone = models.CharField(max_length=100, null=True, blank=True)
    link_cartela = models.CharField(max_length=255, null=True, blank=True)
    globalid = models.CharField(max_length=10, null=True, blank=True)
    data_inauguracao = models.CharField(max_length=10, null=True, blank=True)
    nome_abrev = models.CharField(max_length=255, null=True, blank=True)
    cod_microarea = models.CharField(max_length=20, null=True, blank=True)
    

class FeirasCidade(models.Model):
    x = models.CharField(max_length=20, null=True, blank=True)
    y = models.CharField(max_length=20, null=True, blank=True)
    fid = models.CharField(max_length=10, null=True, blank=True)
    codigo = models.CharField(max_length=20, null=True, blank=True)
    descricao = models.CharField(max_length=255, null=True, blank=True)
    dias_da_se = models.CharField(max_length=20, null=True, blank=True)
    latitude = models.CharField(max_length=10, null=True, blank=True)
    longitude = models.CharField(max_length=10, null=True, blank=True)
    tipo = models.CharField(max_length=20, null=True, blank=True)


class AcademiaTerceira(models.Model):
    x = models.CharField(max_length=20, null=True, blank=True)
    y = models.CharField(max_length=20, null=True, blank=True)
    fid = models.CharField(max_length=10, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    local = models.CharField(max_length=255, null=True, blank=True) #referencia #logradouro
    rua = models.CharField(max_length=255, null=True, blank=True) #referencia #logradouro
    numero = models.CharField(max_length=20, null=True, blank=True)
    latitude = models.CharField(max_length=10, null=True, blank=True)
    longitude = models.CharField(max_length=10, null=True, blank=True)


class BensProtegidos(models.Model):
    x = models.CharField(max_length=20, null=True, blank=True)
    y = models.CharField(max_length=20, null=True, blank=True)
    objectid = models.CharField(max_length=10, null=True, blank=True)
    clnp = models.CharField(max_length=20, null=True, blank=True)
    np = models.CharField(max_length=20, null=True, blank=True)
    rua = models.CharField(max_length=255, null=True, blank=True) #referencia #logradouro
    cl = models.CharField(max_length=20, null=True, blank=True)
    complemento = models.CharField(max_length=20, null=True, blank=True)
    area_de_protecao = models.CharField(max_length=50, null=True, blank=True)
    legislacao = models.CharField(max_length=100, null=True, blank=True)
    obrarestauro = models.CharField(max_length=100, null=True, blank=True)
    anorestauro = models.CharField(max_length=10, null=True, blank=True)
    proapac = models.CharField(max_length=20, null=True, blank=True)
    edicaopropac = models.CharField(max_length=100, null=True, blank=True)
    inestproapac = models.CharField(max_length=100, null=True, blank=True)
    arqueologia = models.CharField(max_length=20, null=True, blank=True)
    anoarqueologia = models.CharField(max_length=20, null=True, blank=True)
    grau_de_pr = models.CharField(max_length=20, null=True, blank=True)


class UnidadeSaneamento(models.Model):
    x = models.CharField(max_length=20, null=True, blank=True)
    y = models.CharField(max_length=20, null=True, blank=True)
    objectid = models.CharField(max_length=10, null=True, blank=True)
    bairro = models.CharField(max_length=100, null=True, blank=True)
    cnes = models.CharField(max_length=20, null=True, blank=True)
    cnes_2 = models.CharField(max_length=20, null=True, blank=True)
    nome = models.CharField(max_length=255, null=True, blank=True)
    endereco = models.CharField(max_length=255, null=True, blank=True)
    cap = models.CharField(max_length=20, null=True, blank=True)
    equipes = models.CharField(max_length=100, null=True, blank=True)
    telefone = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)
    globalid = models.CharField(max_length=10, null=True, blank=True)
    horario_semana = models.CharField(max_length=20, null=True, blank=True)
    data_inauguracao = models.CharField(max_length=10, null=True, blank=True)
    horario_sabado = models.CharField(max_length=20, null=True, blank=True)
    tipo_abc = models.CharField(max_length=10, null=True, blank=True)
    tipo_unidade = models.CharField(max_length=20, null=True, blank=True)
    flg_ativo = models.CharField(max_length=20, null=True, blank=True)

class PontoInd(models.Model):
	usuario = models.ForeignKey(PontoRelatorio,on_delete=models.CASCADE)
	pontos = models.ForeignKey(Pontos_de_Apoio,on_delete=models.CASCADE)
	lat = models.CharField("E-mail", max_length=250, blank=True,null=True)
	lon = models.CharField("Local", max_length=250, blank=True,null=True)
	data = models.CharField("Data", max_length=250, blank=True,null=True)

	class Meta:
		verbose_name = "Ponto"
		verbose_name_plural = "Ponto"

	def __str__(self):
		return self.usuario

class OnibusC(models.Model):
	endere = models.ForeignKey(DataEvento,on_delete=models.CASCADE,verbose_name="Evento",blank=True,null=True)
	empresa = models.CharField("Empresa", max_length=250)
	qt = models.CharField("Quantidade de Passageiros", max_length=250)
	uf = models.CharField("UF de origem", max_length=2)

	class Meta:
		verbose_name = "ANTT"
		verbose_name_plural = "ANTT"

	def __str__(self):
		return self.empresa

	def save(self, *args, **kwargs):
		super(OnibusC, self).save(*args, **kwargs)


class PontoPosto(models.Model):
	endere = models.ForeignKey(DataEvento,on_delete=models.CASCADE,verbose_name="Evento",blank=True,null=True)
	local = models.CharField("Nome", max_length=250)
	GER_CHOICE = (
		('Zona Norte', 'Zona Norte'),
		('Zona Oeste', 'Zona Oeste'),
		('Centro', 'Centro'),
		('Zona Sul', 'Zona Sul'),
	)
	zona = models.CharField("Zona da Cidade",max_length=20,choices=GER_CHOICE,blank=True,null=True)
	AP_CHOICE = (
		('AP 1', 'AP 1'),
		('AP 2', 'AP 2'),
		('AP 3', 'AP 3'),
		('AP 4', 'AP 4'),
		('AP 5', 'AP 5'),
	)
	ap = models.CharField("AP",max_length=20,choices=AP_CHOICE,blank=True,null=True)
	SUBS_CHOICE = (
		('Barra da Tijuca', 'Barra da Tijuca'),
		('Centro e Centro Histórico', 'Centro e Centro Histórico'),
		('Grande Bangu', 'Grande Bangu'),
		('Ilhas', 'Ilhas'),
		('Jacarepaguá', 'Jacarepaguá'),
		('Tijuca', 'Tijuca'),
		('Zona Norte', 'Zona Norte'),
		('Zona Oeste', 'Zona Oeste'),
		('Zona Sul', 'Zona Sul'),
	)
	subs = models.CharField("SubPrefeitura",max_length=100,choices=SUBS_CHOICE,blank=True,null=True)
	BAIRRO_CHOICE = (
		('Abolição','Abolição'),
		('Acari','Acari'),
		('Água Santa','Água Santa'),
		('Alto da Boa Vista','Alto da Boa Vista'),
		('Anchieta','Anchieta'),
		('Andaraí','Andaraí'),
		('Anil','Anil'),
		('Bancários','Bancários'),
		('Bangu','Bangu'),
		('Barra da Tijuca','Barra da Tijuca'),
		('Barra de Guaratiba','Barra de Guaratiba'),
		('Barros Filho','Barros Filho'),
		('Benfica','Benfica'),
		('Bento Ribeiro','Bento Ribeiro'),
		('Bonsucesso','Bonsucesso'),
		('Botafogo','Botafogo'),
		('Brás de Pina','Brás de Pina'),
		('Cachambi','Cachambi'),
		('Cacuia','Cacuia'),
		('Caju','Caju'),
		('Camorim','Camorim'),
		('Campinho','Campinho'),
		('Campo dos Afonsos','Campo dos Afonsos'),
		('Campo Grande','Campo Grande'),
		('Cascadura','Cascadura'),
		('Catete','Catete'),
		('Catumbi','Catumbi'),
		('Cavalcanti','Cavalcanti'),
		('Centro','Centro'),
		('Cidade de Deus','Cidade de Deus'),
		('Cidade Nova','Cidade Nova'),
		('Cidade Universitária','Cidade Universitária'),
		('Cocotá','Cocotá'),
		('Coelho Neto','Coelho Neto'),
		('Colégio','Colégio'),
		('Complexo do Alemão','Complexo do Alemão'),
		('Copacabana','Copacabana'),
		('Cordovil','Cordovil'),
		('Cosme Velho','Cosme Velho'),
		('Cosmos','Cosmos'),
		('Costa Barros','Costa Barros'),
		('Curicica','Curicica'),
		('Del Castilho','Del Castilho'),
		('Deodoro','Deodoro'),
		('Encantado','Encantado'),
		('Engenheiro Leal','Engenheiro Leal'),
		('Engenho da Rainha','Engenho da Rainha'),
		('Engenho de Dentro','Engenho de Dentro'),
		('Engenho Novo','Engenho Novo'),
		('Estácio','Estácio'),
		('Flamengo','Flamengo'),
		('Freguesia (Ilha do Governador)','Freguesia (Ilha do Governador)'),
		('Freguesia (Jacarepaguá)','Freguesia (Jacarepaguá)'),
		('Galeão','Galeão'),
		('Gamboa','Gamboa'),
		('Gardênia Azul','Gardênia Azul'),
		('Gávea','Gávea'),
		('Gericinó','Gericinó'),
		('Glória','Glória'),
		('Grajaú','Grajaú'),
		('Grumari','Grumari'),
		('Guadalupe','Guadalupe'),
		('Guaratiba','Guaratiba'),
		('Higienópolis','Higienópolis'),
		('Honório Gurgel','Honório Gurgel'),
		('Humaitá','Humaitá'),
		('Inhaúma','Inhaúma'),
		('Inhoaíba','Inhoaíba'),
		('Ipanema','Ipanema'),
		('Irajá','Irajá'),
		('Itanhangá','Itanhangá'),
		('Jacaré','Jacaré'),
		('Jacarepaguá','Jacarepaguá'),
		('Jacarezinho','Jacarezinho'),
		('Jardim América','Jardim América'),
		('Jardim Botânico','Jardim Botânico'),
		('Jardim Carioca','Jardim Carioca'),
		('Jardim Guanabara','Jardim Guanabara'),
		('Jardim Sulacap','Jardim Sulacap'),
		('Joá','Joá'),
		('Lagoa','Lagoa'),
		('Lapa','Lapa'),
		('Laranjeiras','Laranjeiras'),
		('Leblon','Leblon'),
		('Leme','Leme'),
		('Lins de Vasconcelos','Lins de Vasconcelos'),
		('Madureira','Madureira'),
		('Magalhães Bastos','Magalhães Bastos'),
		('Mangueira','Mangueira'),
		('Manguinhos','Manguinhos'),
		('Maracanã','Maracanã'),
		('Maré','Maré'),
		('Marechal Hermes','Marechal Hermes'),
		('Maria da Graça','Maria da Graça'),
		('Méier','Méier'),
		('Moneró','Moneró'),
		('Olaria','Olaria'),
		('Oswaldo Cruz','Oswaldo Cruz'),
		('Paciência','Paciência'),
		('Padre Miguel','Padre Miguel'),
		('Paquetá','Paquetá'),
		('Parada de Lucas','Parada de Lucas'),
		('Parque Anchieta','Parque Anchieta'),
		('Parque Columbia','Parque Columbia'),
		('Pavuna','Pavuna'),
		('Pechincha','Pechincha'),
		('Pedra de Guaratiba','Pedra de Guaratiba'),
		('Penha','Penha'),
		('Penha Circular','Penha Circular'),
		('Piedade','Piedade'),
		('Pilares','Pilares'),
		('Pitangueiras','Pitangueiras'),
		('Portuguesa','Portuguesa'),
		('Praça da Bandeira','Praça da Bandeira'),
		('Praça Seca','Praça Seca'),
		('Praia da Bandeira','Praia da Bandeira'),
		('Quintino Bocaiúva','Quintino Bocaiúva'),
		('Ramos','Ramos'),
		('Realengo','Realengo'),
		('Recreio dos Bandeirantes','Recreio dos Bandeirantes'),
		('Riachuelo','Riachuelo'),
		('Ribeira','Ribeira'),
		('Ricardo de Albuquerque','Ricardo de Albuquerque'),
		('Rio Comprido','Rio Comprido'),
		('Rocha','Rocha'),
		('Rocha Miranda','Rocha Miranda'),
		('Rocinha','Rocinha'),
		('Sampaio','Sampaio'),
		('Santa Cruz','Santa Cruz'),
		('Santa Teresa','Santa Teresa'),
		('Santíssimo','Santíssimo'),
		('Santo Cristo','Santo Cristo'),
		('São Conrado','São Conrado'),
		('São Cristóvão','São Cristóvão'),
		('São Francisco Xavier','São Francisco Xavier'),
		('Saúde','Saúde'),
		('Senador Camará','Senador Camará'),
		('Senador Vasconcelos','Senador Vasconcelos'),
		('Sepetiba','Sepetiba'),
		('Tanque','Tanque'),
		('Taquara','Taquara'),
		('Tauá','Tauá'),
		('Tijuca','Tijuca'),
		('Todos os Santos','Todos os Santos'),
		('Tomás Coelho','Tomás Coelho'),
		('Turiaçu','Turiaçu'),
		('Urca','Urca'),
		('Vargem Grande','Vargem Grande'),
		('Vargem Pequena','Vargem Pequena'),
		('Vasco da Gama','Vasco da Gama'),
		('Vaz Lobo','Vaz Lobo'),
		('Vicente de Carvalho','Vicente de Carvalho'),
		('Vidigal','Vidigal'),
		('Vigário Geral','Vigário Geral'),
		('Vila Cosmos','Vila Cosmos'),
		('Vila da Penha','Vila da Penha'),
		('Vila Isabel','Vila Isabel'),
		('Vila Militar','Vila Militar'),
		('Vila Valqueire','Vila Valqueire'),
		('Vista Alegre','Vista Alegre'),
		('Zumbi','Zumbi'),	
	)
	bairro = models.CharField("Bairro",max_length=30,choices=BAIRRO_CHOICE,blank=True,null=True)
	end = models.CharField("Endereço", max_length=250)
	location = PlainLocationField(verbose_name="Coordenadas", based_fields=['end'], zoom=7)
	orgao = models.CharField("Órgão responsável", max_length=250)
	atendimentos = models.CharField("Atendimentos", max_length=250)
	remocoes = models.CharField("Remoções", max_length=250)

	class Meta:
		verbose_name = "Posto de Saúde"
		verbose_name_plural = "Posto de Saúde"

	def __str__(self):
		return self.local

	def save(self, *args, **kwargs):
		import shapefile
		from shapely.geometry import LineString, Point, Polygon
		shape = shapefile.Reader("/home/cocr.servicos/app_cor/Aps/ApsN.shp")
		point = Point(float(self.location.split(",")[1]),float(self.location.split(",")[0]))
		cod = ""
		y = 0
		while y != len(shape.shapeRecords()):
			feature = shape.shapeRecords()[y]
			first = feature.shape.__geo_interface__  
			lista = first['coordinates'][0][0]
			poly2 = Polygon([i for i in lista])
			if (poly2.contains(point)) == True:
				cod = (feature.record['codap'])
				break
			y += 1
		self.ap = "AP "+cod
		super(PontoPosto, self).save(*args, **kwargs)

class PontoTuris(models.Model):
	local = models.CharField("Nome", max_length=250)
	GER_CHOICE = (
		('Zona Norte', 'Zona Norte'),
		('Zona Oeste', 'Zona Oeste'),
		('Centro', 'Centro'),
		('Zona Sul', 'Zona Sul'),
	)
	zona = models.CharField("Zona da Cidade",max_length=20,choices=GER_CHOICE,blank=True,null=True)
	AP_CHOICE = (
		('AP 1', 'AP 1'),
		('AP 2', 'AP 2'),
		('AP 3', 'AP 3'),
		('AP 4', 'AP 4'),
		('AP 5', 'AP 5'),
	)
	ap = models.CharField("AP",max_length=20,choices=AP_CHOICE,blank=True,null=True)
	SUBS_CHOICE = (
		('Barra da Tijuca', 'Barra da Tijuca'),
		('Centro e Centro Histórico', 'Centro e Centro Histórico'),
		('Grande Bangu', 'Grande Bangu'),
		('Ilhas', 'Ilhas'),
		('Jacarepaguá', 'Jacarepaguá'),
		('Tijuca', 'Tijuca'),
		('Zona Norte', 'Zona Norte'),
		('Zona Oeste', 'Zona Oeste'),
		('Zona Sul', 'Zona Sul'),
	)
	subs = models.CharField("SubPrefeitura",max_length=100,choices=SUBS_CHOICE,blank=True,null=True)
	BAIRRO_CHOICE = (
		('Abolição','Abolição'),
		('Acari','Acari'),
		('Água Santa','Água Santa'),
		('Alto da Boa Vista','Alto da Boa Vista'),
		('Anchieta','Anchieta'),
		('Andaraí','Andaraí'),
		('Anil','Anil'),
		('Bancários','Bancários'),
		('Bangu','Bangu'),
		('Barra da Tijuca','Barra da Tijuca'),
		('Barra de Guaratiba','Barra de Guaratiba'),
		('Barros Filho','Barros Filho'),
		('Benfica','Benfica'),
		('Bento Ribeiro','Bento Ribeiro'),
		('Bonsucesso','Bonsucesso'),
		('Botafogo','Botafogo'),
		('Brás de Pina','Brás de Pina'),
		('Cachambi','Cachambi'),
		('Cacuia','Cacuia'),
		('Caju','Caju'),
		('Camorim','Camorim'),
		('Campinho','Campinho'),
		('Campo dos Afonsos','Campo dos Afonsos'),
		('Campo Grande','Campo Grande'),
		('Cascadura','Cascadura'),
		('Catete','Catete'),
		('Catumbi','Catumbi'),
		('Cavalcanti','Cavalcanti'),
		('Centro','Centro'),
		('Cidade de Deus','Cidade de Deus'),
		('Cidade Nova','Cidade Nova'),
		('Cidade Universitária','Cidade Universitária'),
		('Cocotá','Cocotá'),
		('Coelho Neto','Coelho Neto'),
		('Colégio','Colégio'),
		('Complexo do Alemão','Complexo do Alemão'),
		('Copacabana','Copacabana'),
		('Cordovil','Cordovil'),
		('Cosme Velho','Cosme Velho'),
		('Cosmos','Cosmos'),
		('Costa Barros','Costa Barros'),
		('Curicica','Curicica'),
		('Del Castilho','Del Castilho'),
		('Deodoro','Deodoro'),
		('Encantado','Encantado'),
		('Engenheiro Leal','Engenheiro Leal'),
		('Engenho da Rainha','Engenho da Rainha'),
		('Engenho de Dentro','Engenho de Dentro'),
		('Engenho Novo','Engenho Novo'),
		('Estácio','Estácio'),
		('Flamengo','Flamengo'),
		('Freguesia (Ilha do Governador)','Freguesia (Ilha do Governador)'),
		('Freguesia (Jacarepaguá)','Freguesia (Jacarepaguá)'),
		('Galeão','Galeão'),
		('Gamboa','Gamboa'),
		('Gardênia Azul','Gardênia Azul'),
		('Gávea','Gávea'),
		('Gericinó','Gericinó'),
		('Glória','Glória'),
		('Grajaú','Grajaú'),
		('Grumari','Grumari'),
		('Guadalupe','Guadalupe'),
		('Guaratiba','Guaratiba'),
		('Higienópolis','Higienópolis'),
		('Honório Gurgel','Honório Gurgel'),
		('Humaitá','Humaitá'),
		('Inhaúma','Inhaúma'),
		('Inhoaíba','Inhoaíba'),
		('Ipanema','Ipanema'),
		('Irajá','Irajá'),
		('Itanhangá','Itanhangá'),
		('Jacaré','Jacaré'),
		('Jacarepaguá','Jacarepaguá'),
		('Jacarezinho','Jacarezinho'),
		('Jardim América','Jardim América'),
		('Jardim Botânico','Jardim Botânico'),
		('Jardim Carioca','Jardim Carioca'),
		('Jardim Guanabara','Jardim Guanabara'),
		('Jardim Sulacap','Jardim Sulacap'),
		('Joá','Joá'),
		('Lagoa','Lagoa'),
		('Lapa','Lapa'),
		('Laranjeiras','Laranjeiras'),
		('Leblon','Leblon'),
		('Leme','Leme'),
		('Lins de Vasconcelos','Lins de Vasconcelos'),
		('Madureira','Madureira'),
		('Magalhães Bastos','Magalhães Bastos'),
		('Mangueira','Mangueira'),
		('Manguinhos','Manguinhos'),
		('Maracanã','Maracanã'),
		('Maré','Maré'),
		('Marechal Hermes','Marechal Hermes'),
		('Maria da Graça','Maria da Graça'),
		('Méier','Méier'),
		('Moneró','Moneró'),
		('Olaria','Olaria'),
		('Oswaldo Cruz','Oswaldo Cruz'),
		('Paciência','Paciência'),
		('Padre Miguel','Padre Miguel'),
		('Paquetá','Paquetá'),
		('Parada de Lucas','Parada de Lucas'),
		('Parque Anchieta','Parque Anchieta'),
		('Parque Columbia','Parque Columbia'),
		('Pavuna','Pavuna'),
		('Pechincha','Pechincha'),
		('Pedra de Guaratiba','Pedra de Guaratiba'),
		('Penha','Penha'),
		('Penha Circular','Penha Circular'),
		('Piedade','Piedade'),
		('Pilares','Pilares'),
		('Pitangueiras','Pitangueiras'),
		('Portuguesa','Portuguesa'),
		('Praça da Bandeira','Praça da Bandeira'),
		('Praça Seca','Praça Seca'),
		('Praia da Bandeira','Praia da Bandeira'),
		('Quintino Bocaiúva','Quintino Bocaiúva'),
		('Ramos','Ramos'),
		('Realengo','Realengo'),
		('Recreio dos Bandeirantes','Recreio dos Bandeirantes'),
		('Riachuelo','Riachuelo'),
		('Ribeira','Ribeira'),
		('Ricardo de Albuquerque','Ricardo de Albuquerque'),
		('Rio Comprido','Rio Comprido'),
		('Rocha','Rocha'),
		('Rocha Miranda','Rocha Miranda'),
		('Rocinha','Rocinha'),
		('Sampaio','Sampaio'),
		('Santa Cruz','Santa Cruz'),
		('Santa Teresa','Santa Teresa'),
		('Santíssimo','Santíssimo'),
		('Santo Cristo','Santo Cristo'),
		('São Conrado','São Conrado'),
		('São Cristóvão','São Cristóvão'),
		('São Francisco Xavier','São Francisco Xavier'),
		('Saúde','Saúde'),
		('Senador Camará','Senador Camará'),
		('Senador Vasconcelos','Senador Vasconcelos'),
		('Sepetiba','Sepetiba'),
		('Tanque','Tanque'),
		('Taquara','Taquara'),
		('Tauá','Tauá'),
		('Tijuca','Tijuca'),
		('Todos os Santos','Todos os Santos'),
		('Tomás Coelho','Tomás Coelho'),
		('Turiaçu','Turiaçu'),
		('Urca','Urca'),
		('Vargem Grande','Vargem Grande'),
		('Vargem Pequena','Vargem Pequena'),
		('Vasco da Gama','Vasco da Gama'),
		('Vaz Lobo','Vaz Lobo'),
		('Vicente de Carvalho','Vicente de Carvalho'),
		('Vidigal','Vidigal'),
		('Vigário Geral','Vigário Geral'),
		('Vila Cosmos','Vila Cosmos'),
		('Vila da Penha','Vila da Penha'),
		('Vila Isabel','Vila Isabel'),
		('Vila Militar','Vila Militar'),
		('Vila Valqueire','Vila Valqueire'),
		('Vista Alegre','Vista Alegre'),
		('Zumbi','Zumbi'),	
	)
	bairro = models.CharField("Bairro",max_length=30,choices=BAIRRO_CHOICE,blank=True,null=True)
	end = models.CharField("Endereço", max_length=250)
	location = PlainLocationField(verbose_name="Coordenadas", based_fields=['end'], zoom=7)
	historia = models.TextField("Texto")
	servico = models.TextField("Serviço")

	class Meta:
		verbose_name = "Ponto Turistico"
		verbose_name_plural = "Ponto Turistico"

	def __str__(self):
		return self.local

	def save(self, *args, **kwargs):
		import shapefile
		from shapely.geometry import LineString, Point, Polygon
		shape = shapefile.Reader("/home/cocr.servicos/app_cor/Aps/ApsN.shp")
		point = Point(float(self.location.split(",")[1]),float(self.location.split(",")[0]))
		cod = ""
		y = 0
		while y != len(shape.shapeRecords()):
			feature = shape.shapeRecords()[y]
			first = feature.shape.__geo_interface__  
			lista = first['coordinates'][0][0]
			poly2 = Polygon([i for i in lista])
			if (poly2.contains(point)) == True:
				cod = (feature.record['codap'])
				break
			y += 1
		self.ap = "AP "+cod
		super(PontoTuris, self).save(*args, **kwargs)

class PontoCarnaval(models.Model):
	local = models.CharField("Nome", max_length=250)
	end = models.CharField("Endereço", max_length=250)
	location = PlainLocationField(verbose_name="Coordenadas", based_fields=['end'], zoom=7)

	class Meta:
		verbose_name = "Ponto Carnaval"
		verbose_name_plural = "Ponto Carnaval"

	def __str__(self):
		return self.local

	def save(self, *args, **kwargs):
		super(PontoCarnaval, self).save(*args, **kwargs)

class DesfileCarnaval(models.Model):
	escola = models.CharField("Nome da escola", max_length=250)
	enredo = models.CharField("Enredo", max_length=250)
	link = models.CharField("Link Youtube", max_length=250)
	data_inicio = models.DateTimeField("Início do Evento")
	data_fim = models.DateTimeField("Final do evento")
	
	class Meta:
		verbose_name = "Ordem dos desfiles - Carnaval 2024"
		verbose_name_plural = "Ordem dos desfiles - Carnaval 2024"

	def __str__(self):
		return self.escola+" "+self.enredo

class Operacao(models.Model):
	nome_evento = models.CharField("Nome da operação",max_length=255,blank=True,null=True)
	tipo = models.CharField("Tipo",max_length=255,blank=True,null=True)
	endere = models.ForeignKey(Local,on_delete=models.CASCADE,verbose_name="Local da operação")
	data_inicio = models.DateTimeField("Início da operação")
	data_fim = models.DateTimeField("Final da operação")
	
	class Meta:
		verbose_name = "Operação"
		verbose_name_plural = "Operação"

	def __str__(self):
		return self.nome_evento+" "+self.data_inicio.strftime('%d/%m/%Y %H:%M')

	def save(self, *args, **kwargs):
		
		super(Operacao, self).save(*args, **kwargs) 

class MinutoMinutoOperacao(models.Model):
	endere = models.ForeignKey(Operacao,on_delete=models.CASCADE,verbose_name="Operação")
	data_i = models.DateTimeField("Data Inicial Estimada")
	data_ir = models.DateTimeField("Data Inicial Real",blank=True,null=True)
	endere_ini = models.ForeignKey(Local,on_delete=models.CASCADE,verbose_name="Local da inicio", related_name="endere_ini",blank=True,null=True)
	author_in = models.ForeignKey(User, on_delete=models.CASCADE,blank=True,null=True, related_name="author_in_mm")
	data_fi = models.DateTimeField("Data Final Estimada")
	data_fr = models.DateTimeField("Data Final Real",blank=True,null=True)
	endere_fim = models.ForeignKey(Local,on_delete=models.CASCADE,verbose_name="Local de fim", related_name="endere_fim",blank=True,null=True)
	author_fe = models.ForeignKey(User, on_delete=models.CASCADE,blank=True,null=True, related_name="author_fe_mm")
	TIPOEVENTO = (
		('Operação','Operação'),
		('Eventos','Eventos'),
		('Planejamento','Planejamento'),
	)
	tipo = models.CharField("Tipo da atividade", choices=TIPOEVENTO,max_length=255,blank=True,null=True)
	CRITI_CH = (
		('Baixa','Baixa'),
		('Média','Média'),
		('Alta','Alta'),
		('Muito Alta','Muito Alta'),
	)
	criti = models.CharField("Criticidade",max_length=40, choices=CRITI_CH)
	ROTAS_CH = (
		('Primária','Primária'),
		('Secundária','Secundária'),
		('Emergência','Emergência'),
	)
	rotas = models.CharField("Rota",max_length=40, choices=ROTAS_CH,blank=True,null=True)
	voo = models.CharField("Voo",max_length=200,blank=True,null=True)
	icao = models.CharField("ICAO",max_length=200,blank=True,null=True)
	master = models.CharField("Autoridade Máxima",max_length=40, choices=(('Sim','Sim'),('Não','Não'),))
	pais = models.CharField("País",max_length=200,blank=True,null=True)
	numero_prf = models.CharField("ID PRF",max_length=200,blank=True,null=True)
	descr = models.TextField("Descrição")
	infos = models.TextField("Observações",blank=True,null=True)
	resp = models.ForeignKey(Orgao,on_delete=models.CASCADE,verbose_name="Responsável")
	contato = models.TextField("Contato",blank=True,null=True)
	rota_as = models.ForeignKey(RotaTag,on_delete=models.CASCADE,verbose_name="Rotas",blank=True,null=True)
	
	class Meta:
		verbose_name = "Minuto Minuto Operação"
		verbose_name_plural = "Minuto Minuto Operação"

	def __str__(self):
		return self.descr

class KMLOperacao(models.Model):
	endere = models.ForeignKey(Operacao,on_delete=models.CASCADE,verbose_name="Evento")
	nome = models.CharField("Nome do arquivo", max_length=250)
	slug = models.SlugField(max_length=100, blank=True,null=True)
	arquivo = models.FileField(upload_to='uploads/',verbose_name="Arquivo", blank=True,null=True)

	class Meta:
		verbose_name = "KML Operação"
		verbose_name_plural = "KML Operação"

	def __str__(self):
		return self.nome

	def save(self, *args, **kwargs):
		self.slug = slugify(self.nome).replace("-","_")
		super(KMLEve, self).save(*args, **kwargs)

class CamerasVAG20(models.Model):
	estacao = models.ForeignKey(Cameras,on_delete=models.CASCADE)
	local = models.ForeignKey(Local,on_delete=models.CASCADE)


	class Meta:
		verbose_name = "Cameras Video Analitico G20"
		verbose_name_plural = "Cameras Video Analitico G20"


	def __str__(self):
		return self.estacao.nome

class DadosCameraVAG20(models.Model):
	estacaonovo = models.ForeignKey(CamerasVAG20,on_delete=models.CASCADE)
	data = models.DateTimeField(auto_now=False, blank=True,null=True)
	qt = models.CharField("Temperatura", max_length=250)
	dado = models.CharField("Temperatura", max_length=250)
	dia = models.CharField("Nivel", max_length=250)
	hora = models.IntegerField("Nivel")
	minuto = models.IntegerField("Nivel")
	hm = models.CharField("Nivel", max_length=250)

	class Meta:
		verbose_name = "Dados Câmera VA"
		verbose_name_plural = "Dados Câmera VA"

	def __str__(self):
		return self.situ


class Pessoa(models.Model):
        nome = models.CharField("Nome",max_length=255)
        nascimento = models.DateField("Data de nascimento", blank=True,null=True)
        cpf_cnpj = models.CharField("CPF",max_length=16, unique=True)
        matricula = models.CharField("Matricula",max_length=20, blank=True,null=True)
        rg = models.CharField("RG",max_length=12, unique=True, blank=True,null=True)
        telefone = models.CharField("Telefone",max_length=12, unique=True, blank=True,null=True)
        resp = models.ForeignKey(Orgao,on_delete=models.CASCADE,verbose_name="Responsável")
        email = models.EmailField("E-mail",max_length=254, unique=True)
        foto = models.FileField(upload_to='uploads/',verbose_name="Foto", blank=True,null=True)
        APTOS = (
                ('Sim', 'Sim'),
                ('Não', 'Não'),
        )
        apto = models.CharField("Apto para usar?",max_length=3,choices=APTOS,blank=True,null=True)
        author = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,blank=True,null=True)

        class Meta:
                verbose_name = "Cadastros"
                verbose_name_plural = "Cadastros"


        def __str__(self):
                return self.email

class LocalizacaoP(models.Model):
        usuario = models.ForeignKey(Pessoa,on_delete=models.CASCADE)
        lat = models.CharField("E-mail", max_length=250, blank=True,null=True)
        lon = models.CharField("Local", max_length=250, blank=True,null=True)
        data = models.CharField("Data", max_length=250, blank=True,null=True)
        vel = models.CharField("Local", max_length=250, blank=True,null=True)

        class Meta:
                verbose_name = "Localizacao Usuário"
                verbose_name_plural = "Localizacao Usuário"

        def __str__(self):
                return self.usuario

class ConfirmacaoEstagio(models.Model):
        estagio = models.ForeignKey(Estagio,on_delete=models.CASCADE)
        pessoa = models.ForeignKey(Pessoa,on_delete=models.CASCADE)
        STATUS = (
                ('Sim', 'Sim'),
                ('Não', 'Não'),
        )
        alive = models.CharField("A disposição?",max_length=30,choices=STATUS, blank=True,null=True)
        lat = models.CharField("Latitude",max_length=100,blank=True,null=True)
        lon = models.CharField("Longitude",max_length=100,blank=True,null=True)

        class Meta:
                verbose_name = "Confirmação de disponibilidade"
                verbose_name_plural = "Confirmação de disponibilidade"

        def __str__(self):
                return self.alive

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Chat {self.session_id}"

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'Usuário'),
        ('assistant', 'Assistente'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    query_data = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']


# ============================================
# SISTEMA DE USUÁRIOS E PERMISSÕES - INTEGRACITY
# ============================================
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """Perfil estendido do usuário do INTEGRACITY"""

    ROLES = [
        ('superadmin', 'Super Administrador'),
        ('admin', 'Administrador'),
        ('operator_senior', 'Operador Senior'),
        ('operator', 'Operador'),
        ('viewer', 'Visualizador'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField('Perfil', max_length=20, choices=ROLES, default='viewer')
    phone = models.CharField('Telefone', max_length=20, blank=True, null=True)
    department = models.CharField('Departamento', max_length=100, blank=True, null=True)
    cargo = models.CharField('Cargo', max_length=100, blank=True, null=True)
    avatar = models.ImageField('Avatar', upload_to='avatars/', blank=True, null=True)

    # Segurança
    failed_login_attempts = models.IntegerField('Tentativas falhas', default=0)
    locked_until = models.DateTimeField('Bloqueado até', blank=True, null=True)
    must_change_password = models.BooleanField('Deve trocar senha', default=False)
    password_changed_at = models.DateTimeField('Última troca de senha', auto_now_add=True)

    # Auditoria
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='users_created', verbose_name='Criado por'
    )
    last_login_ip = models.GenericIPAddressField('Último IP', blank=True, null=True)

    # Observações
    notes = models.TextField('Observações', blank=True)

    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'Perfil de Usuário'
        verbose_name_plural = 'Perfis de Usuários'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    def is_locked(self):
        """Verifica se conta está bloqueada"""
        from django.utils import timezone
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def lock_account(self, minutes=30):
        """Bloqueia a conta por X minutos"""
        from django.utils import timezone
        from datetime import timedelta
        self.locked_until = timezone.now() + timedelta(minutes=minutes)
        self.save(update_fields=['locked_until'])

    def unlock_account(self):
        """Desbloqueia a conta"""
        self.locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['locked_until', 'failed_login_attempts'])

    def increment_failed_attempts(self):
        """Incrementa tentativas falhas e bloqueia se necessário"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.lock_account(30)
        self.save(update_fields=['failed_login_attempts'])

    def reset_failed_attempts(self):
        """Reseta tentativas falhas após login bem sucedido"""
        self.failed_login_attempts = 0
        self.save(update_fields=['failed_login_attempts'])

    def is_admin(self):
        """Verifica se é admin ou superadmin"""
        return self.role in ['admin', 'superadmin']

    def is_superadmin(self):
        """Verifica se é superadmin"""
        return self.role == 'superadmin'

    def can_manage_users(self):
        """Verifica se pode gerenciar usuários"""
        return self.role in ['admin', 'superadmin']

    def can_view_audit(self):
        """Verifica se pode ver logs de auditoria"""
        return self.role in ['admin', 'superadmin']

    def has_permission(self, resource, action):
        """Verifica se usuário tem permissão específica"""
        # Superadmin tem todas as permissões
        if self.role == 'superadmin':
            return True

        # Verificar permissões baseadas no role
        role_permissions = ROLE_DEFAULT_PERMISSIONS.get(self.role, {})
        if resource in role_permissions:
            if action in role_permissions[resource]:
                return True

        # Verificar permissões customizadas
        return UserPermission.objects.filter(
            user=self.user,
            resource=resource,
            action=action
        ).exists()


# Permissões padrão por role
ROLE_DEFAULT_PERMISSIONS = {
    'superadmin': {
        'users': ['view', 'add', 'edit', 'delete'],
        'cameras': ['view_all', 'view_assigned', 'control'],
        'mosaic': ['view', 'create', 'edit'],
        'map': ['view', 'edit_layers', 'add_markers'],
        'reports': ['view', 'export', 'generate'],
        'audit': ['view_own', 'view_all'],
        'settings': ['view', 'edit'],
    },
    'admin': {
        'users': ['view', 'add', 'edit'],
        'cameras': ['view_all', 'view_assigned', 'control'],
        'mosaic': ['view', 'create', 'edit'],
        'map': ['view', 'edit_layers', 'add_markers'],
        'reports': ['view', 'export', 'generate'],
        'audit': ['view_all'],
        'settings': ['view'],
    },
    'operator_senior': {
        'cameras': ['view_all', 'view_assigned'],
        'mosaic': ['view', 'create', 'edit'],
        'map': ['view', 'add_markers'],
        'reports': ['view', 'export'],
        'audit': ['view_own'],
    },
    'operator': {
        'cameras': ['view_assigned'],
        'mosaic': ['view'],
        'map': ['view'],
        'reports': ['view'],
    },
    'viewer': {
        'cameras': ['view_assigned'],
        'map': ['view'],
    },
}


class UserPermission(models.Model):
    """Permissões granulares customizadas de usuário"""

    RESOURCES = [
        ('users', 'Usuários'),
        ('cameras', 'Câmeras'),
        ('mosaic', 'Mosaico'),
        ('map', 'Mapa'),
        ('reports', 'Relatórios'),
        ('audit', 'Auditoria'),
        ('settings', 'Configurações'),
    ]

    ACTIONS = [
        ('view', 'Visualizar'),
        ('view_all', 'Visualizar Todos'),
        ('view_assigned', 'Visualizar Atribuídos'),
        ('add', 'Adicionar'),
        ('edit', 'Editar'),
        ('delete', 'Excluir'),
        ('control', 'Controlar'),
        ('create', 'Criar'),
        ('edit_layers', 'Editar Camadas'),
        ('add_markers', 'Adicionar Marcadores'),
        ('export', 'Exportar'),
        ('generate', 'Gerar'),
        ('view_own', 'Ver Próprios'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_permissions')
    resource = models.CharField('Recurso', max_length=50, choices=RESOURCES)
    action = models.CharField('Ação', max_length=50, choices=ACTIONS)
    scope = models.JSONField('Escopo', default=dict, blank=True)

    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='permissions_granted', verbose_name='Criado por'
    )

    class Meta:
        db_table = 'user_permissions'
        verbose_name = 'Permissão de Usuário'
        verbose_name_plural = 'Permissões de Usuários'
        unique_together = ['user', 'resource', 'action']

    def __str__(self):
        return f"{self.user.username}: {self.resource}.{self.action}"


class AuditLog(models.Model):
    """Log de auditoria de ações do sistema"""

    ACTIONS = [
        ('login', 'Login'),
        ('login_failed', 'Login Falhou'),
        ('logout', 'Logout'),
        ('user_create', 'Criação de Usuário'),
        ('user_edit', 'Edição de Usuário'),
        ('user_delete', 'Exclusão de Usuário'),
        ('user_activate', 'Ativação de Usuário'),
        ('user_deactivate', 'Desativação de Usuário'),
        ('user_unlock', 'Desbloqueio de Usuário'),
        ('permission_grant', 'Concessão de Permissão'),
        ('permission_revoke', 'Revogação de Permissão'),
        ('password_change', 'Alteração de Senha'),
        ('password_reset', 'Reset de Senha'),
        ('settings_change', 'Alteração de Configuração'),
        ('camera_access', 'Acesso a Câmera'),
        ('export_data', 'Exportação de Dados'),
        ('report_generate', 'Geração de Relatório'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='audit_logs', verbose_name='Usuário'
    )
    action = models.CharField('Ação', max_length=50, choices=ACTIONS)
    resource_type = models.CharField('Tipo de Recurso', max_length=100, blank=True)
    resource_id = models.CharField('ID do Recurso', max_length=100, blank=True)
    details = models.JSONField('Detalhes', default=dict)
    ip_address = models.GenericIPAddressField('Endereço IP')
    user_agent = models.TextField('User Agent', blank=True)
    timestamp = models.DateTimeField('Data/Hora', auto_now_add=True)
    success = models.BooleanField('Sucesso', default=True)
    error_message = models.TextField('Mensagem de Erro', blank=True)

    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else 'Anônimo'
        return f"[{self.timestamp}] {user_str}: {self.get_action_display()}"

    @classmethod
    def log(cls, request, action, resource_type='', resource_id='', details=None, success=True, error_message=''):
        """Método helper para criar log de auditoria"""
        user = request.user if request.user.is_authenticated else None

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')

        return cls.objects.create(
            user=user,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else '',
            details=details or {},
            ip_address=ip,
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            success=success,
            error_message=error_message
        )


# Signal para criar UserProfile automaticamente quando User é criado
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Cria UserProfile automaticamente quando User é criado"""
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Salva UserProfile quando User é salvo"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.get_or_create(user=instance)


# ============================================
# SISTEMA DE GERENCIAMENTO DE OCORRÊNCIAS
# ============================================

class CategoriaOcorrencia(models.Model):
    """Categorias de Ocorrências para o sistema de gerenciamento"""

    ICONES = [
        ('fa-car-crash', 'Acidente de Trânsito'),
        ('fa-fire', 'Incêndio'),
        ('fa-tools', 'Infraestrutura'),
        ('fa-water', 'Emergência Ambiental'),
        ('fa-paw', 'Animal'),
        ('fa-exclamation-triangle', 'Evento Especial'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    icone = models.CharField(max_length=50, choices=ICONES, default='fa-exclamation-triangle')
    cor = models.CharField(max_length=7, default='#00D4FF')
    ativa = models.BooleanField(default=True)
    ordem = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categorias_ocorrencias'
        verbose_name = 'Categoria de Ocorrência'
        verbose_name_plural = 'Categorias de Ocorrências'
        ordering = ['ordem', 'nome']

    def __str__(self):
        return self.nome


class AgenciaResponsavel(models.Model):
    """Agências/Órgãos Responsáveis por atendimento de ocorrências"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nome = models.CharField(max_length=200, unique=True)
    sigla = models.CharField(max_length=20, unique=True)
    descricao = models.TextField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)
    icone = models.CharField(max_length=50, default='fa-building')
    cor = models.CharField(max_length=7, default='#B537F2')
    ativa = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'agencias_responsaveis'
        verbose_name = 'Agência Responsável'
        verbose_name_plural = 'Agências Responsáveis'
        ordering = ['nome']

    def __str__(self):
        return f"{self.sigla} - {self.nome}"


class ProcedimentoOperacional(models.Model):
    """Procedimentos Operacionais Padrão (POPs)"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codigo = models.CharField(max_length=50, unique=True)
    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)
    categoria = models.ForeignKey(
        CategoriaOcorrencia,
        on_delete=models.PROTECT,
        related_name='procedimentos'
    )
    agencias = models.ManyToManyField(
        AgenciaResponsavel,
        related_name='procedimentos',
        blank=True
    )

    arquivo_pdf = models.FileField(upload_to='pops/', blank=True, null=True)
    arquivo_path = models.CharField(max_length=500, blank=True)

    checklist = models.JSONField(default=list, blank=True)
    tempo_resposta_esperado = models.IntegerField(
        null=True,
        blank=True,
        help_text='Tempo esperado em minutos'
    )

    ativo = models.BooleanField(default=True)
    versao = models.CharField(max_length=20, default='R00')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='pops_criados'
    )

    class Meta:
        db_table = 'procedimentos_operacionais'
        verbose_name = 'Procedimento Operacional'
        verbose_name_plural = 'Procedimentos Operacionais'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.titulo}"


class OcorrenciaGerenciada(models.Model):
    """Ocorrência/Chamado/Solicitação do Sistema de Gerenciamento"""

    STATUS_CHOICES = [
        ('aberta', 'Aberta'),
        ('em_andamento', 'Em Andamento'),
        ('aguardando', 'Aguardando Retorno'),
        ('resolvida', 'Resolvida'),
        ('fechada', 'Fechada'),
        ('cancelada', 'Cancelada'),
    ]

    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]

    ORIGEM_CHOICES = [
        ('telefone', 'Telefone'),
        ('email', 'E-mail'),
        ('whatsapp', 'WhatsApp'),
        ('redes_sociais', 'Redes Sociais'),
        ('aplicativo', 'Aplicativo'),
        ('presencial', 'Presencial'),
        ('sistema', 'Sistema'),
    ]

    # Identificação
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_protocolo = models.CharField(max_length=50, unique=True, editable=False)

    # Classificação
    categoria = models.ForeignKey(
        CategoriaOcorrencia,
        on_delete=models.PROTECT,
        related_name='ocorrencias_gerenciadas'
    )
    procedimento = models.ForeignKey(
        ProcedimentoOperacional,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ocorrencias'
    )
    agencias = models.ManyToManyField(
        AgenciaResponsavel,
        related_name='ocorrencias_gerenciadas',
        blank=True
    )

    # Dados Básicos
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    origem = models.CharField(max_length=20, choices=ORIGEM_CHOICES)

    # Status e Prioridade
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='aberta')
    prioridade = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='media')

    # Localização
    endereco = models.CharField(max_length=500, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, default='Rio de Janeiro')
    cep = models.CharField(max_length=10, blank=True)
    referencia = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)

    # Solicitante
    solicitante_nome = models.CharField(max_length=200, blank=True)
    solicitante_telefone = models.CharField(max_length=20, blank=True)
    solicitante_email = models.EmailField(blank=True)

    # Datas
    data_abertura = models.DateTimeField(auto_now_add=True)
    data_prevista = models.DateTimeField(null=True, blank=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)

    # Responsáveis
    aberto_por = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='ocorrencias_gerenciadas_abertas'
    )
    responsavel = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ocorrencias_gerenciadas_responsavel'
    )

    # Metadados
    observacoes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    dados_extras = models.JSONField(default=dict, blank=True)

    # Auditoria
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ocorrencias_gerenciadas'
        verbose_name = 'Ocorrência Gerenciada'
        verbose_name_plural = 'Ocorrências Gerenciadas'
        ordering = ['-data_abertura']
        indexes = [
            models.Index(fields=['status', 'prioridade']),
            models.Index(fields=['categoria', 'data_abertura']),
            models.Index(fields=['numero_protocolo']),
            models.Index(fields=['data_abertura']),
        ]

    def __str__(self):
        return f"{self.numero_protocolo} - {self.titulo}"

    def save(self, *args, **kwargs):
        if not self.numero_protocolo:
            from django.db.models import Max
            from django.utils import timezone as tz
            hoje = tz.now().strftime('%Y%m%d')
            ultimo = OcorrenciaGerenciada.objects.filter(
                numero_protocolo__startswith=f'OCR-{hoje}'
            ).aggregate(Max('numero_protocolo'))['numero_protocolo__max']

            if ultimo:
                seq = int(ultimo.split('-')[-1]) + 1
            else:
                seq = 1

            self.numero_protocolo = f'OCR-{hoje}-{seq:04d}'

        super().save(*args, **kwargs)

    @property
    def status_color(self):
        """Retorna cor CSS baseada no status"""
        colors = {
            'aberta': '#00D4FF',
            'em_andamento': '#FFB800',
            'aguardando': '#B537F2',
            'resolvida': '#4CAF50',
            'fechada': '#6B7280',
            'cancelada': '#EF4444',
        }
        return colors.get(self.status, '#00D4FF')

    @property
    def prioridade_color(self):
        """Retorna cor CSS baseada na prioridade"""
        colors = {
            'baixa': '#4CAF50',
            'media': '#00D4FF',
            'alta': '#FFB800',
            'critica': '#EF4444',
        }
        return colors.get(self.prioridade, '#00D4FF')


class HistoricoOcorrenciaGerenciada(models.Model):
    """Histórico de alterações da ocorrência gerenciada"""

    TIPOS = [
        ('criacao', 'Criação'),
        ('atualizacao', 'Atualização'),
        ('mudanca_status', 'Mudança de Status'),
        ('atribuicao', 'Atribuição'),
        ('comentario', 'Comentário'),
        ('anexo', 'Anexo Adicionado'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ocorrencia = models.ForeignKey(
        OcorrenciaGerenciada,
        on_delete=models.CASCADE,
        related_name='historico'
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descricao = models.TextField()
    dados_alterados = models.JSONField(default=dict, blank=True)

    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historico_ocorrencias_gerenciadas'
        verbose_name = 'Histórico de Ocorrência'
        verbose_name_plural = 'Históricos de Ocorrências'
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.ocorrencia.numero_protocolo} - {self.tipo} - {self.timestamp}"

    @property
    def tipo_icone(self):
        """Retorna ícone FontAwesome baseado no tipo"""
        icones = {
            'criacao': 'fa-plus-circle',
            'atualizacao': 'fa-edit',
            'mudanca_status': 'fa-exchange-alt',
            'atribuicao': 'fa-user-plus',
            'comentario': 'fa-comment',
            'anexo': 'fa-paperclip',
        }
        return icones.get(self.tipo, 'fa-info-circle')

    @property
    def tipo_cor(self):
        """Retorna cor CSS baseada no tipo"""
        cores = {
            'criacao': '#4CAF50',
            'atualizacao': '#00D4FF',
            'mudanca_status': '#FFB800',
            'atribuicao': '#B537F2',
            'comentario': '#6B7280',
            'anexo': '#00D4FF',
        }
        return cores.get(self.tipo, '#00D4FF')


class AnexoOcorrenciaGerenciada(models.Model):
    """Anexos da ocorrência gerenciada (fotos, documentos)"""

    TIPOS = [
        ('foto', 'Foto'),
        ('documento', 'Documento'),
        ('video', 'Vídeo'),
        ('audio', 'Áudio'),
        ('outro', 'Outro'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ocorrencia = models.ForeignKey(
        OcorrenciaGerenciada,
        on_delete=models.CASCADE,
        related_name='anexos'
    )
    tipo = models.CharField(max_length=20, choices=TIPOS)
    arquivo = models.FileField(upload_to='ocorrencias/%Y/%m/')
    nome_original = models.CharField(max_length=255)
    descricao = models.CharField(max_length=500, blank=True)
    tamanho = models.IntegerField(help_text='Tamanho em bytes')

    uploaded_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'anexos_ocorrencias_gerenciadas'
        verbose_name = 'Anexo de Ocorrência'
        verbose_name_plural = 'Anexos de Ocorrências'
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.ocorrencia.numero_protocolo} - {self.nome_original}"

    @property
    def tipo_icone(self):
        """Retorna ícone FontAwesome baseado no tipo"""
        icones = {
            'foto': 'fa-image',
            'documento': 'fa-file-alt',
            'video': 'fa-video',
            'audio': 'fa-volume-up',
            'outro': 'fa-file',
        }
        return icones.get(self.tipo, 'fa-file')

    @property
    def tamanho_formatado(self):
        """Retorna tamanho formatado (KB, MB, etc.)"""
        if self.tamanho < 1024:
            return f"{self.tamanho} B"
        elif self.tamanho < 1024 * 1024:
            return f"{self.tamanho / 1024:.1f} KB"
        else:
            return f"{self.tamanho / (1024 * 1024):.1f} MB"


class AgenciaOcorrencia(models.Model):
    """
    Relação entre Agência e Ocorrência com status de acionamento.
    Permite controlar o status de cada agência: informada, presente, concluída.
    """

    STATUS_CHOICES = [
        ('informada', 'Informada'),
        ('a_caminho', 'A Caminho'),
        ('presente', 'Presente no Local'),
        ('atuando', 'Em Atuação'),
        ('concluida', 'Concluída'),
        ('dispensada', 'Dispensada'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ocorrencia = models.ForeignKey(
        OcorrenciaGerenciada,
        on_delete=models.CASCADE,
        related_name='agencias_acionadas'
    )
    agencia = models.ForeignKey(
        AgenciaResponsavel,
        on_delete=models.CASCADE,
        related_name='acionamentos'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='informada')

    # Controle de datas
    data_acionamento = models.DateTimeField(auto_now_add=True)
    data_chegada = models.DateTimeField(null=True, blank=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)

    # Quem acionou e observações
    acionado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='agencias_acionadas'
    )
    observacoes = models.TextField(blank=True)

    class Meta:
        db_table = 'agencias_ocorrencias'
        verbose_name = 'Agência Acionada'
        verbose_name_plural = 'Agências Acionadas'
        ordering = ['-data_acionamento']
        unique_together = ['ocorrencia', 'agencia']

    def __str__(self):
        return f"{self.agencia.sigla} - {self.ocorrencia.numero_protocolo} ({self.get_status_display()})"

    @property
    def status_cor(self):
        """Retorna cor CSS baseada no status"""
        cores = {
            'informada': '#FFB800',
            'a_caminho': '#00D4FF',
            'presente': '#B537F2',
            'atuando': '#00D4FF',
            'concluida': '#4CAF50',
            'dispensada': '#6B7280',
        }
        return cores.get(self.status, '#00D4FF')

    @property
    def status_icone(self):
        """Retorna ícone FontAwesome baseado no status"""
        icones = {
            'informada': 'fa-phone',
            'a_caminho': 'fa-truck',
            'presente': 'fa-map-marker-alt',
            'atuando': 'fa-tools',
            'concluida': 'fa-check-circle',
            'dispensada': 'fa-times-circle',
        }
        return icones.get(self.status, 'fa-building')


# ==========================================
# MATRIZ DECISÓRIA - MOTOR DE DECISÃO
# ==========================================

class MatrizDecisoria(models.Model):
    """
    Versão da Matriz Decisória HEXAGON.
    Define os pesos e configurações para cálculo do estágio operacional da cidade.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    versao = models.CharField(max_length=20, unique=True)  # ex: "3.5"
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True)

    # Status
    STATUS_CHOICES = [
        ('rascunho', 'Rascunho'),
        ('em_aprovacao', 'Em Aprovação'),
        ('publicada', 'Publicada'),
        ('arquivada', 'Arquivada'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='rascunho')
    ativa = models.BooleanField(default=False)  # Apenas 1 pode estar ativa

    # Pesos dos grupos (conforme planilha HEXAGON)
    peso_meteorologia = models.DecimalField(max_digits=3, decimal_places=1, default=2.0)
    peso_incidentes = models.DecimalField(max_digits=3, decimal_places=1, default=2.0)
    peso_mobilidade = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    peso_eventos = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)

    # Configuração detalhada dos grupos em JSON
    config_grupo1 = models.JSONField(default=dict, blank=True)  # Meteorologia
    config_grupo2 = models.JSONField(default=dict, blank=True)  # Incidentes
    config_grupo3 = models.JSONField(default=dict, blank=True)  # Mobilidade
    config_grupo4 = models.JSONField(default=dict, blank=True)  # Eventos

    # Auditoria
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='matrizes_criadas')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'matrizes_decisorias'
        verbose_name = 'Matriz Decisória'
        verbose_name_plural = 'Matrizes Decisórias'
        ordering = ['-created_at']

    def __str__(self):
        return f"Matriz {self.versao} - {self.nome}"

    def save(self, *args, **kwargs):
        # Se marcada como ativa, desativar outras
        if self.ativa:
            MatrizDecisoria.objects.exclude(pk=self.pk).update(ativa=False)
        super().save(*args, **kwargs)

    @property
    def peso_total(self):
        """Soma de todos os pesos"""
        return float(self.peso_meteorologia + self.peso_incidentes + self.peso_mobilidade + self.peso_eventos)


class EstagioOperacional(models.Model):
    """
    Registro de cálculo de estágio operacional em momento específico.
    Armazena todos os dados usados no cálculo para auditoria.
    """

    # Nomenclatura oficial dos níveis
    NOMENCLATURA_NIVEIS = {
        0: 'Normal',
        1: 'Atenção',
        2: 'Alerta',
        3: 'Mobilização',
        4: 'Crise',
        5: 'Calamidade',
        6: 'Colapso',
    }

    # Cores por nível (tema high-tech)
    CORES_NIVEIS = {
        0: '#00ff88',   # Verde neon
        1: '#00D4FF',   # Cyan
        2: '#FFB800',   # Amarelo
        3: '#FF6B00',   # Laranja
        4: '#FF4444',   # Vermelho
        5: '#B537F2',   # Roxo
        6: '#FF0055',   # Vermelho intenso
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    matriz = models.ForeignKey(MatrizDecisoria, on_delete=models.PROTECT, related_name='calculos')

    # Níveis calculados por grupo (0-6)
    nivel_meteorologia = models.IntegerField(default=0)
    nivel_incidentes = models.IntegerField(default=0)
    nivel_mobilidade = models.IntegerField(default=0)
    nivel_eventos = models.IntegerField(default=0)

    # Nível final da cidade
    nivel_cidade = models.IntegerField()
    nivel_cidade_decimal = models.DecimalField(max_digits=5, decimal_places=3)
    proximidade_proximo_nivel = models.DecimalField(max_digits=5, decimal_places=4)

    # Dados de entrada usados no cálculo (para auditoria)
    dados_entrada = models.JSONField(default=dict)

    # Detalhamento de cada grupo
    detalhes_meteorologia = models.JSONField(default=dict, blank=True)
    detalhes_incidentes = models.JSONField(default=dict, blank=True)
    detalhes_mobilidade = models.JSONField(default=dict, blank=True)
    detalhes_eventos = models.JSONField(default=dict, blank=True)

    # Justificativa do cálculo
    justificativa = models.TextField(blank=True)

    # Ações recomendadas geradas automaticamente
    acoes_geradas = models.JSONField(default=list, blank=True)

    # Timestamp
    calculado_em = models.DateTimeField(auto_now_add=True)

    # Usuário que solicitou (pode ser automático/sistema)
    solicitado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='estagios_solicitados'
    )

    class Meta:
        db_table = 'estagios_operacionais'
        verbose_name = 'Estágio Operacional'
        verbose_name_plural = 'Estágios Operacionais'
        ordering = ['-calculado_em']
        indexes = [
            models.Index(fields=['-calculado_em', 'nivel_cidade']),
        ]

    def __str__(self):
        return f"Nível {self.nivel_cidade} ({self.get_nomenclatura()}) - {self.calculado_em.strftime('%d/%m/%Y %H:%M')}"

    def get_nomenclatura(self):
        """Retorna nomenclatura textual do nível"""
        return self.NOMENCLATURA_NIVEIS.get(self.nivel_cidade, 'Desconhecido')

    def get_cor(self):
        """Retorna cor CSS do nível"""
        return self.CORES_NIVEIS.get(self.nivel_cidade, '#00D4FF')

    @property
    def percentual_proximo_nivel(self):
        """Retorna proximidade em percentual"""
        return float(self.proximidade_proximo_nivel) * 100


class AcaoRecomendada(models.Model):
    """
    Ações recomendadas para cada faixa de nível.
    Vincula agências, POPs e categorias automaticamente.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    matriz = models.ForeignKey(MatrizDecisoria, on_delete=models.CASCADE, related_name='acoes')

    # Faixa de nível que dispara esta ação
    nivel_minimo = models.IntegerField()
    nivel_maximo = models.IntegerField()

    # Descrição da ação
    titulo = models.CharField(max_length=200)
    descricao = models.TextField()

    # Vinculação com entidades existentes
    agencias = models.ManyToManyField(
        'AgenciaResponsavel',
        blank=True,
        related_name='acoes_matriz'
    )
    pop = models.ForeignKey(
        'ProcedimentoOperacional',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acoes_matriz'
    )
    categoria = models.ForeignKey(
        'CategoriaOcorrencia',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='acoes_matriz'
    )

    # Priorização automática
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('critica', 'Crítica'),
    ]
    prioridade_automatica = models.CharField(max_length=20, choices=PRIORIDADE_CHOICES, default='media')
    prazo_horas = models.IntegerField(null=True, blank=True, help_text='Prazo em horas para execução')

    # Ordenação e status
    ordem = models.IntegerField(default=0)
    ativa = models.BooleanField(default=True)

    class Meta:
        db_table = 'acoes_recomendadas'
        verbose_name = 'Ação Recomendada'
        verbose_name_plural = 'Ações Recomendadas'
        ordering = ['nivel_minimo', 'ordem']

    def __str__(self):
        return f"{self.titulo} (Níveis {self.nivel_minimo}-{self.nivel_maximo})"

    def aplicavel_para_nivel(self, nivel):
        """Verifica se ação é aplicável para um nível específico"""
        return self.nivel_minimo <= nivel <= self.nivel_maximo

    @property
    def cor_prioridade(self):
        """Retorna cor CSS baseada na prioridade"""
        cores = {
            'baixa': '#00ff88',
            'media': '#00D4FF',
            'alta': '#FFB800',
            'critica': '#FF0055',
        }
        return cores.get(self.prioridade_automatica, '#00D4FF')
