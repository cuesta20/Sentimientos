#-*- coding=utf-8 -*-

#importacion de las librerias utilizadas
from django.http import HttpResponse
from django.shortcuts import render
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.http import HttpResponseRedirect
import random 
import datetime
import nltk  #para el procesamiento del lenguaje natural
import nltk.classify.util
from nltk.classify import NaiveBayesClassifier
from nltk.corpus import movie_reviews, stopwords, cess_esp , conll2002
from nltk.probability import FreqDist
import string
from itertools import chain
from nltk.metrics import ConfusionMatrix
from nltk.collocations import *
import paramiko  #para acceso ssh al servidor
import os
import yaml   #para configuracion
from nltk import word_tokenize
from nltk.data import load
from nltk.stem import SnowballStemmer
from string import punctuation
from nltk.tokenize.toktok import ToktokTokenizer


#from django.views.decorators.csrf import csrf_exempt
#from textblob import TextBlob
#from sklearn.feature_extraction.text import CountVectorizer       

import collections
import nltk.metrics
from nltk.corpus import names

'''
url='http://62.204.199.211:8880'
urlSin='62.204.199.211:8880'
urlSinPuerto='62.204.199.211'
nickname='david'
clave='daviduned2017.'
'''
url=""
urlSin=""
urlSinPuerto=""
nickname=""
clave=""
puerto=22
segundos=20
texto=""
contador=1
non_words=""
stemmer=""

#limpia pantalla de la consola en windows o linux
def limpia():
    if os.name == 'posix':
        os.system('clear')

    elif os.name in ('ce', 'nt', 'dos'):
        os.system('cls')

# función para llamar a la pagina landing page del sitio WEB
def index(request):
	global contador
	global texto
	response = ''
	cadtexto=""
	cadresultado=""
	limpia()
	if request.POST:
		print("\n Entra en POST \n")
		cadtexto = request.POST.get('txtTexto')
		cadresultado = request.POST.get('txtResultado')
	if contador==1:
		leerYAML()
		conectarServidor()
		descargarCorpus()
		entrenamiento()
		clasificar()
		resultado()
		contador=contador+1
		return render_to_response('index.html',cadresultado,cadtexto)
	else:	
		return render_to_response('resultado.html')

def conectarServidor():
	print("\n ==============================================================\n")
	print("         Conectando con el servidor de la Universidad            ")
	print("\n ==============================================================\n")
	try:
		nltk.set_proxy(url, (nickname, clave))	
	except Exception:
		print("  Error de Comunicacion con el Servidor") 
		return
	print("   Servidor Conectado OK \n\n")
	conexionSSH()
	return
	
def conexionSSH():
	print("   Fase 1/6 Iniciamos la conexion SSH.............. \n\n")
	# Datos para la conexión SSH
	ssh_servidor = urlSin
	ssh_usuario  = nickname
	ssh_clave    = clave
	ssh_puerto   = puerto 
	comando      = 'ls' # comando que vamos a ejecutar en el servidor para comprobar acceso
	
	# Conectamos al servidor
	try:
		ssh = paramiko.SSHClient()  # Iniciamos un cliente SSH
		ssh.load_system_host_keys()  # Agregamos el listado de host conocidos
		ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Si no encuentra el host, lo agrega automáticamente
		# Iniciamos la conexión.
		#conexion= ssh.connect('62.204.199.211', port=22, username='david', password='daviduned2017.') 
		conexion= ssh.connect(urlSinPuerto, port=puerto, username=nickname, password=clave,  timeout=segundos)  
		print("   Conexion cliente establecida con el servidor de la Universidad \n\n      "+str(ssh))
		print("\n\n    Archivos del Servidor ")
		#listar los ficheros y directorios del servidor 
		stdin, stdout, stderr = ssh.exec_command('ls -l')
		x = stdout.readlines()
		print("\n   ==============================================================\n")
		for line in x:
			print("   "+str(line))
		print("\n   ==============================================================\n")	
		#con = paramiko.Transport((ssh_servidor, ssh_puerto))
		#con.connect(username = ssh_usuario, password = ssh_clave)
		# Abrimos una sesión en el servidor
		#canal = con.open_session()
	except paramiko.ssh_exception.SSHException:
		print("Error de Comunicacion con el Servidor SSH") 
		ssh.close()
		return
	except paramiko.AuthenticationException:
		print("Error de Autenticación con el Servidor SSH") 
		ssh.close()
		return
	except socket.error, e:
		print("Error de Socket con el Servidor SSH") 
		ssh.close()
		return
	print("\n\n  Servidor SSH en Escucha \n\n")
	#conexion.close()	
	return
	
