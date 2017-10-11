#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cgi

print("Content-Type: text/html")
print("")
print("Resultado del Analisis de Sentimientos del texto")

form = cgi.FieldStorage()
var_caja = form["txtTexto"].value
print(var_caja)
form["txtTexto"].value="Resultado:"

