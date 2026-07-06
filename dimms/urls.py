# Importações do Django
from django.urls import path

# Importações do códigp
from .views import *

# =================================
# URL'S DA DIMMS (BENS DE CONSUMO)
# =================================



app_name = 'dimms'

urlpatterns = [
    # Url's da Homepage e Páginas de Aviso
    path('', homepage, name='homepage'),
    path('exportar-planilha/', exportar_planilha, name='exportar_planilha'),
    path('essential/', essential, name='essential'),
    path('low_stock/', low_stock, name='low_stock'),
    path('expiration_alert/', expiration_alert, name='expiration_alert'),
    
    
    # Url's do detalhamento de cada bem
    path('overview/<int:pk>/', overview, name='overview'),
    path('overview/<int:pk>/qrcode/', qrcode_view, name='qrcode'),
    path('overview/<int:pk>/label/', label, name='label'),
    path('overview/<int:pk>/ficha-tecnica/', ficha_tecnica, name='ficha_tecnica'),
    path('overview/<int:pk>/edit/', overview_edit, name='overview_edit'),
    

    # Url's de Solicitações
    path('processing/', processing, name='processing'),
    path('processing/<int:pk>/', details_processing, name='details_processing'),
    path('processing/create_request/', create_request, name='create_request'), 
    path('processing/create_update/',create_update,name= 'create_update'),
    path('processing/<int:pk>/update_request/', update_request, name='update_request'),
    path('processing/<int:pk>/update_request/qrcode/', qrcode_update, name='qrcode_update'),
    path('processing/<int:pk>/update_request/label/', label_update, name='label_update'),
    path('processing/<int:solicitacao_pk>/course/<int:tramitacao_pk>/', course, name='course'),
    path('processing/<int:solicitacao_pk>/course/<int:tramitacao_pk>/comprovante/', comprovante_tramitacao, name='comprovante_tramitacao'),
    path('processing/<int:pk>/pdf/', pdf_solicitacao, name='pdf_solicitacao'),
    path('processing/parse-guia-remessa/', parse_guia_remessa, name='parse_guia_remessa'),
    path('processing/<int:pk>/edit-itens/', edit_solicitacao_itens, name='edit_solicitacao_itens'),
    
    
    
    # Busca de E-Fisco (autocomplete)
    path('efisco/search/', efisco_search, name='efisco_search'),

    # Busca de item do Estoque por E-Fisco (autocomplete nas solicitações)
    path('estoque/search/', estoque_search, name='estoque_search'),

    # Url's dos Artefatos e das Propostas
    path('artifacts/', artifacts, name='artifacts'),
    path('artifacts/<int:pk>/', artifacts_details, name='artifacts_details'),
    path('artifacts/<int:pk>/edit', artifacts_edit, name='artifacts_edit'),
    path('artifacts/<int:pk>/new/', artifacts_add, name='artifacts_add'),
    path('artifacts/<int:pk>/documents/', artifacts_documents, name='artifacts_documents'),
    path('artifacts/new/', artifacts_create, name='artifacts_create'),
    path('proposals/<int:pk>/', proposal_details, name='proposal_details'),
    path('proposal/<int:pk>/status/', proposal_status, name='proposal_item_update_status'),
    path('artifacts/<int:pk>/proposal/create/', proposal_create, name='proposal_create'),
    path('proposals/<int:pk>/item/add/', proposal_item_add, name='proposal_item_add'),
    path('proposals/item/<int:pk>/delete/', proposal_item_delete, name='proposal_item_delete'),
    path('proposals/<int:pk>/contrato/', contrato_create, name='contrato_create'),
    path('contrato/<int:pk>/', contrato_detail, name='contrato_detail'),
    path('contrato/<int:contrato_pk>/saldo/gerar/<int:proposal_pk>/', contrato_gerar_saldo, name='contrato_gerar_saldo'),


    # Url's do Saldo Ativo
    path('saldo-ativo/', saldo_ativo_homepage, name='saldo_ativo_homepage'),
    path('saldo-ativo/contrato/criar/', contrato_criar_saldoativo, name='contrato_criar_saldoativo'),
    path('saldo-ativo/fornecedores/', fornecedor_lista, name='fornecedor_lista'),
    path('saldo-ativo/fornecedor/<int:pk>/', fornecedor_detail, name='fornecedor_detail'),
    path('saldo-ativo/fornecedor/buscar/', fornecedor_search, name='fornecedor_search'),
    path('saldo-ativo/fornecedor/criar/', fornecedor_criar_saldoativo, name='fornecedor_criar_saldoativo'),
    path('saldo-ativo/solicitacoes/', saldo_ativo_solicitacoes, name='saldo_ativo_solicitacoes'),
    path('saldo-ativo/solicitacao/criar/', saldo_ativo_solicitacao_create, name='saldo_ativo_solicitacao_create'),
    path('saldo-ativo/solicitacao/<int:pk>/', saldo_ativo_solicitacao_detail, name='saldo_ativo_solicitacao_detail'),
    path('saldo-ativo/envio/<int:item_pk>/', saldo_ativo_confirmar_envio, name='saldo_ativo_confirmar_envio'),
    path('saldo-ativo/remessa/<int:remessa_pk>/receber/', saldo_ativo_confirmar_recebimento, name='saldo_ativo_confirmar_recebimento'),
    path('saldo-ativo/solicitacao/<int:pk>/pdf/', pdf_relatorio_solicitacao, name='pdf_relatorio_solicitacao'),
    path('saldo-ativo/relatorio/recebimentos/', relatorio_recebimentos, name='relatorio_recebimentos'),


    # Catálogo de Bens de Consumo — listagem pública
    path('catalogo/', catalogo_consumo_lista, name='catalogo_consumo'),

    # Catálogo de Bens de Consumo — gestão (admin)
    path('catalogo/admin/',                      catalogo_consumo_admin_lista, name='catalogo_consumo_admin'),
    path('catalogo/admin/novo/',                 catalogo_consumo_criar,       name='catalogo_consumo_criar'),
    path('catalogo/admin/<int:pk>/editar/',      catalogo_consumo_editar,      name='catalogo_consumo_editar'),
    path('catalogo/admin/<int:pk>/excluir/',     catalogo_consumo_excluir,     name='catalogo_consumo_excluir'),

    # Catálogo — solicitações
    path('catalogo/minhas-solicitacoes/',        minhas_solicitacoes_consumo,     name='minhas_solicitacoes_consumo'),
    path('catalogo/aprovacao/',                  painel_solicitacoes_consumo,     name='painel_solicitacoes_consumo'),
    path('catalogo/aprovacao/<int:pk>/',         analisar_solicitacao_consumo,    name='analisar_solicitacao_consumo'),

    # Url's das Ações no estoque
    path('stock_add/', stock_add, name='stock_add'),
    path('stock_up/', stock_up, name='stock_up'),
    path('bensconsumo/', bensconsumo, name='bensconsumo'),
    path('bensconsumo/add/', bensconsumo_add, name='bensconsumo_add'),
    path('bensconsumo/<int:pk>/edit/', bensconsumo_edit, name='bensconsumo_edit'),
    path('bensconsumo/<int:pk>/delete/', bensconsumo_delete, name='bensconsumo_delete'),
    path('bensconsumo/recalcular-consumo/', recalcular_consumo_view, name='recalcular_consumo'),
    ]

