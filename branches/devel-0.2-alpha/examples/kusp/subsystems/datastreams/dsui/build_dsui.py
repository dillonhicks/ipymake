libdsui:
    libdsui_files = [
        'dstrm_buffer.c', 
        'dstrm_buffer.h', 
        'buffer_thread.c', 
        'buffer_thread.h', 	
        'logging_thread.c', 
        'logging_thread.h',
        'pool.c',
        'pool.h',
        'buffer_queue.c',
        'buffer_queue.h', 
        'dsui.c',
        'filters.h',
        'filters.c', 
        'entity.c',
        'entity.h', 
        'datastream.c',
        'datastream.h',
        'clksyncapi.c',
        'dstream_header.c',
        'log_functions.c' ]
    libdsui_files = filter(lambda s: not s.endswith('.h'), libdsui_files)
    libdsui_files = map(lambda s: './libdsui/'+s, libdsui_files)
    compile_static_library('dsui', include_dirs=['libdsui', '../include', '../../common/include'], *libdsui_files)
    pass


all: libdsui
    print 'HELLO WORLD'
    pass
