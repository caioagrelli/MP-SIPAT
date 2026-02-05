# ===================================================================
# 1. IMPORTAÇÕES - Todas as ferramentas que vamos precisar 
# ===================================================================
import qrcode
import io
import zipfile
import gspread
from collections import defaultdict
from django.db import models 
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Value, Q, Sum, F
from django.db.models.functions import Coalesce 
from .models import Item, Bloco, Setor, Movimentacao, Requisicao, ItemRequisitado
from .forms import UnifiedForm, BlocoForm, MovimentacaoForm, ItemRequisitadoForm, RequisicaoForm, ImportarGoogleSheetsForm

from django.http import JsonResponse
from django.db import transaction


def homepage(request):
    return render(request, 'itens/homepage.html')

@login_required
def detalhe_item(request, numero_id):
    """Mostra a página de detalhes de um item específico (acessada pelo QR Code)."""
    item = get_object_or_404(Item, pk=numero_id)
    # Passamos o formulário vazio para a página de detalhes
    form_movimentacao = MovimentacaoForm() 
    
    context = {
        'item': item,
        'form_movimentacao': form_movimentacao
    }
    return render(request, 'itens/detalhe_item.html', context)

@login_required
def painel_principal(request):
    """
    Página principal de gestão (dashboard).
    Mostra os botões de categoria e a lista de itens filtrada.
    """
    # Pega a lista de todos os itens inicialmente
    itens_list = Item.objects.all()

    # --- LÓGICA DE FILTRO POR CATEGORIA ---
    categoria_selecionada = request.GET.get('categoria')
    if categoria_selecionada and categoria_selecionada in ['PERMANENTE', 'CONSUMO', 'TI']:
        itens_list = itens_list.filter(categoria=categoria_selecionada)
    
    # --- LÓGICA DE PESQUISA ---
    
    query = request.GET.get('q')
    if query:
        # A pesquisa agora vai procurar em Tombo, Nome E E-Fisco
        itens_list = itens_list.filter(
            Q(numero_identificacao__icontains=query) | # Busca pelo Tombo
            Q(nome__icontains=query) |                 # Busca pelo Nome
            Q(codigo_efisco__icontains=query)          # Busca pelo E-Fisco
        )

    # --- LÓGICA DE AGRUPAMENTO (continua a mesma) ---
    itens_agrupados = defaultdict(list)
    for item in itens_list.order_by('numero_identificacao'):
        chave_agrupamento = item.lote or "Itens Cadastrados Individualmente"
        itens_agrupados[chave_agrupamento].append(item)
    
    context = {
        'itens_agrupados': dict(itens_agrupados),
        'query': query or "",
        'categoria_selecionada': categoria_selecionada,
        'total_itens': Item.objects.count(), # Para os cards de estatísticas
    }
    
    return render(request, 'itens/painel_principal.html', context)

@login_required
def gestao_itens(request):
# Pega a lista de todos os itens inicialmente
    itens_list = Item.objects.all()

    # --- NOVO: FILTRO DE CATEGORIA ---
    categoria_selecionada = request.GET.get('categoria')
    if categoria_selecionada and categoria_selecionada in ['PERMANENTE', 'CONSUMO', 'TI']:
        itens_list = itens_list.filter(categoria=categoria_selecionada)
    
    # Lógica de Pesquisa (continua a mesma)
    query = request.GET.get('q')
    if query:
        itens_list = itens_list.filter(nome__icontains=query)

    # Lógica de Agrupamento (continua a mesma)
    itens_agrupados = defaultdict(list)
    for item in itens_list.order_by('numero_identificacao'):
        chave_agrupamento = item.lote or "Itens Cadastrados Individualmente"
        itens_agrupados[chave_agrupamento].append(item)
    
    context = {
        'itens_agrupados': dict(itens_agrupados),
        'query': query or "",
        'categoria_selecionada': categoria_selecionada, # Para saber na tela qual categoria está ativa
    }
    
    return render(request, 'itens/gestao_itens.html', context)