# el corpus es un conjunto linguisitico amplio y estructurado de ejemplos reales del uso de la lengua
def descargarCorpus():
	print("   Fase 2/6  Descargando Corpus..................espere un momento \n")
	'''
	sino="n"
	sino=raw_input("    ===> Descargar el DATASET del Corpus S/N ?  ")
	sino=sino.lower()
	if (sino=="s"):
		print("\n iniciando la descarga...... espere un momento \n")
		#nltk.download("movie_reviews")
		nltk.download("spanish_grammars")
		nltk.download("cess_esp")
		print("\n  dataset descargado \n")
	if (sino=="n"):
		print("\n  procesando dataset en memoria \n")
		reviews = [(list(movie_reviews.words(fileid)), category)
		for category in movie_reviews.categories()
		for fileid in movie_reviews.fileids(category)]
		new_train, new_test = reviews[0:100], reviews[101:200]
		print(new_train[0])
		print("\n\n")
	'''
	print("\n  procesando dataset en memoria.... espere un momento por favor \n")
	'''
	reviews = [(list(movie_reviews.words(fileid)), category)
	for category in movie_reviews.categories()
	for fileid in movie_reviews.fileids(category)]
	new_train, new_test = reviews[0:100], reviews[101:200]
	print(new_train[0])
	print("\n\n")
	'''
	reviews = list(cess_esp.words()) #reviews = [(list(cess_esp.words(fileid)), category)]	
	new_train, new_test = reviews[0:100], reviews[101:200]	
	print("\n        procesando dataset en memoria del cees_esp \n\n")
	#print(str(reviews))
	print("\n\n")
	print(new_train)
	print("\n\n      Test...... \n")
	print(new_test)
	print("\n\n")
	return


# metodo feaststructs para extraccion de caracteristicas de diccionarios 
def word_feats(words):
	return dict([(word, True) for word in words])

#código para entrenar y probar el clasificador de naive bayes en el corpus de critica de peliculas de cine	
def entrenamiento():
	global texto
	print("\n\n      Fase 3/6 Entrenamiento \n")
	
	#creacion de la lista de tuplas formada por pares de valores
	conjunto = [('Me gusta el cine', 'pos'),
    ('Me gusta comer en restaurantes', 'pos'),
    ('Me gustan la peliculas de accion', 'pos'),
    ('No me gusta el teatro', 'neg'),
    ('No me gusta la poesia', 'neg'),
	('Si me gusta la poesia', 'pos'),
	]

	test = [('Quiero ir a un restaurante a comer', 'pos'),
    ('Normalmente me gusta el cine', 'neg'),
    ('Mi jefe no me gusta', 'neg'), 
	('Normalmente si me gusta el cine', 'pos'),
    ('Mi jefa si me gusta', 'pos'), 
	('Si me gusta Trabajar', 'pos'), 
	]
	
	'''
	conjunto = [('I like the Cine', 'pos'),
    ('I like eat in the restaurant', 'pos'),
    ('I like actions films', 'pos'),
    ('I not like the rain', 'neg'),
    ('I not like the production', 'neg'),
	]

	test = [('I want go to eat in the restaurant', 'pos'),
    ('playing really see not the cine', 'neg'),
    ('Not like the studio', 'neg'), 
	('The people is happy in the cine', 'pos'),
    ('my director is happy with the film', 'pos'), 
	]
	print("\n\n   Datos de entrenamiento creados con exito \n")
	#obtenemos el clasificador
	print("    Generando el clasificador con los Datos del entrenamiento...:\n\n   "+str(conjunto)) 
	'''
	print("\n")
	print("      clasificando con el algoritmo Naive Bayes \n\n")
	
	exactitud=""
	cadena=""
	negids = movie_reviews.fileids('neg')
	posids = movie_reviews.fileids('pos')
	negfeats = [(word_feats(movie_reviews.words(fileids=[f])), 'neg') for f in negids]
	posfeats = [(word_feats(movie_reviews.words(fileids=[f])), 'pos') for f in posids]
	negcutoff = len(negfeats)*3/4
	poscutoff = len(posfeats)*3/4
	trainfeats = negfeats[:negcutoff] + posfeats[:poscutoff]
	testfeats = negfeats[negcutoff:] + posfeats[poscutoff:]
	#cadena='Entrenamiento sobre '+str(len(trainfeats))+' instancias, Test de prueba sobre '+str(len(testfeats))+' instancias'  
	print('\n      Entrenamiento sobre %d instancias, Test de prueba sobre %d instancias' % (len(trainfeats), len(testfeats)))
	classifier = NaiveBayesClassifier.train(trainfeats)
	print("\n")
	exactitud=str(nltk.classify.util.accuracy(classifier, testfeats))
	cadena='      Exactitud: '+exactitud
	print(cadena)
	print("\n\n")
	print("      Fin de la clasificacion con el algoritmo Naive Bayes \n\n")
	print("\n\n      Fase 4/6  Tokenizando corpus..................espere un momento \n\n")
	print("      Resultado del entrenamiento: \n\n  ")
	classifier.show_most_informative_features()
	#classifier.accuracy(test) #puntuacion
	#classifier.show_informative_features(5) 
	print("\n    Tokenizacion finalizada \n\n")
	#cadena_html=str(cadena)+"\n"+str(exactitud)
	#return render_to_response('resultado.html', locals(), context_instance=RequestContext(request))
	#return HttpResponse("Detalle %s." % categoria
	#spanish_tokenizer = nltk.data.load("spanish.pickle") #ojooooooooo
	#spanish_tokenizer.tokenize(texto) #ojooooooooo
	#toktok = ToktokTokenizer()
	#sent = u"¿Quién eres tú? ¡Hola! ¿Dónde estoy?"
	#toktok.tokenize(sent)
	#OJO nuevo
	refsets = collections.defaultdict(set)
	testsets = collections.defaultdict(set)
	for i, (feats, label) in enumerate(testfeats):
		refsets[label].add(i)
		observed = classifier.classify(feats)
		testsets[observed].add(i)
	'''
	print('\n pos precision:', nltk.metrics.precision(refsets['pos'], testsets['pos']))
	print('\n pos recall:', nltk.metrics.recall(refsets['pos'], testsets['pos']))
	print('\n pos F-measure:', nltk.metrics.f_measure(refsets['pos'], testsets['pos']))
	print('\n neg precision:', nltk.metrics.precision(refsets['neg'], testsets['neg']))
	print('\n neg recall:', nltk.metrics.recall(refsets['neg'], testsets['neg']))
	print('\n neg F-measure:', nltk.metrics.f_measure(refsets['neg'], testsets['neg']))
	'''
	return
	
