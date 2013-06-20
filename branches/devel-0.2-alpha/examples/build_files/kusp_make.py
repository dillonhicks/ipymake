
import ipymake.textstyle as style


clean:
    build_subdir('subsystems', 'build_subsystems.py', target='clean_subsystems')


all:
    print style.intense_black_text('='*80)
    print 
    print style.bold_text('                           KUSP IPYMAKE TESTING')
    print 
    print style.intense_black_text('='*80)
    build_subdir('subsystems', 'build_subsystems.py')
    pass