@login_required
@permission_required('itens.add_item', raise_exception=True)
@transaction.atomic
def adicionar_item(request):
    if request.method == 'POST':
        form = UnifiedForm(request.POST, request.FILES)
        
        if form.is_valid():
            dados = form.cleaned_data
            tipo_cadastro = dados.get('tipo_cadastro')
            
            # Dicionário base
            dados_item = {
                'nome': dados.get('nome'),
                'categoria': dados.get('categoria'),
                'bloco': dados.get('bloco'),
                'marca': dados.get('marca'),
                'modelo': dados.get('modelo'),
                'valor_unitario': dados.get('valor_unitario'),
                'descricao': dados.get('descricao'),
                'tipo_consumo': dados.get('tipo_consumo'),
                'qtd_estoque': dados.get('qtd_estoque'),
                'validade': dados.get('validade'),
                'numero_de_serie': dados.get('numero_de_serie'),
            }

            try:
                if tipo_cadastro == 'UNICO':
                    # Validação manual: Tombo é obrigatório para único
                    if not dados.get('numero_identificacao'):
                        raise ValueError("O campo Tombo é obrigatório para itens únicos.")

                    novo_item = Item.objects.create(
                        numero_identificacao=dados.get('numero_identificacao'),
                        foto_do_bem=dados.get('foto_do_bem'),
                        **dados_item
                    )
                    messages.success(request, f"Item '{novo_item.nome}' cadastrado!")
                    
                    if request.POST.get('action') == 'cadastrar_gerar':
                        return redirect('gerar_etiqueta_a4', numero_id=novo_item.pk)

                elif tipo_cadastro == 'LOTE':
                    # Validação manual: Início e Fim são obrigatórios para lote
                    if not dados.get('inicio') or not dados.get('fim'):
                        raise ValueError("Início e Fim são obrigatórios para lotes.")
                    
                    inicio = dados.get('inicio')
                    fim = dados.get('fim')
                    nome_base = dados_item.pop('nome') # Remove nome para usar o base
                    
                    # Identificador único do lote
                    lote_id = f"LOTE-{timezone.now().strftime('%Y%m%d%H%M%S')}"

                    for i in range(inicio, fim + 1):
                        Item.objects.create(
                            numero_identificacao=i,
                            nome=f"{nome_base} #{i}",
                            lote=lote_id,
                            **dados_item
                        )
                    messages.success(request, f"Lote de {fim - inicio + 1} itens criado!")

                return redirect('painel_principal')

            except Exception as e:
                messages.error(request, f"Erro ao salvar: {e}")
        
        else:
            # ISSO VAI AJUDAR A DESCOBRIR O ERRO:
            print("ERROS DO FORMULÁRIO:", form.errors) 
            messages.error(request, "Verifique os campos em vermelho.")

    else:
        form = UnifiedForm()

    return render(request, 'itens/adicionar_item_unificado.html', {'form': form})

