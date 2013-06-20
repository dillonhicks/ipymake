all:
	cd regression; mkdir build; cd build;\
	cmake ..; make ; \
	make -f test.mk

clean: 
	cd regression; make -f test.mk clean
	rm -f *.out
