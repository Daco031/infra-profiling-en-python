CXX = g++
# -mavx habilita los intrínsecos; -fno-tree-vectorize evita que el compilador
# vectorice por su cuenta el ciclo escalar, para que la comparación sea entre
# el ciclo tal como está escrito y las instrucciones AVX escritas a mano.
FLAGS = -std=c++17 -O2 -mavx -fno-tree-vectorize

producto_punto:
	$(CXX) $(FLAGS) -o producto_punto producto_punto.cpp
	./producto_punto | tee producto_punto.txt
	rm -f producto_punto

limpiar:
	rm -f producto_punto producto_punto.txt