@login_required
@permission_required('itens.add_item', raise_exception=True)
def adicionar_lote(request):
    if request.method == 'POST':
        form = UnifiedForm(request.POST)
        if form.is_valid():
            bloco_selecionado = form.cleaned_data.get('bloco')
            dados_comuns = {
            'nome_base': form.cleaned_data.get('nome'),
            'descricao': form.cleaned_data.get('descricao'),
            'bloco': bloco_selecionado, # << ADICIONADO AQUI
            # ... todos os outros campos ...
            'lote': f"LOTE-{timezone.now().strftime('%Y%m%d-%H%M%S')}"
            }
            # Pega os dados validados do formulário
            inicio = form.cleaned_data['inicio']
            fim = form.cleaned_data['fim']
            
            # Prepara um dicionário com todos os dados comuns para o lote
            dados_comuns = {
                'nome_base': form.cleaned_data.get('nome'),
                'descricao': form.cleaned_data.get('descricao'),
                'localizacao': form.cleaned_data.get('localizacao'),
                'marca': form.cleaned_data.get('marca'),
                'modelo': form.cleaned_data.get('modelo'),
                'estado_de_conservacao': form.cleaned_data.get('estado_de_conservacao'),
                'valor_unitario': form.cleaned_data.get('valor_unitario'),
                # Adicione todos os outros campos do UnifiedForm aqui
                'codigo_efisco': form.cleaned_data.get('codigo_efisco'),
                'tipo_do_bem': form.cleaned_data.get('tipo_do_bem'),
                'numero_de_serie': form.cleaned_data.get('numero_de_serie'),
                'situacao_juridica': form.cleaned_data.get('situacao_juridica'),
                'situacao_fisica': form.cleaned_data.get('situacao_fisica'),
                'forma_de_ingresso': form.cleaned_data.get('forma_de_ingresso'),
                'numero_do_documento': form.cleaned_data.get('numero_do_documento'),
                'tipo_do_documento': form.cleaned_data.get('tipo_do_documento'),
                'cnpj_fornecedor': form.cleaned_data.get('cnpj_fornecedor'),
                'data_aquisicao': form.cleaned_data.get('data_aquisicao'),
                'garantia_em_dias': form.cleaned_data.get('garantia_em_dias'),
                'centro_de_custo': form.cleaned_data.get('centro_de_custo'),
                'responsavel_ua': form.cleaned_data.get('responsavel_ua'),
                'mat_responsavel_ua': form.cleaned_data.get('mat_responsavel_ua'),
                'observacao': form.cleaned_data.get('observacao'),
                'lote': f"LOTE-{timezone.now().strftime('%Y%m%d-%H%M%S')}"
            }

            # 1. CRIA OS ITENS NO BANCO DE DADOS (acontece para ambos os botões)
            for numero in range(inicio, fim + 1):
                dados_defaults = dados_comuns.copy()
                nome_base = dados_defaults.pop('nome_base') # Remove para não salvar no model
                
                Item.objects.get_or_create(
                    numero_identificacao=numero,
                    defaults={
                        'nome': f"{nome_base} #{numero}",
                        **dados_defaults # Desempacota o resto dos dados
                    }
                )
            
            # --- DECISÃO BASEADA NO BOTÃO CLICADO ---
            action = request.POST.get('action')

            if action == 'cadastrar_gerar':
                # 2. GERA O ARQUIVO ZIP COM OS QR CODES
                buffer = io.BytesIO()
                zip_file = zipfile.ZipFile(buffer, 'w')
                for numero in range(inicio, fim + 1):
                    url = request.build_absolute_uri(f'/item/{numero}/')
                    img = qrcode.make(url)
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, 'PNG')
                    zip_file.writestr(f'item_{numero}.png', img_buffer.getvalue())
                zip_file.close()

                response = HttpResponse(buffer.getvalue(), content_type='application/zip')
                response['Content-Disposition'] = 'attachment; filename=qr_codes_lote.zip'
                return response
            
            elif action == 'cadastrar':
                # Apenas cadastra e volta para a página de gestão com uma mensagem
                quantidade = fim - inicio + 1
                plural = 's' if quantidade > 1 else ''
                messages.success(request, f"{quantidade} item{plural} cadastrado{plural} com sucesso no lote!")
                return redirect('gestao_itens')

        else:
            # ADICIONE ESTA LINHA PARA DESCOBRIR O ERRO
            print("ERROS NO LOTEFORM:", form.errors.as_json())
            

    else: # Se for a primeira visita (GET)
        form = UnifiedForm()
        
    return render(request, 'itens/adicionar_lote.html', {'form': form})