def prueba (req, nombre):
	print(nombre)
	return

def clasificar():	
	global texto
	print("      Fase 5/6 Clasificacion de los tokens y steaming..................espere un momento por favor \n\n")
	stop = stopwords.words('spanish') 
	print("\n      diccionario castellano de palabras finales: \n\n  "+str(stop))
	all_words = FreqDist(w.lower() for w in movie_reviews.words() if w.lower() not in stop and w.lower() not in string.punctuation)
	print("\n      Palabras clasificadas:               "+str(all_words))
	documents = [([w for w in movie_reviews.words(i) if w.lower() not in stop and w.lower() not in string.punctuation], i.split('/')[0]) for i in movie_reviews.fileids()]
	word_features = FreqDist(chain(*[i for i,j in documents]))
	word_features = word_features.keys()[:100]
	numtrain = int(len(documents) * 90 / 100)
	print("\n    Num. Entrenamientos de la clasificacion:        "+str(numtrain))
	train_set = [({i:(i in tokens) for i in word_features}, tag) for tokens,tag in documents[:numtrain]]
	test_set = [({i:(i in tokens) for i in word_features}, tag) for tokens,tag in documents[numtrain:]]
	classifier = NaiveBayesClassifier.train(train_set)
	print("\n    Precision:     "+str(nltk.classify.accuracy(classifier, test_set))+" \n")
	classifier.show_most_informative_features(5)
	texto=str(classifier)
	#cadena_html="Prueba"
	#return render_to_response('resultado.html', locals(), context_instance=RequestContext(request))
	
	#OJO nuevo
	# inicializar el extractor de raices lexicales
	print("\n       Inicializando extractor de raices lexicales \n")
	global stemmer
	stemmer = SnowballStemmer('spanish')
	print(" \n       Stemmer - extracion de raices semanticas \n\n "+str(stemmer))
	# inicializar la lista de palabras ignoradas 
	print(" \n     Inicializando lista de palabras ignoradas \n")
	global non_words
	non_words = list(punctuation)  
	print(" \n    Palabras ignoradas:    "+str(non_words))
	print(" \n   agregando signos de apertura y digitos \n")
	# agregar a la lista los signos de apertura y los digitos [1-9]
	non_words.extend(['¿', '¡'])  
	non_words.extend(map(str,range(10)))
	print("      Ingresa una frase para el proceso de NLP:")
	t=raw_input();
	print(tokenize(str(t)));
	return
	
def resultado():
	print("   Fase 6/6  Resultado final")
	return
	
