from logica import LPQuery, ASK

class Agente:

	def __init__(self):
		self.perceptos = []
		self.acciones = []
		self.tabla = {}
		self.reglas = []
		self.base = LPQuery([])
		self.turno = 1
		self.loc = (0,0)

	def reaccionar(self, DEB=False):
		if len(self.acciones) == 0:
			self.programa(DEB)
		a = self.acciones.pop(0)
		self.turno += 1
		return a

	def interp_percepto(self, mundo):
		if mundo == 'laberinto':
			orden = ['frn_bloq_', 'izq_bloq_', 'der_bloq_', 'atr_bloq_']
		elif mundo == 'wumpus':
			orden = ['hedor_', 'brisa_', 'brillo_', 'batacazo_', 'grito_']
		f = ''
		inicial = True
		for i, p in enumerate(self.perceptos):
			if p:
				if inicial:
					f = orden[i]+str(self.turno)
					inicial = False
				else:
					f = f + 'Y' + orden[i]+str(self.turno)
			else:
				if inicial:
					f = '-' + orden[i]+str(self.turno)
					inicial = False
				else:
					f = f + 'Y-' + orden[i]+str(self.turno)
		return f

# METODOS DE ESTIMACIÓN DE ESTADO
	def estimar_estado(self, W):
		self.base.TELL(f'segura({self.loc[0]},{self.loc[1]})')
		cas_seguras = self.adyacentes_seguras()
		self.base.TELL('Y'.join([f'segura({c[0]},{c[1]})' for c in cas_seguras]))
		nueva_dir = self.nueva_direccion()
		self.base.TELL(nueva_dir)
		nueva_pos = self.nueva_posicion()
		self.base.TELL(nueva_pos)
		formulas = [d for d in self.base.datos if f'_{self.turno}' in d]
		formulas += [s for s in self.base.datos if 'segura' in s]
		formulas += self.fluentes_mapa_mental()
		formulas += self.brisa_pozo()
		formulas += self.hedor_wumpus()
		formulas += self.casilla_segura()
		formulas += self.casillas_visitadas()
		self.perceptos = W.para_sentidos()
		formulas += [self.interp_percepto(mundo='wumpus')]
		self.base = LPQuery(formulas)
  
	def casillas_visitadas(self):
		turno = self.turno
		# Guardamos las casillas visitadas
		visitadas = []
		casillas = [(x,y) for x in range(4) for y in range(4)]
		for c in casillas:
			x, y = c
			consulta = ASK(f'visitada({x},{y})_{turno}', 'success', self.base)
			if consulta:
				visitadas.append(f'visitada({x},{y})_{turno}')
		return visitadas

	def nueva_posicion(self):
    
		def truncar(x):
			if x < 0:
				return 0
			elif x > 3:
				return 3
			else:
				return x

		def adyacentes(casilla):
			x, y = casilla
			adyacentes = [(truncar(x - 1), y), (truncar(x + 1), y), (x, truncar(y - 1)), (x, truncar(y + 1))]
			adyacentes = [c for c in adyacentes if c != casilla]
			return adyacentes 
    
		casillas = [self.loc] + adyacentes(self.loc)
		for c in casillas:
			x, y = c
			pos = f'en({x},{y})_{self.turno}'
			evaluacion = ASK(pos, 'success', self.base)
			if evaluacion:
				self.loc = (x,y)
				return pos
		raise Exception('¡No se encontró posición!')

	def nueva_direccion(self):
		direcciones = ['o', 'e', 's', 'n']
		for d in direcciones:
			direccion = f'mirando_{d}_{self.turno}'
			evaluacion = ASK(direccion, 'success', self.base)
			if evaluacion:
				return direccion
		raise Exception('¡No se encontró dirección!')
            
	def solo_direccion(self):
		direcciones = ['o', 'e', 's', 'n']
		dir_direcciones = {'o':'oeste', 'e':'este', 's':'sur', 'n':'norte'}
		for d in direcciones:
			direccion = f'mirando_{d}_{self.turno}'
			if direccion in self.base.datos:
				return dir_direcciones[d]
		raise Exception('¡No se encontró dirección!')
            
	def cache(self):
		turno = self.turno
		casilla_actual = self.loc
		direccion = self.solo_direccion()
		cas_seguras = self.adyacentes_seguras()
		cas_seguras = [c for c in cas_seguras if c != casilla_actual]
		cas_visitadas = self.casillas_visitadas()
		cas_visitadas = [tuple([int(s[9]),int(s[11])]) for s in cas_visitadas]
		return turno, casilla_actual, direccion, cas_seguras, cas_visitadas