@login_required
@permission_required('itens.change_item', raise_exception=True)
def editar_item(request, numero_id):
    """
    Controla o formulário para editar um item existente.
    """
    item = get_object_or_404(Item, pk=numero_id)
    
    if request.method == 'POST':
        form = UnifiedForm(request.POST, request.FILES) # Validação
        if form.is_valid():
            dados = form.cleaned_data
            
            # Atualiza o item campo por campo
            item.nome = dados.get('nome')
            item.categoria = dados.get('categoria')
            item.bloco = dados.get('bloco')
            item.marca = dados.get('marca')
            item.modelo = dados.get('modelo')
            item.numero_de_serie = dados.get('numero_de_serie')
            item.valor_unitario = dados.get('valor_unitario')
            item.tipo_consumo = dados.get('tipo_consumo')
            item.qtd_estoque = dados.get('qtd_estoque')
            item.validade = dados.get('validade')
            # ... (adicione todos os outros campos aqui) ...
            
            if dados.get('foto_do_bem'):
                item.foto_do_bem = dados.get('foto_do_bem')
            
            item.save()
            messages.success(request, f"Item '{item.nome}' atualizado com sucesso!")
            return redirect('detalhe_item', numero_id=item.pk)
    else:
        # --- CORREÇÃO AQUI ---
        # Converte os dados do item em um dicionário para pré-preencher o formulário
        dados_iniciais = item.__dict__
        # Define o tipo de cadastro (já que estamos editando, é sempre 'UNICO')
        dados_iniciais['tipo_cadastro'] = 'UNICO'
        
        # Em vez de 'instance=item', passamos 'initial=dados_iniciais'
        form = UnifiedForm(initial=dados_iniciais) 
    
    # Precisamos de um template separado para a edição, para que o JS funcione
    return render(request, 'itens/editar_item.html', {'form': form, 'item': item})

@login_required
@permission_required('itens.delete_item', raise_exception=True)
def apagar_item(request, numero_id):
    item = get_object_or_404(Item, pk=numero_id)
    if request.method == 'POST':
        nome_item = item.nome
        item.delete()
        messages.success(request, f"Item '{nome_item}' apagado com sucesso!")
        return redirect('painel_principal')
    return render(request, 'itens/item_confirm_delete.html', {'item': item})

@login_required
@permission_required('itens.delete_item', raise_exception=True)
def apagar_lote(request):
    """Controla a exclusão de múltiplos itens selecionados ou de um lote inteiro."""
    if request.method == 'POST':
        ids_para_apagar = request.POST.getlist('ids_para_apagar')
        if 'confirmar_exclusao' in request.POST:
            quantidade_apagada = len(ids_para_apagar)
            Item.objects.filter(pk__in=ids_para_apagar).delete()
            if quantidade_apagada > 0:
                plural = 's' if quantidade_apagada > 1 else ''
                messages.success(request, f'{quantidade_apagada} item{plural} selecionado{plural} apagado{plural} com sucesso!')
            return redirect('painel_principal')
        else:
            if not ids_para_apagar:
                messages.warning(request, 'Nenhum item foi selecionado para apagar.')
                return redirect('painel_principal')
            itens_para_apagar = Item.objects.filter(pk__in=ids_para_apagar)
            return render(request, 'itens/confirmar_apagar_lote.html', {'itens_para_apagar': itens_para_apagar})
    return redirect('painel_principal')

@login_required
@permission_required('itens.delete_item', raise_exception=True)
def apagar_lote_inteiro(request, lote_id):
    """Controla a exclusão de todos os itens de um mesmo lote."""
    itens_do_lote = Item.objects.filter(lote=lote_id)
    quantidade = itens_do_lote.count()
    if request.method == 'POST':
        itens_do_lote.delete()
        messages.success(request, f"Lote '{lote_id}' com {quantidade} itens foi apagado com sucesso!")
        return redirect('painel_principal')

    return render(request, 'itens/confirmar_apagar_lote.html', {'itens_para_apagar': itens_do_lote})

# --- Views de Sucesso e Ferramentas ---

@login_required
def item_criado_sucesso(request, numero_id):
    """Página de sucesso exibida após cadastrar um item único."""
    item = get_object_or_404(Item, pk=numero_id)
    return render(request, 'itens/item_criado_sucesso.html', {'item': item})

