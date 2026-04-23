"""
BSB Contabilidade - Plataforma de Cadastro Inteligente
Visual Pulse (azul) + estrutura de wizard preservada.
"""

import streamlit as st
import requests
import re
from datetime import datetime
from typing import Dict, Any

# =============================================================================
# CONFIGURAÇÃO DA PÁGINA
# =============================================================================
st.set_page_config(
    page_title="BSB Contabilidade | Cadastro",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =============================================================================
# CSS PULSE AZUL — Navy dark + blue accents
# =============================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    * { font-family: 'Inter', sans-serif !important; }

    /* Background e base */
    .stApp {
        background: linear-gradient(135deg, #0b1e2e 0%, #0f172a 100%);
        color: #f1f5f9;
    }
    .block-container {
        max-width: 520px !important;
        padding: 2rem 1rem 1rem 1rem !important;
    }

    /* Título principal estilo "Pulse" */
    .bsb-logo {
        font-size: 3.4rem;
        font-weight: 900;
        letter-spacing: -0.04em;
        background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 50%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 0;
        filter: drop-shadow(0 0 20px rgba(59,130,246,0.4));
    }
    .bsb-slogan {
        text-align: center;
        color: #94a3b8;
        font-weight: 500;
        font-size: 0.95rem;
        margin-top: 0.2rem;
    }

    h1, h2, h3, .stSubheader {
        color: #e2e8f0;
        font-weight: 600;
    }

    /* Cards (containers, forms) */
    .stContainer, div[data-testid="stExpander"], div[data-testid="stForm"] {
        background: linear-gradient(135deg, #1a2e42 0%, #243b54 100%);
        border: 1px solid #334155;
        border-radius: 18px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.5);
        padding: 20px;
        backdrop-filter: blur(10px);
    }

    /* Botões */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 1.2rem;
        font-weight: 700;
        font-size: 0.95rem;
        width: 100%;
        box-shadow: 0 4px 12px rgba(59,130,246,0.4);
        transition: all 0.2s ease;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(59,130,246,0.6);
    }
    .stButton > button[kind="secondary"] {
        background: rgba(26,46,66,0.7);
        border: 1px solid #475569;
        color: #cbd5e1;
        box-shadow: none;
    }
    .stButton > button[kind="secondary"]:hover {
        background: #334155;
        border-color: #3b82f6;
    }

    /* Campos */
    input, textarea, select, .stNumberInput input, div[data-baseweb="input"] > div {
        background: #0f172a !important;
        border: 1px solid #334155 !important;
        color: #f1f5f9 !important;
        border-radius: 10px !important;
    }
    input:focus, textarea:focus, select:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 12px rgba(59,130,246,0.5) !important;
    }

    /* Radio e checkbox */
    .stRadio > div, .stCheckbox > label { color: #cbd5e1 !important; }

    /* Progress bar */
    .stProgress > div > div {
        background: linear-gradient(90deg, #2563eb, #3b82f6);
    }

    /* LGPD box estilo Pulse info-box */
    .lgpd-box {
        background: linear-gradient(135deg, rgba(59,130,246,0.08) 0%, rgba(6,182,212,0.05) 100%);
        border-left: 3px solid #3b82f6;
        padding: 12px 16px;
        border-radius: 12px;
        color: #cbd5e1;
        font-size: 0.85rem;
        margin-bottom: 20px;
    }

    /* Etapas / Tabs (se usar) */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; background: transparent; }
    .stTabs [data-baseweb="tab"] {
        background: #1a2e42; border: 1px solid #334155; border-radius: 10px;
        padding: 0.5rem 0.8rem; font-weight: 500; font-size: 0.72rem; color: #94a3b8 !important;
    }
    .stTabs [data-baseweb="tab"]:hover { background: #243b54; color: #f1f5f9 !important; }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
        color: white !important; border-color: #3b82f6 !important;
        box-shadow: 0 2px 12px rgba(59,130,246,0.4); font-weight: 700 !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #0b1e2e; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #3b82f6; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# INICIALIZAÇÃO DO ESTADO DA SESSÃO
# =============================================================================
def init_session_state():
    defaults = {
        'step': 0,
        'perfil': None,
        'dados_cadastrais': {},
        'dados_operacionais': {},
        'documentos': [],
        'honorario_interno': 0.0,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# =============================================================================
# APIs
# =============================================================================
@st.cache_data(ttl=600, show_spinner=False)
def consulta_cnpj(cnpj: str) -> Dict[str, Any]:
    cnpj_clean = re.sub(r'\D', '', cnpj)
    if len(cnpj_clean) != 14:
        return None
    url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_clean}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except:
        return None

@st.cache_data(ttl=600, show_spinner=False)
def consulta_cep(cep: str) -> Dict[str, Any]:
    cep_clean = re.sub(r'\D', '', cep)
    if len(cep_clean) != 8:
        return None
    url = f"https://brasilapi.com.br/api/cep/v1/{cep_clean}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except:
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def consulta_cnae(codigo: str) -> str:
    if not codigo: return ""
    codigo_clean = re.sub(r'\D', '', codigo)
    url = f"https://brasilapi.com.br/api/cnae/v1/{codigo_clean}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get('descricao', 'CNAE não encontrado')
    except:
        return "Descrição não disponível"

# =============================================================================
# CÁLCULO DE HONORÁRIOS (INTERNO, OCULTO)
# =============================================================================
def calcular_honorario_pj(dados):
    regime = dados.get('regime', 'Simples Nacional')
    fat = float(dados.get('faturamento', 0))
    notas = int(dados.get('num_notas', 0))
    func = dados.get('tem_funcionarios', False)
    est = dados.get('tem_estoque', False)
    sit = dados.get('situacao_fiscal', 'regular')
    base = {'MEI':150, 'Simples Nacional':600, 'Lucro Presumido':1200, 'Lucro Real':2200}
    b = base.get(regime, 600)
    if fat<=10000: f=0.8
    elif fat<=30000: f=1.0
    elif fat<=100000: f=1.4
    elif fat<=300000: f=1.8
    else: f=2.5
    add = (notas//20)*80 + (250 if func else 0) + (200 if est else 0)
    irreg = 1.3 if sit=='irregular' else 1.0
    return round((b*f + add)*irreg, 2)

def calcular_honorario_pf(dados):
    renda = float(dados.get('renda_mensal', 0))
    bens = dados.get('possui_bens', False)
    invest = dados.get('possui_investimentos', False)
    base = 200
    f = 1.0 if renda<=5000 else (1.5 if renda<=15000 else 2.0)
    extras = (100 if bens else 0) + (150 if invest else 0)
    return round(base*f + extras, 2)

# =============================================================================
# VALIDAÇÕES
# =============================================================================
def validar_cnpj(cnpj): return len(re.sub(r'\D','',cnpj))==14
def validar_cpf(cpf): return len(re.sub(r'\D','',cpf))==11

# =============================================================================
# INTERFACE PRINCIPAL
# =============================================================================
def main():
    # Título estilo Pulse
    st.markdown('<div class="bsb-logo">BSB Contabilidade</div>', unsafe_allow_html=True)
    st.markdown('<div class="bsb-slogan">Inteligência fiscal para acelerar seu futuro.</div>', unsafe_allow_html=True)
    st.markdown("---")

    # Saudação
    st.markdown("""
    <div style="font-size:1rem; margin: 10px 0; color: #e2e8f0;">
        Seja bem-vindo(a)! Pra que possamos proceder com seu processo, favor preencher as informações cadastrais.
    </div>
    """, unsafe_allow_html=True)

    # LGPD
    st.markdown("""
    <div class="lgpd-box">
        🔒 <strong>Segurança e Privacidade (LGPD):</strong> Seus dados estão protegidos pela Lei Geral de Proteção de Dados.
        Todas as informações fornecidas são confidenciais e serão utilizadas exclusivamente para elaboração de proposta de serviços contábeis.
        Não compartilhamos seus dados com terceiros.
    </div>
    """, unsafe_allow_html=True)

    progresso = st.progress(st.session_state.step / 3)

    if st.session_state.step == 0:
        etapa_selecao_perfil()
    elif st.session_state.step == 1:
        etapa_dados_cadastrais()
    elif st.session_state.step == 2:
        etapa_dados_operacionais()
    elif st.session_state.step == 3:
        etapa_upload()
    elif st.session_state.step == 4:
        etapa_sucesso()

    progresso.progress(st.session_state.step / 4)

# =============================================================================
# ETAPA 0: SELEÇÃO DE PERFIL
# =============================================================================
def etapa_selecao_perfil():
    st.header("Nova Proposta")
    st.subheader("Para começarmos, selecione o tipo de cliente:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏢 PESSOA JURÍDICA", use_container_width=True):
            st.session_state.perfil = 'PJ'
            st.session_state.step = 1
            st.rerun()
    with col2:
        if st.button("👤 PESSOA FÍSICA", use_container_width=True):
            st.session_state.perfil = 'PF'
            st.session_state.step = 1
            st.rerun()

# =============================================================================
# ETAPA 1: DADOS CADASTRAIS
# =============================================================================
def etapa_dados_cadastrais():
    st.header("📋 Dados Cadastrais")
    perfil = st.session_state.perfil

    with st.container():
        if perfil == 'PJ':
            st.subheader("Dados da Empresa")
            col1, col2 = st.columns(2)
            with col1:
                cnpj_input = st.text_input("CNPJ", placeholder="00.000.000/0000-00", key='cnpj_input')
                if st.button("🔍 Consultar CNPJ", type="secondary"):
                    if validar_cnpj(cnpj_input):
                        with st.spinner("Conectando ao servidor da Receita..."):
                            dados = consulta_cnpj(cnpj_input)
                            if dados:
                                st.session_state.dados_cadastrais.update({
                                    'cnpj': cnpj_input,
                                    'razao_social': dados.get('razao_social',''),
                                    'nome_fantasia': dados.get('nome_fantasia',''),
                                    'natureza_juridica': dados.get('natureza_juridica',{}).get('descricao',''),
                                    'cnae_principal': dados.get('cnae_fiscal_descricao',''),
                                    'cnae_codigo': dados.get('cnae_fiscal',''),
                                    'cep': dados.get('cep',''),
                                    'logradouro': dados.get('logradouro',''),
                                    'bairro': dados.get('bairro',''),
                                    'municipio': dados.get('municipio',''),
                                    'uf': dados.get('uf','')
                                })
                                if not dados.get('cnae_fiscal_descricao') and dados.get('cnae_fiscal'):
                                    st.session_state.dados_cadastrais['cnae_principal'] = consulta_cnae(dados.get('cnae_fiscal'))
                                st.success("Empresa localizada!")
                                st.rerun()
                            else:
                                st.error("CNPJ inválido ou não encontrado.")
                    else:
                        st.error("CNPJ deve ter 14 dígitos.")

            dados = st.session_state.dados_cadastrais
            with col1:
                razao_social = st.text_input("Razão Social*", value=dados.get('razao_social',''))
                nome_fantasia = st.text_input("Nome Fantasia", value=dados.get('nome_fantasia',''))
                natureza_juridica = st.text_input("Natureza Jurídica", value=dados.get('natureza_juridica',''))
                cnae_principal = st.text_input("CNAE Principal", value=dados.get('cnae_principal',''))
            with col2:
                cep_input = st.text_input("CEP", value=dados.get('cep',''), key='cep_input')
                if st.button("📍 Buscar CEP"):
                    if len(re.sub(r'\D','',cep_input))==8:
                        ender = consulta_cep(cep_input)
                        if ender:
                            st.session_state.dados_cadastrais.update({
                                'cep': cep_input,
                                'logradouro': ender.get('street',''),
                                'bairro': ender.get('neighborhood',''),
                                'municipio': ender.get('city',''),
                                'uf': ender.get('state','')
                            })
                            st.rerun()
                    else:
                        st.error("CEP inválido.")
                logradouro = st.text_input("Logradouro", value=dados.get('logradouro',''))
                bairro = st.text_input("Bairro", value=dados.get('bairro',''))
                municipio = st.text_input("Município", value=dados.get('municipio',''))
                uf = st.text_input("UF", value=dados.get('uf',''), max_chars=2)

            st.session_state.dados_cadastrais.update({
                'cnpj': cnpj_input, 'razao_social':razao_social,
                'nome_fantasia':nome_fantasia, 'natureza_juridica':natureza_juridica,
                'cnae_principal':cnae_principal, 'cep':cep_input,
                'logradouro':logradouro, 'bairro':bairro, 'municipio':municipio, 'uf':uf
            })
        else:  # PF
            st.subheader("Dados da Pessoa Física")
            col1, col2 = st.columns(2)
            with col1:
                cpf = st.text_input("CPF*", placeholder="000.000.000-00", key='cpf')
                nome = st.text_input("Nome Completo*", key='nome')
                data_nasc = st.date_input("Data de Nascimento")
            with col2:
                cep = st.text_input("CEP", key='cep_pf')
                if st.button("📍 Buscar CEP", key='buscar_cep_pf'):
                    if len(re.sub(r'\D','',cep))==8:
                        ender = consulta_cep(cep)
                        if ender:
                            st.session_state.dados_cadastrais.update({
                                'cep': cep,
                                'logradouro': ender.get('street',''),
                                'bairro': ender.get('neighborhood',''),
                                'municipio': ender.get('city',''),
                                'uf': ender.get('state','')
                            })
                            st.rerun()
                    else:
                        st.error("CEP inválido.")
                logradouro = st.text_input("Logradouro", key='logradouro_pf')
                bairro = st.text_input("Bairro", key='bairro_pf')
                municipio = st.text_input("Município", key='municipio_pf')
                uf = st.text_input("UF", max_chars=2, key='uf_pf')

            st.session_state.dados_cadastrais.update({
                'cpf': cpf, 'nome': nome,
                'data_nascimento': data_nasc.strftime('%d/%m/%Y') if data_nasc else '',
                'cep': cep, 'logradouro': logradouro, 'bairro': bairro,
                'municipio': municipio, 'uf': uf
            })

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("⬅ Voltar", use_container_width=True):
                st.session_state.step = 0
                st.rerun()
        with col_btn2:
            if st.button("Próximo ➡", type="primary", use_container_width=True):
                if perfil == 'PJ' and not validar_cnpj(st.session_state.dados_cadastrais.get('cnpj','')):
                    st.error("CNPJ obrigatório e deve ter 14 dígitos.")
                elif perfil == 'PF' and (not validar_cpf(st.session_state.dados_cadastrais.get('cpf','')) or not nome):
                    st.error("CPF e Nome são obrigatórios.")
                else:
                    st.session_state.step = 2
                    st.rerun()

# =============================================================================
# ETAPA 2: DADOS OPERACIONAIS
# =============================================================================
def etapa_dados_operacionais():
    st.header("📊 Configuração Fiscal")
    perfil = st.session_state.perfil
    if not st.session_state.dados_operacionais:
        st.session_state.dados_operacionais = {}

    with st.form(key='form_operacional'):
        if perfil == 'PJ':
            regime = st.selectbox("Regime Tributário*", ["Simples Nacional","Lucro Presumido","Lucro Real","MEI"])
            faturamento = st.number_input("Faturamento médio mensal (R$)*", min_value=0.0, step=1000.0)
            num_notas = st.number_input("Notas fiscais emitidas por mês*", min_value=0, step=1)
            tem_funcionarios = st.checkbox("Possui funcionários?")
            tem_estoque = st.checkbox("Controle de estoque?")
            situacao_fiscal = st.radio("Situação fiscal*", ["Em dia", "Com pendências"])
            contato_nome = st.text_input("Nome do responsável*")
            contato_email = st.text_input("E-mail*")
            contato_telefone = st.text_input("Telefone")
            expectativa = st.selectbox("Início desejado", ["Imediato", "Próximo mês", "Em até 3 meses"])
            submitted = st.form_submit_button("Avançar ➡", use_container_width=True)
            if submitted:
                if not contato_nome or not contato_email:
                    st.error("Nome e e-mail são obrigatórios.")
                else:
                    st.session_state.dados_operacionais = {
                        'regime': regime, 'faturamento': faturamento,
                        'num_notas': num_notas, 'tem_funcionarios': tem_funcionarios,
                        'tem_estoque': tem_estoque,
                        'situacao_fiscal': 'irregular' if 'pendências' in situacao_fiscal else 'regular',
                        'contato_nome': contato_nome, 'contato_email': contato_email,
                        'contato_telefone': contato_telefone, 'expectativa': expectativa
                    }
                    st.session_state.step = 3
                    st.rerun()
        else:
            renda_mensal = st.number_input("Renda mensal aproximada (R$)*", min_value=0.0, step=500.0)
            possui_bens = st.checkbox("Possui bens?")
            possui_investimentos = st.checkbox("Possui investimentos?")
            tipo_declaracao = st.radio("Tipo de declaração*", ["Simplificada", "Completa"])
            contato_nome = st.text_input("Nome do responsável*")
            contato_email = st.text_input("E-mail*")
            contato_telefone = st.text_input("Telefone")
            submitted = st.form_submit_button("Avançar ➡", use_container_width=True)
            if submitted:
                if not contato_nome or not contato_email:
                    st.error("Nome e e-mail obrigatórios.")
                else:
                    st.session_state.dados_operacionais = {
                        'renda_mensal': renda_mensal, 'possui_bens': possui_bens,
                        'possui_investimentos': possui_investimentos,
                        'tipo_declaracao': tipo_declaracao,
                        'contato_nome': contato_nome, 'contato_email': contato_email,
                        'contato_telefone': contato_telefone
                    }
                    st.session_state.step = 3
                    st.rerun()

# =============================================================================
# ETAPA 3: UPLOAD DE DOCUMENTOS
# =============================================================================
def etapa_upload():
    st.header("📎 Documentos para Validação")
    perfil = st.session_state.perfil
    if perfil == 'PJ':
        cartao = st.file_uploader("Cartão CNPJ", type=['pdf','png','jpg'])
        contrato = st.file_uploader("Contrato Social", type=['pdf','png','jpg'])
        docs = [cartao, contrato]
    else:
        doc_id = st.file_uploader("RG ou CNH", type=['pdf','png','jpg'])
        comp_res = st.file_uploader("Comprovante de Residência", type=['pdf','png','jpg'])
        docs = [doc_id, comp_res]
    st.session_state.documentos = [d for d in docs if d]

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⬅ Voltar", use_container_width=True):
            st.session_state.step = 2
            st.rerun()
    with col2:
        if st.button("Finalizar Cadastro", type="primary", use_container_width=True):
            if perfil == 'PJ':
                st.session_state.honorario_interno = calcular_honorario_pj(st.session_state.dados_operacionais)
            else:
                st.session_state.honorario_interno = calcular_honorario_pf(st.session_state.dados_operacionais)
            st.session_state.step = 4
            st.rerun()

# =============================================================================
# ETAPA 4: SUCESSO
# =============================================================================
def etapa_sucesso():
    st.header("🚀 Cadastro Enviado com Sucesso!")
    st.balloons()
    st.success("Recebemos suas informações. Nossa equipe da **BSB Contabilidade** analisará os documentos e enviará uma proposta personalizada em até 24 horas.")
    st.info(f"Um resumo foi enviado para o e-mail cadastrado: {st.session_state.dados_operacionais.get('contato_email', '')}")
    if st.button("🔄 Nova Proposta"):
        for key in ['step','perfil','dados_cadastrais','dados_operacionais','documentos','honorario_interno']:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()
