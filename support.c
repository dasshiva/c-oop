void* new_object(void* fn, unsigned long size, ...) {
	void (*construc) (void*) = fn;
	void* space = malloc(size);
	construc(space);
	return space;
}