# itens/views.py

@login_required
def gerar_etiqueta_item(request, numero_id):
    # --- 1. Busca os dados ---
    item = get_object_or_404(Item, pk=numero_id)

    # --- 2. Gera o QR Code em memória ---
    url = request.build_absolute_uri(f'/item/{item.numero_identificacao}/')
    qr_img = qrcode.make(url)
    qr_img = qr_img.resize((200, 200))

    # --- 3. Prepara a etiqueta (o canvas) ---
    etiqueta = Image.new('RGB', (800, 400), 'white')
    draw = ImageDraw.Draw(etiqueta)

    # --- 4. Adiciona o Logo (COM O CAMINHO CORRIGIDO) ---
    caminho_logo = settings.BASE_DIR / 'frontend/static/images/brasao_mppe.png' # Removido o .parent
    try:
        logo = Image.open(caminho_logo).convert("RGBA")
        logo = logo.resize((180, 180))
        etiqueta.paste(logo, (50, 110), logo)
    except FileNotFoundError:
        print(f"AVISO: Logo não encontrado em {caminho_logo}.")
        pass

    # --- 5. Adiciona o QR Code ---
    etiqueta.paste(qr_img, (550, 110))

    # --- 6. Adiciona o Nome do Item ---
    texto_nome_item = f"{item.nome.upper()}"
    caminho_fonte_nome = settings.BASE_DIR / 'frontend/static/fonts/arial.ttf' # Removido o .parent
    try:
        fonte_nome = ImageFont.truetype(str(caminho_fonte_nome), 36)
        largura_texto_nome, altura_texto_nome = draw.textbbox((0,0), texto_nome_item, font=fonte_nome)[2:]
        pos_x_nome = (etiqueta.width - largura_texto_nome) / 2
        draw.text((pos_x_nome, 40), texto_nome_item, font=fonte_nome, fill='black')
    except IOError:
        print(f"AVISO DE FONTE: Não foi possível encontrar a fonte em '{caminho_fonte_nome}'.")

    # --- 7. Adiciona o Texto "TOMBO" ---
    texto_tombo = f"TOMBO: {item.numero_identificacao}"
    caminho_fonte_tombo = settings.BASE_DIR / 'frontend/static/fonts/arial.ttf' # Removido o .parent
    try:
        fonte_tombo = ImageFont.truetype(str(caminho_fonte_tombo), 48)
        largura_texto_tombo, altura_texto_tombo = draw.textbbox((0,0), texto_tombo, font=fonte_tombo)[2:]
        pos_x_tombo = (etiqueta.width - largura_texto_tombo) / 2
        draw.text((pos_x_tombo, 320), texto_tombo, font=fonte_tombo, fill='black')
    except IOError:
        print(f"AVISO DE FONTE: Não foi possível encontrar a fonte em '{caminho_fonte_tombo}'.")

    # --- 8. Salva e envia a etiqueta final para download ---
    buffer = io.BytesIO()
    etiqueta.save(buffer, 'PNG')
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename=etiqueta_{item.numero_identificacao}.png'
    return response

@login_required
def ficha_completa(request, numero_id):
    item = get_object_or_404(Item, pk=numero_id)
    return render(request, 'itens/ficha_completa.html', {'item': item})

# itens/views.py

