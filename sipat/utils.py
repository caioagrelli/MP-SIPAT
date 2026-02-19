import os

def caminho_benspermanentes(instance, filename):
    tombamento = instance.tombamento_legado or 'sem_tombo'
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{tombamento}{ext}'
    
    return f'bens/permanentes/{nome_aquivo}'


def caminho_bensconsumo(instance, filename):
    n_efisco = instance.efisco or 'sem_efisco'
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{n_efisco}{ext}'
    
    return f'bens/consumo/{nome_aquivo}'

def caminho_movimentacao_consumo(instance, filename):
    n_movimentacao = instance.id
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{n_movimentacao}{ext}'
    
    return f'documentos/movimentacao_consumo/{nome_aquivo}'

def caminho_nf_compraindividual(instance, filename):
    n_nf = instance.id
    ext = os.path.splitext(filename)[1]
    nome_aquivo = f'{n_nf}{ext}'
    
    return f'documentos/nf_individual/{nome_aquivo}'