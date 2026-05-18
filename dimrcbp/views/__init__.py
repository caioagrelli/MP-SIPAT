from .homepage             import homepage
from .meus_bens            import meus_bens, detalhe_bem, atualizar_foto, registrar_inventario
from .cadastro_bem         import cadastro_bem
from .filtros_operacionais import filtros_operacionais
from .bem_detalhe_admin    import bem_detalhe_admin
from .qrcode_bem           import qrcode_bem
from .etiqueta_bem         import etiqueta_bem
from .editar_bem           import editar_bem
from .relatorio_mudanca    import relatorio_mudanca
from .atualizar_foto_admin import atualizar_foto_admin
from .catalogo             import (
    catalogo_lista, catalogo_detalhe,
    catalogo_criar, catalogo_editar, catalogo_excluir,
    catalogo_cart_add, catalogo_cart_remove, catalogo_cart_update, catalogo_cart_clear,
    catalogo_checkout,
    minhas_solicitacoes, minhas_solicitacoes_catalogo,
    painel_solicitacoes_catalogo, aprovar_solicitacao_catalogo,
)
from .catalogo_pdf         import catalogo_pdf
from .controle_prazos      import controle_prazos
from .painel_inventario    import painel_inventario, abrir_inventario
from .movimentacao         import (
    lista_solicitacoes,
    criar_solicitacao,
    analisar_solicitacao,
    transferir_bem,
    historico_movimentacoes,
    termo_transferencia,
)