@login_required
def gerar_etiqueta_a4(request, numero_id):
    item = get_object_or_404(Item, pk=numero_id)
    
    # Gera o QR Code
    url = request.build_absolute_uri(f'/item/{item.numero_identificacao}/')
    qr_img = qrcode.make(url).resize((300, 300))

    # Cria a etiqueta (canvas)
    etiqueta = Image.new('RGB', (1000, 500), 'white')
    draw = ImageDraw.Draw(etiqueta)

    # Prepara a fonte
    try:
        caminho_fonte_bold = str(settings.BASE_DIR.parent / 'ROMKRL/frontend/static/fonts/arialbd.ttf')
        fonte_grande = ImageFont.truetype(caminho_fonte_bold, 52)
        fonte_media = ImageFont.truetype(caminho_fonte_bold, 40)
    except IOError:
        fonte_grande = fonte_media = ImageFont.load_default()

    # Adiciona o Logo na esquerda
    try:
        caminho_logo = settings.BASE_DIR.parent / 'ROMKRL/frontend/static/images/brasao_mppe.png'
        logo = Image.open(caminho_logo).convert("RGBA").resize((300, 300))
        etiqueta.paste(logo, (50, 50), logo)
    except FileNotFoundError:
        pass
        
    # Escreve as informações
    draw.text((50, 380), item.nome.upper(), font=fonte_media, fill='black')
    draw.text((50, 430), f"TOMBO: {item.numero_identificacao}", font=fonte_grande, fill='#8B0000')

    # Cola o QR Code na direita
    etiqueta.paste(qr_img, (650, 100))

    # Desenha uma borda
    draw.rectangle([(0,0), (999,499)], outline='black', width=3)

    # Salva e envia para download
    buffer = io.BytesIO()
    etiqueta.save(buffer, 'PNG')
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename=etiqueta_A4_{item.numero_identificacao}.png'
    return response


@login_required
def gerar_etiqueta_pequena(request, numero_id):
    """Gera uma etiqueta pequena e compacta no modelo original."""
    item = get_object_or_404(Item, pk=numero_id)
    
    # Gera o QR Code
    url = request.build_absolute_uri(f'/item/{item.numero_identificacao}/')
    qr_img = qrcode.make(url).resize((200, 200))

    # Cria a etiqueta (canvas)
    etiqueta = Image.new('RGB', (800, 400), 'white')
    draw = ImageDraw.Draw(etiqueta)

    # Prepara a fonte
    try:
        caminho_fonte = str(settings.BASE_DIR.parent / 'ROMKRL/frontend/static/fonts/arial.ttf')
        fonte_tombo = ImageFont.truetype(caminho_fonte, 48)
    except IOError:
        fonte_tombo = ImageFont.load_default()

    # Adiciona o Logo na esquerda
    try:
        caminho_logo = settings.BASE_DIR.parent / 'ROMKRL/frontend/static/images/brasao_mppe.png'
        logo = Image.open(caminho_logo).convert("RGBA").resize((200, 200))
        etiqueta.paste(logo, (50, 80), logo)
    except FileNotFoundError:
        pass
        
    # Adiciona o QR Code na direita
    etiqueta.paste(qr_img, (550, 80))

    # Adiciona o texto "TOMBO" embaixo, centralizado
    texto_tombo = f"TOMBO: {item.numero_identificacao}"
    largura_texto_tombo, altura_texto_tombo = draw.textbbox((0,0), texto_tombo, font=fonte_tombo)[2:]
    pos_x_tombo = (etiqueta.width - largura_texto_tombo) / 2
    draw.text((pos_x_tombo, 320), texto_tombo, font=fonte_tombo, fill='black')

    # Salva e envia para download
    buffer = io.BytesIO()
    etiqueta.save(buffer, 'PNG')
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename=etiqueta_pequena_{item.numero_identificacao}.png'
    return response


@login_required
def pagina_bens_ti(request):
    context = {}
    return render(request, 'itens/pagina_bens_ti.html', context)

@login_required
def pagina_bens_permanentes(request):
    context = {}
    return render(request, 'itens/pagina_bens_permanentes.html', context)

@login_required
def pagina_bens_consumo(request):
    context = {}
    return render(request, 'itens/pagina_bens_consumo.html', context)

@login_required
def pagina_bens_moveis(request):
    """Página provisória para listar os Bens Móveis."""
    context = {}
    return render(request, 'itens/pagina_bens_moveis.html', context)


