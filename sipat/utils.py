import os

def caminho_benspermanentes(instance, filename):
    tombamento = instance.tombamento_legado or 'sem_tombo'
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{tombamento}{ext}'
    
    return f'permanentes/{nome_aquivo}'


def caminho_bensconsumo(instance, filename):
    efisco = instance.efisco or 'sem_efisco'
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{efisco}{ext}'
    
    return f'consumo/{nome_aquivo}'