def leerYAML():
	global url
	global urlSin
	global urlSinPuerto
	global nickname
	global clave
	global puerto
	
	url='http://62.204.199.211:8880'
	urlSin='62.204.199.211:8880'
	urlSinPuerto='62.204.199.211'
	nickname='david'
	clave='daviduned2017.'
	puerto=22
	
	print("\n    Cargando el archivo YAML de configuración \n")
	print("      Directorio actual ==> "+str(os.getcwd()))
	print("\n")
	archivo="App.yaml"
	stream = open(archivo, "r")
	docs = yaml.load_all(stream)
	for doc in docs:
		for k,v in doc.items():
			print(k, "->", v)
			if k==url:
				url=v
			if k==urlSin:
				urlSin=v
			if k==urlSinPuerto:
				urlSinPuerto=v
			if k==nickname:
				nickname=v	
			if k==clave:
				clave=v	
			if k==puerto:
				puerto=v	
		print("\n ,") 

def test_esp():
        words = cess_esp.words()[:15]
        txt = "El grupo estatal Electricité_de_France -Fpa- EDF -Fpt- anunció hoy , jueves , la compra del"
        self.assertEqual(words, txt.split())

def bayes(request,texto):
	print("funcion para Proceso de Bayes \n")
	if(request.GET.get('btnbuscar')):
		print("Bayes GET \n")
		cadena=request.GET.get('txtResultado')
		print("Cadena: "+str(cadena))
	if request.method == "POST":
		print("Bayes POST \n")
		form = NameForm(request.POST)
		data=request.POST
		if form.is_valid():
			print("formu OK")
		if request.POST:
			if 'btnbuscar' in request.POST:
				print("btnbuscar \n")
			elif 'boton3' in request.POST:
				print("boton3 \n")
		response = ''
		for key, value in request.POST.items():
			response += 'key:%s value:%s\n' % (key, value)
		#return HttpResponse(response) 
		print("bayes POST \n")
		return render(request, 'resultado.html', {'form': form} )		
	else:
		form = NameForm() #hacemos formulario en blanco
	print("bayes resultado.html \n")	
	return render(request, 'resultado.html', {'form': form} )

def corpus(request):
	print("descargando corpus \n")
	nltk.download()
	#nltk.download("movie_reviews")
	nltk.download("spanish_grammars")
	nltk.download("cess_esp")
	print("FIN \n")
		
def gender_features(name):
	features = {}
	features["first_letter"] = name[0].lower()
	features["last_letter"] = name[-1].lower()
	features["first_three_letter"] = name[:3].lower()
	features["last_three_letter"] = name[-3:].lower()
	return features
 
def indice(request):
	print("INDICE \n")
	message = ''
	if request.method == 'POST':
		input_name = request.POST.get("name", "")
		if input_name != '':
			# Prepare the label for each name
			labeled_names = ([(name, 'male') for name in names.words('male.txt')] + [(name, 'female') for name in names.words('female.txt')])
			random.shuffle(labeled_names)
			# Generate the training set and test set
			feature_set = [(gender_features(n), gender) for (n, gender) in labeled_names]
			train_set = feature_set[:3000]
			test_set = feature_set[3000:]
			classifier = nltk.NaiveBayesClassifier.train(train_set)
			message = input_name + " is probably " + classifier.classify(gender_features(input_name)) + ". (accuracy : " + str(round(nltk.classify.accuracy(classifier, test_set) * 100, 2)) + "%)"
		else:
			message = "Name cannot be empty!"
	context = {'message': message}
	return render(request, 'templates/form.html', context)	
	
#######################

	
# funcion de extraccion de raices lexicales
def stem(word):
	global stemmer
	return stemmer.stem(word)

# funcion de extraccion de raices lexicales sobre una lista
def stem_tokens(tokens):  
	stemmed = []
	for item in tokens:
		stemmed.append(stem(item))
	return stemmed
# funcion de disgregacion de palabras 
'''
    Separa las palabras
'''
def tokenize(text): 
	global non_words 
	print("\n Palabras eliminadas: "+str(non_words)+" \n")
	qgrams=[];
	trigrams=[];
	bigrams=[];
	text=text.lower()
	print("\n Texto en minusculas: "+str(text)+" \n")
	text = ''.join([c for c in text if c not in non_words])
	tokens =  word_tokenize(text)
	tokens = stem_tokens(tokens)
	return tokens	
	
def hora_actual(request):
	ahora = datetime.datetime.now()
	html = u"<html><body>Día y hora actual: %s.</body></html>" % ahora
	return HttpResponse(html)	