@login_required
def pagina_bens_consumo(request):
    itens_list = Item.objects.filter(categoria='CONSUMO')

    query = request.GET.get('q')
    if query:
        itens_list = itens_list.filter(
            Q(nome__icontains=query) |
            Q(descricao__icontains=query) |
            Q(numero_identificacao__icontains=query)
        )

    # ======================================================
    #           LÓGICA PARA OS NOVOS GRÁFICOS
    # ======================================================

    dados_tipo_qtde = itens_list.annotate(
        tipo_final=Coalesce('tipo_consumo', Value('Não Informado'))
    ).values('tipo_final').annotate(
        quantidade=Count('pk')
    ).order_by('-quantidade')

    dados_tipo_valor = itens_list.annotate(
        tipo_final=Coalesce('tipo_consumo', Value('Não Informado'))
    ).values('tipo_final').annotate(
        valor_total=Sum(F('valor_aquisicao') * F('qtde'), output_field=models.DecimalField())
    ).order_by('-valor_total')

    # --- GRÁFICO 3: Visão Geral de Todas as Categorias ---
    # Esta consulta é feita no modelo Item *sem filtro* para pegar todos os itens do inventário.
    dados_categorias_geral = Item.objects.values('categoria').annotate(
        quantidade=Count('pk')
    ).order_by('categoria')


    # 4. Prepara o "pacote" de dados (context) para enviar para o template
    context = {
        'itens': itens_list.order_by('nome'),
        'total_itens': itens_list.count(),
        'query': query or "",
        
        # Dados para o Gráfico 1 (Quantidade por Tipo)
        'labels_tipo_qtde': [item['tipo_final'] for item in dados_tipo_qtde],
        'data_tipo_qtde': [item['quantidade'] for item in dados_tipo_qtde],

        # Dados para o Gráfico 2 (Valor por Tipo)
        'labels_tipo_valor': [item['tipo_final'] for item in dados_tipo_valor],
        # Converte o Decimal para float para o Chart.js ler corretamente
        'data_tipo_valor': [float(item['valor_total']) for item in dados_tipo_valor],
        
        # Dados para o Gráfico 3 (Todas as Categorias)
        'labels_categorias_geral': [item['categoria'] for item in dados_categorias_geral],
        'data_categorias_geral': [item['quantidade'] for item in dados_categorias_geral],
    }
    
    return render(request, 'itens/pagina_bens_consumo.html', context)

@login_required
def detalhe_bloco(request, bloco_id): # 1. Renomeamos o parâmetro
    bloco = get_object_or_404(Bloco, pk=bloco_id) # 2. Buscamos pela chave primária (pk)
    itens_no_bloco = Item.objects.filter(bloco=bloco)
    context = {
        'bloco': bloco,
        'itens': itens_no_bloco,
    }
    return render(request, 'itens/detalhe_bloco.html', context)

@login_required
def apagar_bloco(request, bloco_id):
    bloco = get_object_or_404(Bloco, pk=bloco_id)
    setor_id_para_redirect = bloco.setor.id  # Salva o ID do setor antes de apagar

    if request.method == 'POST':
        nome_bloco = bloco.nome
        bloco.delete()
        messages.success(request, f"Bloco '{nome_bloco}' apagado com sucesso.")
        return redirect('detalhe_setor', setor_id=setor_id_para_redirect)
    
    context = {
        'bloco': bloco
    }
    return render(request, 'itens/bloco_confirm_delete.html', context)


def listar_setores(request):
    """Mostra uma lista de todos os setores."""
    setores = Setor.objects.all()
    return render(request, 'itens/listar_setores.html', {'setores': setores})

def detalhe_setor(request, setor_id):

    setor = get_object_or_404(Setor, pk=setor_id)
    blocos_no_setor = setor.blocos.all()

    query = request.GET.get('q')
    if query:
        blocos_no_setor = blocos_no_setor.filter(nome__icontains=query)
    context = {
        'setor': setor,
        'blocos': blocos_no_setor.order_by('nome'), 
        'query': query or "" 
    }
    return render(request, 'itens/detalhe_setor.html', {'setor': setor, 'blocos': blocos_no_setor})


