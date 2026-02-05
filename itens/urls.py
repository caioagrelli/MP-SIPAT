from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- Rota Principal (Homepage) ---
    path('', views.painel_principal, name='homepage'),
    
    # --- Rota de Login/Logout ---
    path('login/', auth_views.LoginView.as_view(template_name='itens/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # --- Rotas da Área de Gestão ---
    path('painel/', views.painel_principal, name='painel_principal'),
    path('gestao/adicionar/', views.adicionar_item, name='adicionar_item'),
    path('gestao/bloco/adicionar/', views.adicionar_bloco, name='adicionar_bloco'),
    
    # --- Rotas com Parâmetros (Corrigidas para 'numero_id' e 'bloco_id') ---
    path('item/<int:numero_id>/', views.detalhe_item, name='detalhe_item'),
    path('item/<int:numero_id>/ficha-completa/', views.ficha_completa, name='ficha_completa'),
    path('item/<int:numero_id>/movimentar/', views.registrar_movimentacao, name='registrar_movimentacao'),
    path('gestao/item/<int:numero_id>/editar/', views.editar_item, name='editar_item'),
    path('gestao/item/<int:numero_id>/apagar/', views.apagar_item, name='apagar_item'),
    
    # --- Rotas de Lote ---
    path('gestao/lote/<str:lote_id>/apagar/', views.apagar_lote_inteiro, name='apagar_lote_inteiro'),
    path('gestao/apagar-lote/', views.apagar_lote, name='apagar_lote'),
    
    # --- Rotas de Ferramentas (Geradores) ---
    path('item/<int:numero_id>/etiqueta-a4/', views.gerar_etiqueta_a4, name='gerar_etiqueta_a4'),
    path('item/<int:numero_id>/etiqueta-pequena/', views.gerar_etiqueta_pequena, name='gerar_etiqueta_pequena'),
    
    # --- Rotas de Páginas de Categoria ---
    path('bens/ti/', views.pagina_bens_ti, name='pagina_bens_ti'),
    path('bens/permanentes/', views.pagina_bens_permanentes, name='pagina_bens_permanentes'),
    path('bens/consumo/', views.pagina_bens_consumo, name='pagina_bens_consumo'),
    path('bens/moveis/', views.pagina_bens_moveis, name='pagina_bens_moveis'),
    
    # --- Rotas de Setores e Blocos ---
    path('setores/', views.listar_setores, name='listar_setores'),
    path('setor/<int:setor_id>/', views.detalhe_setor, name='detalhe_setor'),
    path('bloco/<int:bloco_id>/', views.detalhe_bloco, name='detalhe_bloco'),
    path('bloco/<int:bloco_id>/qr/', views.gerar_qr_bloco, name='gerar_qr_bloco'),
    path('gestao/bloco/<int:bloco_id>/apagar/', views.apagar_bloco, name='apagar_bloco'),
    path('gestao/requisicoes/', views.requisicoes, name='requisicoes'),
    path('requisicoes/adicionar/', views.adicionar_requisicao, name='adicionar_requisicao'),
    
]