def gerar_qr_bloco(request, bloco):
    url = request.build_absolute_uri(f'/bloco/{bloco.id}/') 

    img = qrcode.make(url)
    buffer = io.BytesIO()
    img.save(buffer, 'PNG')
    response = HttpResponse(buffer.getvalue(), content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename=qr_bloco_{bloco.nome}.png'
    return response

def carregar_blocos(request):
    setor_id = request.GET.get('setor_id')
    # Filtra os blocos que pertencem ao setor recebido
    blocos = Bloco.objects.filter(setor_id=setor_id).order_by('nome')
    # Constrói uma lista de dicionários para a resposta JSON
    blocos_list = list(blocos.values('id', 'nome'))
    return JsonResponse(blocos_list, safe=False)

@login_required
def adicionar_bloco(request):
    if request.method == 'POST':
        form = BlocoForm(request.POST)
        if form.is_valid():
            novo_bloco = form.save()
            messages.success(request, f"Bloco '{novo_bloco.nome}' adicionado com sucesso!")
            return redirect('detalhe_setor', setor_id=novo_bloco.setor.id)
    else:
        form = BlocoForm()
    
    return render(request, 'itens/adicionar_bloco.html', {'form': form})

@login_required
@transaction.atomic
def registrar_movimentacao(request, numero_id):
    item = get_object_or_404(Item, pk=numero_id)
    
    if request.method == 'POST':
        form = MovimentacaoForm(request.POST, request.FILES)
        
        if form.is_valid():
            quantidade = form.cleaned_data['quantidade']
            observacao = form.cleaned_data['observacao']
            documento = form.cleaned_data.get('documento_pdf')
            
            tipo_mov = None
            if 'saida' in request.POST:
                tipo_mov = 'SAIDA'
                if quantidade > item.qtde:
                    messages.error(request, f"Retirada falhou. Estoque insuficiente: {item.qtde} un.")
                    return redirect('detalhe_item', numero_id=item.pk) # <-- CORRIGIDO para numero_id
                item.qtde -= quantidade
            
            elif 'entrada' in request.POST:
                tipo_mov = 'ENTRADA'
                item.qtde += quantidade
            
            if tipo_mov:
                item.save()
                
                Movimentacao.objects.create(
                    item=item,
                    tipo=tipo_mov,
                    quantidade=quantidade,
                    usuario=request.user,
                    observacao=observacao,
                    documento_pdf=documento
                )
                messages.success(request, f"{tipo_mov.capitalize()} de {quantidade} un. registrada com sucesso!")
            
            else:
                messages.warning(request, "Nenhuma ação (Entrada ou Saída) foi selecionada.")
        
        else:
            messages.error(request, f"Erro no formulário: {form.errors.as_text()}")
            
    return redirect('detalhe_item', numero_id=item.pk)

@login_required
def requisicoes(request):
    """
    Renderiza a PÁGINA PRINCIPAL de Requisições,
    agora com a LISTA de todas as requisições.
    """
    # Busca todas as requisições do banco de dados
    lista_de_requisicoes = Requisicao.objects.all()
    
    context = {
        'requisicoes': lista_de_requisicoes
    }
    return render(request, 'itens/requisicoes.html', context)

@login_required
def adicionar_requisicao(request):
    if request.method == 'POST':
        form = RequisicaoForm(request.POST)
        if form.is_valid():
            nova_requisicao = form.save(commit=False)
            nova_requisicao.requisitante = request.user 
            nova_requisicao.save() 
            messages.success(request, 'Requisição enviada com sucesso!')
            return redirect('requisicoes') 
    else:
        form = RequisicaoForm()

    context = {
        'form': form
    }
    return render(request, 'itens/adicionar_requisicao.html', context)